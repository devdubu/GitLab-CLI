from __future__ import annotations

from enum import Enum


class RiskLevel(str, Enum):
    READ = "READ"
    CONFIRM = "CONFIRM"
    DANGER = "DANGER"
    UNKNOWN = "UNKNOWN"


# 명령어 토큰 → 위험도 매핑
_READ_TOKENS = frozenset(["list", "show", "export", "search"])
_CONFIRM_TOKENS = frozenset(["create", "update", "merge", "close", "archive"])
_DANGER_TOKENS = frozenset(["delete", "block", "remove", "destroy", "force"])


def classify(command: str) -> RiskLevel:
    """CLI 명령어 문자열에서 위험도를 분류한다."""
    tokens = set(command.lower().split())
    if tokens & _DANGER_TOKENS:
        return RiskLevel.DANGER
    if tokens & _CONFIRM_TOKENS:
        return RiskLevel.CONFIRM
    if tokens & _READ_TOKENS:
        return RiskLevel.READ
    return RiskLevel.UNKNOWN


def check_allowed(command: str) -> tuple[bool, str]:
    """
    v0.1.0-beta: READ 명령어만 허용.
    반환: (allowed, message)
    """
    level = classify(command)
    if level == RiskLevel.READ:
        return True, ""
    if level == RiskLevel.CONFIRM:
        return False, (
            "이 명령어는 데이터 수정 작업을 포함합니다 (CONFIRM 등급).\n"
            "v0.1.0-beta에서는 조회 명령어만 지원합니다. 다음 버전에서 지원 예정입니다."
        )
    if level == RiskLevel.DANGER:
        return False, (
            "이 명령어는 데이터 삭제/차단 등 위험 작업을 포함합니다 (DANGER 등급).\n"
            "v0.1.0-beta에서는 조회 명령어만 지원합니다. 다음 버전에서 지원 예정입니다."
        )
    return False, (
        "알 수 없는 명령어입니다. 'gl --help'로 사용 가능한 명령어를 확인하세요."
    )
