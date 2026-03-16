from __future__ import annotations

import sys
from typing import Optional

import typer
from rich.console import Console

from commands import issue, mr, pipeline, user, project, export, search as search_cmd
from chat import llm_client, prompt, parser as cmd_parser
from core.formatter import print_error, print_info, print_warning

console = Console()

app = typer.Typer(
    name="gl",
    help="GitLab Admin CLI — Self-hosted GitLab 관리 도구 (v0.1.0-beta)",
    no_args_is_help=True,
)

# 서브커맨드 등록
app.add_typer(issue.app, name="issue")
app.add_typer(mr.app, name="mr")
app.add_typer(pipeline.app, name="pipeline")
app.add_typer(user.app, name="user")
app.add_typer(project.app, name="project")
app.add_typer(export.app, name="export")
app.add_typer(search_cmd.app, name="search")


@app.command("chat")
def chat_mode(
    message: Optional[str] = typer.Argument(None, help="자연어 명령어 (생략 시 대화형 모드)"),
) -> None:
    """자연어로 GitLab 명령어를 실행합니다 (Chat 모드)."""
    if message:
        _run_chat(message)
    else:
        _interactive_chat()


def _run_chat(user_input: str) -> None:
    """단일 자연어 입력을 처리한다."""
    print_info(f"입력: {user_input}")
    try:
        messages = prompt.build_messages(user_input)
        raw_cmd = llm_client.generate_command(messages)
        console.print(f"[dim]생성된 명령어:[/dim] [bold]{raw_cmd}[/bold]")

        argv = cmd_parser.parse_and_validate(raw_cmd)
        print_info(f"실행: gl {' '.join(argv)}")
        app(argv, standalone_mode=False)
    except cmd_parser.ParseError as e:
        print_warning(str(e))
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


def _interactive_chat() -> None:
    """대화형 Chat 모드."""
    console.print("[bold cyan]GitLab Admin CLI — Chat 모드[/bold cyan]")
    console.print("자연어로 명령어를 입력하세요. 종료: [bold]exit[/bold] 또는 Ctrl+C\n")
    while True:
        try:
            user_input = typer.prompt("▶")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]종료합니다.[/dim]")
            break
        if user_input.strip().lower() in ("exit", "quit", "종료"):
            console.print("[dim]종료합니다.[/dim]")
            break
        if not user_input.strip():
            continue
        _run_chat(user_input)
        console.print()


if __name__ == "__main__":
    app()
