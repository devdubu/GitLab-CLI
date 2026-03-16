from __future__ import annotations

import csv
import io
import json
from typing import Any

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


def print_table(rows: list[dict[str, Any]], title: str = "") -> None:
    if not rows:
        console.print("[yellow]결과가 없습니다.[/yellow]")
        return

    table = Table(
        title=title,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        show_lines=False,
    )

    columns = list(rows[0].keys())
    for col in columns:
        table.add_column(col, overflow="fold", max_width=60)

    for row in rows:
        table.add_row(*[str(row.get(c, "")) for c in columns])

    console.print(table)


def print_json(rows: list[dict[str, Any]]) -> None:
    console.print_json(json.dumps(rows, ensure_ascii=False, indent=2))


def to_csv_str(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def print_output(rows: list[dict[str, Any]], fmt: str, title: str = "") -> None:
    if fmt == "json":
        print_json(rows)
    elif fmt == "csv":
        console.print(to_csv_str(rows))
    else:
        print_table(rows, title=title)


def print_error(msg: str) -> None:
    console.print(f"[bold red]오류:[/bold red] {msg}")


def print_warning(msg: str) -> None:
    console.print(f"[bold yellow]경고:[/bold yellow] {msg}")


def print_success(msg: str) -> None:
    console.print(f"[bold green]✓[/bold green] {msg}")


def print_info(msg: str) -> None:
    console.print(f"[cyan]ℹ[/cyan] {msg}")
