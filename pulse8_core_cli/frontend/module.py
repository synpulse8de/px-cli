from typing import Annotated

import typer

from rich import print
from pulse8_core_cli.frontend.functions import frontend_create, frontend_update

app = typer.Typer()


@app.command()
def dev():
    """
    Develop on an existing frontend
    """
    print(f"[WIP]...")


@app.command()
def create(answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
           create_remote_repository: Annotated[str,
           typer.Option(help="Create remote repository [options: no/private/internal]")] = None,
           defaults: Annotated[bool, typer.Option(help="Use default answers and skip questions")] = False,
           skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = False):
    """
    Create a new frontend
    """
    frontend_create(create_remote_repository, answers_file, defaults, skip_answered)


@app.command()
def update(answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
           defaults: Annotated[bool, typer.Option(help="Use default answers and skip questions")] = False,
           skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = True):
    """
    Update an existing frontend
    """
    frontend_update(answers_file, defaults, skip_answered)


@app.command()
def delete():
    """
    Delete an existing frontend
    """
    print(f"[WIP]...")


@app.command()
def deploy():
    """
    Start the deployment workflow for an existing frontend
    """
    print(f"[WIP]...")
