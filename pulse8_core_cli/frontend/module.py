import typer
import os
from typing_extensions import Annotated
from copier import run_copy, run_update

app = typer.Typer()


@app.command()
def dev():
    print(f"[WIP]...")


@app.command()
def create(
    github_username: Annotated[str, typer.Option(
        prompt=True, confirmation_prompt=False, help="Synpulse github username")]
):

    print("\n")
    print('Pulling latest template data...')

    run_copy(
        f"https://{github_username}@github.com/synpulse-group/pulse8-core-frontend-nextjs-template.git", ".")

    os.system("git init")
    os.system("git add .")
    os.system(
        "git commit -m \"[PULSE8] Generated using Pulse8 Core Template\" ")


@app.command()
def update():
    print('Pulling latest template data...')
    run_update('.', overwrite=True)


@app.command()
def delete():
    print(f"[WIP]...")
