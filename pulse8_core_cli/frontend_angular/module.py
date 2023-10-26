import os

import typer
from copier import run_copy, run_update

app = typer.Typer()


@app.command()
def dev():
    print(f"[WIP]...")


@app.command()
def create(
        folder_name: str = typer.Argument(None, help="Folder name for your project.")
):
    if not folder_name:
        folder_name = typer.prompt("Enter a folder name")

    print("\n")
    print('Pulling latest template data...')

    run_copy(
        f"git@github.com:synpulse-group/pulse8-core-frontend-angular-template.git", folder_name)

    os.chdir(folder_name)
    os.system("pnpm install")
    os.system("husky install")
    os.system("git init")
    os.system("git add .")
    os.system(
        "git commit -m \"[PULSE8] Generated using Pulse8 Core Template\" ")


@app.command()
def update(
        use_saved_answers: bool = typer.Argument(True, help="Decide if the old answers are used")
):
    use_saved_answers = typer.confirm("Do you want to use the saved answers?", default=True)

    print('Checking template tags')
    run_update('.', overwrite=True, defaults=use_saved_answers)
    print('Update completed.')


@app.command()
def delete():
    print(f"[WIP]...")


@app.command()
def deploy():
    print(f"[WIP]...")
