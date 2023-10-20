import typer
import os

from rich import print
from copier import run_copy, run_update
from pulse8_core_cli.environment.functions import ENV_GITHUB_USER, ENV_GITHUB_TOKEN

app = typer.Typer()


@app.command()
def dev():
    print(f"[WIP]...")


@app.command()
def create():

    try:
        github_token = os.environ[ENV_GITHUB_TOKEN]
        github_user = os.environ[ENV_GITHUB_USER]
        print(f"[green]Github authentication set to user {github_user}[/green]")
    except KeyError:
        print("[bold red]Please set GITHUB_TOKEN and GITHUB_USER environment variables[/bold red]")
        exit(1)

    print('Pulling latest template data...')
    run_copy(f"https://{github_user}:{github_token}@github.com/synpulse-group/pulse8-core-frontend-nextjs-template.git", ".")

    os.system("git init")
    os.system("git add .")
    os.system('git commit -m "[PULSE8] Generated using Pulse8 Core Template" --quiet')

    print("[bold green]Committed generated content. Happy coding![/bold green]")


@app.command()
def update():
    print('Pulling latest template data...')
    run_update('.', overwrite=True)


@app.command()
def delete():
    print(f"[WIP]...")
