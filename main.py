import sys
from dotenv import load_dotenv

load_dotenv()

from alfred.db import init_db
from alfred.agent import AlfredAgent

from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.history import FileHistory


console = Console()


def run():
    init_db()
    agent = AlfredAgent()

    console.print("[bold green]Alfred online.[/bold green] Type 'exit' or Ctrl+C to quit.\n")

    history = FileHistory(".alfred_history")

    try:
        while True:
            try:
                user_input = pt_prompt("You: ", history=history).strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "bye"):
                break

            try:
                response = agent.chat(user_input)
                console.print("\n[bold cyan]Alfred:[/bold cyan]")
                console.print(Markdown(response))
                console.print()
            except RuntimeError as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    finally:
        console.print("\n[dim]Archiving session...[/dim]")
        agent.end_session()
        console.print("[dim]Session closed.[/dim]")


if __name__ == "__main__":
    run()
