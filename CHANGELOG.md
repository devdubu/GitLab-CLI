# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0-beta] - 2026-03-16

### Added

#### Core
- `cli/core/config.py` — 환경변수 로딩 (`GITLAB_URL`, `GITLAB_TOKEN`, `VLLM_URL`, `VLLM_MODEL`, `EXPORT_DIR`), `lru_cache` 싱글톤 패턴
- `cli/core/safety.py` — 위험도 3단계 분류 (`READ` / `CONFIRM` / `DANGER`), v0.1.0-beta는 READ만 허용
- `cli/core/formatter.py` — Rich 기반 테이블/JSON/CSV 출력, `print_error` / `print_success` / `print_info` 헬퍼

#### Adapters
- `cli/adapters/gitlab_api.py` — `python-gitlab` 래퍼, 페이지네이션 지원 (`as_list=False`)
  - `list_issues()` — 프로젝트/상태/담당자 필터
  - `list_mrs()` — 프로젝트/상태/생성일 필터
  - `list_pipelines()` — 프로젝트/상태 필터, 프로젝트 미지정 시 멤버십 프로젝트 전체 순회
  - `list_users()` — active/blocked 필터
  - `list_projects()` — owned/starred 필터
  - `search()` — scope 매핑 포함 (mrs → merge_requests)

#### Commands
- `cli/commands/issue.py` — `gl issue list`
- `cli/commands/mr.py` — `gl mr list`
- `cli/commands/pipeline.py` — `gl pipeline list`
- `cli/commands/user.py` — `gl user list`
- `cli/commands/project.py` — `gl project list`
- `cli/commands/export.py` — `gl export issues|mrs|users|projects` (CSV/JSON 파일 저장)
- `cli/commands/search.py` — `gl search --query --scope`

#### Chat Mode
- `cli/chat/prompt.py` — Few-shot 시스템 프롬프트 빌더, 현재 월 자동 삽입
- `cli/chat/llm_client.py` — vLLM OpenAI 호환 엔드포인트 호출, 타임아웃/API 오류 처리
- `cli/chat/parser.py` — LLM 응답 파싱 및 허용 명령어 목록 검증, `ParseError` 정의

#### Entrypoint
- `cli/main.py` — Typer 앱, 서브커맨드 등록, `gl chat` 단일/대화형 모드

#### Open WebUI Integration
- `openwebui/functions/gitlab_cli.py` — `Tools.gitlab_query()` 및 `pipe()` 인터페이스, subprocess/HTTP 이중 실행 모드

#### Infrastructure
- `cli/Dockerfile` — Python 3.12-slim 기반, glab CLI 포함
- `cli/requirements.txt` — `typer[all]`, `rich`, `python-gitlab`, `openai`, `pandas`, `openpyxl`
- `docker-compose.yml` — `gitlab` / `gl-cli` / `open-webui` 3-서비스 구성, `gl-net` 브리지 네트워크
- `.env.example` — 필수 환경변수 템플릿

### Architecture Decisions
- LLM은 자연어 → CLI 명령어 문자열 변환만 담당 (Tool use/Function calling 미사용)
- 모든 명령어는 `safety.py` → `parser.py` 검증 레이어를 반드시 통과
- v0.1.0-beta 범위: 데이터 조회(READ) 전용, 수정/삭제는 미구현

---

## [Unreleased]

### Planned (v0.2.0)
- CONFIRM 등급 명령어 지원 (create, update, merge, close, archive)
- DANGER 등급 명령어 지원 (delete, block, remove) — Y/N 또는 전문 입력 확인 플로우

### Planned (v0.3.0+)
- 명령어 히스토리 및 자동완성
- glab CLI 워크플로우 위임
- pandas 기반 Excel 내보내기
