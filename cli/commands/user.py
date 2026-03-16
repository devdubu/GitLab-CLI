from __future__ import annotations

import typer

from adapters import gitlab_api
from core.formatter import print_output, print_error

app = typer.Typer(help="유저 관련 명령어")


@app.command("list")
def user_list(
    active: bool = typer.Option(False, "--active", help="활성 유저만 조회"),
    blocked: bool = typer.Option(False, "--blocked", help="차단된 유저만 조회"),
    fmt: str = typer.Option("table", "--format", "-f", help="출력 형식 (table|json|csv)"),
) -> None:
    """유저 목록을 조회합니다."""
    try:
        rows = gitlab_api.list_users(active=active, blocked=blocked)
        print_output(rows, fmt, title="Users")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
