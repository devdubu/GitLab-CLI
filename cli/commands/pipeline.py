from __future__ import annotations

from typing import Optional

import typer

from adapters import gitlab_api
from core.formatter import print_output, print_error

app = typer.Typer(help="파이프라인 관련 명령어")


@app.command("list")
def pipeline_list(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="프로젝트 이름 또는 경로"),
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="파이프라인 상태 (running|success|failed|canceled|pending)"
    ),
    fmt: str = typer.Option("table", "--format", "-f", help="출력 형식 (table|json|csv)"),
) -> None:
    """파이프라인 목록을 조회합니다."""
    try:
        rows = gitlab_api.list_pipelines(project=project, status=status)
        print_output(rows, fmt, title="Pipelines")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
