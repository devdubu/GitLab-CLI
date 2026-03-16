from __future__ import annotations

import typer

from adapters import gitlab_api
from core.formatter import print_output, print_error

app = typer.Typer(help="프로젝트 관련 명령어")


@app.command("list")
def project_list(
    owned: bool = typer.Option(False, "--owned", help="내가 소유한 프로젝트만"),
    starred: bool = typer.Option(False, "--starred", help="즐겨찾기 프로젝트만"),
    fmt: str = typer.Option("table", "--format", "-f", help="출력 형식 (table|json|csv)"),
) -> None:
    """프로젝트 목록을 조회합니다."""
    try:
        rows = gitlab_api.list_projects(owned=owned, starred=starred)
        print_output(rows, fmt, title="Projects")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
