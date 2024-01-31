import typer
from typing_extensions import Annotated

from pulse8_core_cli.backend.functions import backend_create, backend_update

app = typer.Typer()


@app.command()
def dev():
    """
    Develop on an existing backend
    """
    print(f"[WIP]...")


@app.command()
def create(
    answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
    create_remote_repository: Annotated[
        bool,
        typer.Option(help="Create private remote repository"),
    ] = None,
    defaults: Annotated[
        bool, typer.Option(help="Use default answers and skip questions")
    ] = False,
    skip_answered: Annotated[
        bool, typer.Option(help="Skip answered questions")
    ] = False,
):
    """
    Create a new backend
    """
    backend_create(create_remote_repository, answers_file, defaults, skip_answered)


@app.command()
def update(
    answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
    defaults: Annotated[
        bool, typer.Option(help="Use default answers and skip questions")
    ] = False,
    skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = True,
):
    """
    Update an existing backend
    """
    backend_update(answers_file, defaults, skip_answered)


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
