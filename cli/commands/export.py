from __future__ import annotations

import json
import os
from typing import Optional

import typer

from adapters import gitlab_api
from core.config import get_config
from core.formatter import print_error, print_success, print_info, to_csv_str

app = typer.Typer(help="데이터 내보내기 명령어")


def _resolve_output(output: Optional[str], default_name: str, fmt: str) -> str:
    if output:
        return output
    cfg = get_config()
    ext = "csv" if fmt == "csv" else "json"
    return os.path.join(cfg.export_dir, f"{default_name}.{ext}")


def _write_file(path: str, rows: list[dict], fmt: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if fmt == "csv":
        content = to_csv_str(rows)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)


@app.command("issues")
def export_issues(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="프로젝트 이름"),
    state: str = typer.Option("all", "--state", help="이슈 상태 (open|closed|all)"),
    fmt: str = typer.Option("csv", "--format", "-f", help="파일 형식 (csv|json)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="저장 경로"),
) -> None:
    """이슈를 파일로 내보냅니다."""
    try:
        print_info("이슈 데이터를 가져오는 중...")
        rows = gitlab_api.list_issues(project=project, state=state)
        path = _resolve_output(output, "issues", fmt)
        _write_file(path, rows, fmt)
        print_success(f"{len(rows)}건 저장 완료: {path}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("mrs")
def export_mrs(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="프로젝트 이름"),
    state: str = typer.Option("all", "--state", help="MR 상태 (open|merged|closed|all)"),
    fmt: str = typer.Option("csv", "--format", "-f", help="파일 형식 (csv|json)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="저장 경로"),
) -> None:
    """Merge Request를 파일로 내보냅니다."""
    try:
        print_info("MR 데이터를 가져오는 중...")
        rows = gitlab_api.list_mrs(project=project, state=state)
        path = _resolve_output(output, "mrs", fmt)
        _write_file(path, rows, fmt)
        print_success(f"{len(rows)}건 저장 완료: {path}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("users")
def export_users(
    fmt: str = typer.Option("csv", "--format", "-f", help="파일 형식 (csv|json)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="저장 경로"),
) -> None:
    """유저 목록을 파일로 내보냅니다."""
    try:
        print_info("유저 데이터를 가져오는 중...")
        rows = gitlab_api.list_users()
        path = _resolve_output(output, "users", fmt)
        _write_file(path, rows, fmt)
        print_success(f"{len(rows)}건 저장 완료: {path}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("projects")
def export_projects(
    fmt: str = typer.Option("csv", "--format", "-f", help="파일 형식 (csv|json)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="저장 경로"),
) -> None:
    """프로젝트 목록을 파일로 내보냅니다."""
    try:
        print_info("프로젝트 데이터를 가져오는 중...")
        rows = gitlab_api.list_projects()
        path = _resolve_output(output, "projects", fmt)
        _write_file(path, rows, fmt)
        print_success(f"{len(rows)}건 저장 완료: {path}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
