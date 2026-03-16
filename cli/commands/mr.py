from __future__ import annotations

from typing import Optional

import typer

from adapters import gitlab_api
from core.formatter import print_output, print_error

app = typer.Typer(help="Merge Request 관련 명령어")


@app.command("list")
def mr_list(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="프로젝트 이름 또는 경로"),
    state: str = typer.Option("open", "--state", "-s", help="MR 상태 (open|merged|closed|all)"),
    created_after: Optional[str] = typer.Option(
        None, "--created-after", help="생성일 필터 (YYYY-MM-DD)"
    ),
    fmt: str = typer.Option("table", "--format", "-f", help="출력 형식 (table|json|csv)"),
) -> None:
    """Merge Request 목록을 조회합니다."""
    try:
        rows = gitlab_api.list_mrs(
            project=project, state=state, created_after=created_after
        )
        print_output(rows, fmt, title=f"Merge Requests [{state}]")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
