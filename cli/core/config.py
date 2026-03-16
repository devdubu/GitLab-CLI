from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class Config:
    gitlab_url: str
    gitlab_token: str
    vllm_url: str
    vllm_model: str
    export_dir: str

    @classmethod
    def from_env(cls) -> "Config":
        missing = []
        gitlab_url = os.getenv("GITLAB_URL", "")
        gitlab_token = os.getenv("GITLAB_TOKEN", "")
        if not gitlab_url:
            missing.append("GITLAB_URL")
        if not gitlab_token:
            missing.append("GITLAB_TOKEN")
        if missing:
            raise EnvironmentError(
                f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing)}"
            )
        return cls(
            gitlab_url=gitlab_url,
            gitlab_token=gitlab_token,
            vllm_url=os.getenv("VLLM_URL", "http://localhost:8000"),
            vllm_model=os.getenv("VLLM_MODEL", "gpt-oss-120b"),
            export_dir=os.getenv("EXPORT_DIR", "/exports"),
        )


@lru_cache(maxsize=1)
def get_config() -> Config:
    return Config.from_env()
