"""
Open WebUI Function — GitLab Admin CLI 연동

이 파일을 Open WebUI의 Functions 디렉토리에 마운트하면
채팅 인터페이스에서 자연어로 GitLab CLI 명령어를 실행할 수 있다.

동작 방식:
  1. Open WebUI가 사용자 메시지를 이 Function으로 전달
  2. vLLM에 Few-shot 프롬프트를 전송하여 CLI 명령어 생성
  3. gl-cli 컨테이너에서 해당 명령어를 subprocess로 실행
  4. 결과를 마크다운으로 포맷하여 응답

환경변수 (Open WebUI 컨테이너):
  GL_CLI_URL  : gl-cli 컨테이너의 HTTP API URL (선택)
                설정하지 않으면 subprocess 직접 실행 모드 사용
  VLLM_URL    : vLLM 엔드포인트
  VLLM_MODEL  : vLLM 모델 이름
  GITLAB_URL  : GitLab URL (subprocess 모드에서 환경변수 전달용)
  GITLAB_TOKEN: GitLab Personal Access Token
"""
from __future__ import annotations

import os
import shlex
import subprocess
from typing import Any, Generator

# Open WebUI Function 메타데이터
"""
id: gitlab_admin_cli
name: GitLab Admin CLI
description: 자연어로 Self-hosted GitLab을 조회합니다 (v0.1.0-beta)
author: gitlab-admin-cli
version: 0.1.0
"""


# ──────────────────────────── LLM 호출 ────────────────────────────

def _build_system_prompt() -> str:
    import datetime
    current_month = datetime.date.today().strftime("%Y-%m")
    return f"""\
당신은 GitLab CLI 명령어 생성기입니다.
사용자의 자연어를 아래 허용된 명령어 중 하나로만 변환하세요.
반드시 명령어 한 줄만 출력하세요. 어떤 설명도 하지 마세요.
명령어를 생성할 수 없으면 "UNKNOWN" 이라고만 출력하세요.

허용 명령어 목록:
gl issue list, gl mr list, gl pipeline list,
gl user list, gl project list,
gl export issues, gl export mrs, gl export users, gl export projects,
gl search

예시:
입력: 열린 이슈 보여줘
출력: gl issue list --state=open

입력: myapp 프로젝트 머지된 MR 뽑아줘
출력: gl mr list --project=myapp --state=merged

입력: 이번 달 이후 생성된 MR
출력: gl mr list --created-after={current_month}-01

입력: 전체 유저 CSV로 내보내줘
출력: gl export users --format=csv --output=/exports/users.csv

입력: 이슈 삭제해줘
출력: UNKNOWN
"""


def _call_vllm(user_input: str) -> str:
    """vLLM OpenAI 호환 엔드포인트를 호출하여 CLI 명령어 생성."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai 패키지가 설치되어 있지 않습니다.")

    vllm_url = os.getenv("VLLM_URL", "http://localhost:8000")
    vllm_model = os.getenv("VLLM_MODEL", "gpt-oss-120b")

    client = OpenAI(base_url=f"{vllm_url}/v1", api_key="dummy", timeout=30.0)
    response = client.chat.completions.create(
        model=vllm_model,
        messages=[
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": user_input},
        ],
        max_tokens=128,
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()


# ──────────────────────────── 명령어 실행 ────────────────────────────

def _run_gl_command(argv: list[str]) -> str:
    """
    gl-cli 컨테이너에서 명령어 실행.
    GL_CLI_URL 환경변수가 설정되어 있으면 HTTP 모드, 아니면 subprocess 모드.
    """
    gl_cli_url = os.getenv("GL_CLI_URL", "")
    if gl_cli_url:
        return _run_via_http(gl_cli_url, argv)
    return _run_via_subprocess(argv)


def _run_via_subprocess(argv: list[str]) -> str:
    """python main.py를 subprocess로 직접 실행."""
    cmd = ["python", "/app/main.py"] + argv
    env = {
        **os.environ,
        "GITLAB_URL": os.getenv("GITLAB_URL", ""),
        "GITLAB_TOKEN": os.getenv("GITLAB_TOKEN", ""),
        "VLLM_URL": os.getenv("VLLM_URL", ""),
        "VLLM_MODEL": os.getenv("VLLM_MODEL", ""),
    }
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    output = result.stdout + result.stderr
    return output.strip()


def _run_via_http(base_url: str, argv: list[str]) -> str:
    """gl-cli HTTP API 엔드포인트 호출 (선택적 모드)."""
    import urllib.request
    import json

    payload = json.dumps({"argv": argv}).encode()
    req = urllib.request.Request(
        f"{base_url}/run",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data.get("output", "")


# ──────────────────────────── 안전 검사 ────────────────────────────

_READ_TOKENS = frozenset(["list", "show", "export", "search"])
_CONFIRM_TOKENS = frozenset(["create", "update", "merge", "close", "archive"])
_DANGER_TOKENS = frozenset(["delete", "block", "remove", "destroy", "force"])

_ALLOWED_COMMANDS = {
    ("issue", "list"),
    ("mr", "list"),
    ("pipeline", "list"),
    ("user", "list"),
    ("project", "list"),
    ("export", "issues"),
    ("export", "mrs"),
    ("export", "users"),
    ("export", "projects"),
    ("search",),
}


def _validate(raw: str) -> list[str]:
    text = raw.strip()
    if text.upper() == "UNKNOWN" or not text:
        raise ValueError("명령어를 생성할 수 없습니다. 더 구체적으로 요청해 주세요.")

    if text.startswith("gl "):
        text = text[3:].strip()

    tokens = set(text.lower().split())
    if tokens & _DANGER_TOKENS:
        raise ValueError("DANGER 등급 명령어는 v0.1.0-beta에서 지원하지 않습니다.")
    if tokens & _CONFIRM_TOKENS:
        raise ValueError("CONFIRM 등급 명령어는 v0.1.0-beta에서 지원하지 않습니다.")
    if not (tokens & _READ_TOKENS):
        raise ValueError("READ 명령어만 허용됩니다.")

    argv = shlex.split(text)
    key = tuple(argv[:2]) if len(argv) >= 2 else (argv[0],)
    if key not in _ALLOWED_COMMANDS and (argv[0],) not in _ALLOWED_COMMANDS:
        raise ValueError(f"허용되지 않는 명령어: {' '.join(argv[:2])}")

    return argv


# ──────────────────────────── Open WebUI 진입점 ────────────────────────────

class Tools:
    """Open WebUI Tools 클래스 — Function 등록용."""

    def gitlab_query(self, query: str) -> str:
        """
        자연어로 GitLab 데이터를 조회합니다.

        :param query: 자연어 질의 (예: "열린 이슈 보여줘")
        :return: 조회 결과 텍스트
        """
        try:
            raw_cmd = _call_vllm(query)
            argv = _validate(raw_cmd)
            output = _run_gl_command(argv)

            return (
                f"**실행된 명령어:** `gl {' '.join(argv)}`\n\n"
                f"```\n{output}\n```"
            )
        except ValueError as e:
            return f"⚠️ {e}"
        except Exception as e:
            return f"❌ 오류 발생: {e}"


# Open WebUI pipe 방식 지원 (선택적)
def pipe(body: dict[str, Any], __user: dict | None = None) -> str | Generator:
    """Open WebUI pipe 인터페이스."""
    messages = body.get("messages", [])
    if not messages:
        return "메시지가 없습니다."

    user_input = messages[-1].get("content", "")
    tools = Tools()
    return tools.gitlab_query(user_input)
