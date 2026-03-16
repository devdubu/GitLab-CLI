from __future__ import annotations

import shlex

from core.safety import check_allowed, RiskLevel, classify

# 허용된 최상위 서브커맨드 구조
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


class ParseError(Exception):
    pass


def parse_and_validate(raw: str) -> list[str]:
    """
    LLM 응답 문자열을 검증하고 shlex로 토큰화하여 반환한다.

    반환값: argv 리스트 (예: ["issue", "list", "--state=open"])
    예외:
      - ParseError: 명령어 형식이 올바르지 않거나 허용되지 않는 경우
    """
    text = raw.strip()

    if text.upper() == "UNKNOWN" or not text:
        raise ParseError(
            "명령어를 생성할 수 없습니다. 더 구체적으로 요청해 주세요."
        )

    # "gl " 접두사 제거
    if text.startswith("gl "):
        text = text[3:].strip()
    elif text.startswith("gl"):
        text = text[2:].strip()

    # 안전 검사
    allowed, msg = check_allowed(text)
    if not allowed:
        raise ParseError(msg)

    try:
        tokens = shlex.split(text)
    except ValueError as e:
        raise ParseError(f"명령어 파싱 오류: {e}") from e

    if not tokens:
        raise ParseError("빈 명령어입니다.")

    # 최상위 커맨드 구조 검증
    key: tuple
    if len(tokens) >= 2:
        key = (tokens[0], tokens[1])
    else:
        key = (tokens[0],)

    if key not in _ALLOWED_COMMANDS and (tokens[0],) not in _ALLOWED_COMMANDS:
        raise ParseError(
            f"허용되지 않는 명령어입니다: {' '.join(tokens[:2])}. "
            "'gl --help'로 사용 가능한 명령어를 확인하세요."
        )

    return tokens
