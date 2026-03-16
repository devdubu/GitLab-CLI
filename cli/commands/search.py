from __future__ import annotations

import typer

from adapters import gitlab_api
from core.formatter import print_output, print_error

app = typer.Typer(help="GitLab 검색 명령어")


@app.command()
def search(
    query: str = typer.Option(..., "--query", "-q", help="검색어"),
    scope: str = typer.Option(
        "projects",
        "--scope",
        "-s",
        help="검색 범위 (issues|mrs|projects|users)",
    ),
    fmt: str = typer.Option("table", "--format", "-f", help="출력 형식 (table|json|csv)"),
) -> None:
    """GitLab에서 검색합니다."""
    try:
        results = gitlab_api.search(query=query, scope=scope)
        # 검색 결과는 구조가 다양하므로 dict 형태로 정규화
        rows = []
        for item in results:
            if isinstance(item, dict):
                rows.append(item)
            else:
                rows.append(item.__dict__ if hasattr(item, "__dict__") else {"result": str(item)})
        print_output(rows, fmt, title=f'Search: "{query}" [{scope}]')
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
