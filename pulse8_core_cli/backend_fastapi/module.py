from typing import Annotated

import typer

from pulse8_core_cli.backend_fastapi.functions import backend_fastapi_update, backend_fastapi_create

app = typer.Typer()


@app.command()
def dev():
    """
    Develop on an existing backend
    """
    print(f"[WIP]...")


@app.command()
def create(answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
           create_remote_repository: Annotated[str,
           typer.Option(help="Create remote repository [options: no/private/internal]")] = None,
           defaults: Annotated[bool, typer.Option(help="Use default answers and skip questions")] = False,
           skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = False):
    """
    Create a new backend
    """
    backend_fastapi_create(create_remote_repository, answers_file, defaults, skip_answered)


@app.command()
def update(answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
           defaults: Annotated[bool, typer.Option(help="Use default answers and skip questions")] = False,
           skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = True):
    """
    Update an existing backend
    """
    backend_fastapi_update(answers_file, defaults, skip_answered)


@app.command()
def delete():
    """
    Delete an existing backend
    """
    print(f"[WIP]...")


@app.command()
def deploy():
    """
    Start the deployment workflow for an existing backend
    """
    print(f"[WIP]...")
