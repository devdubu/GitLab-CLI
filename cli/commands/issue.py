from __future__ import annotations

from typing import Optional

import typer

from adapters import gitlab_api
from core.formatter import print_output, print_error

app = typer.Typer(help="이슈 관련 명령어")


@app.command("list")
def issue_list(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="프로젝트 이름 또는 경로"),
    state: str = typer.Option("open", "--state", "-s", help="이슈 상태 (open|closed|all)"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="담당자 username"),
    fmt: str = typer.Option("table", "--format", "-f", help="출력 형식 (table|json|csv)"),
) -> None:
    """이슈 목록을 조회합니다."""
    try:
        rows = gitlab_api.list_issues(project=project, state=state, assignee=assignee)
        print_output(rows, fmt, title=f"Issues [{state}]")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
