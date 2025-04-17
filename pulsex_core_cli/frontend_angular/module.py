import typer
from typing_extensions import Annotated

from pulsex_core_cli.frontend_angular.functions import (
    frontend_angular_create,
    frontend_angular_update,
    frontend_angular_release,
)

app = typer.Typer()


@app.command()
def dev():
    """
    Develop on an existing frontend
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
    ssh: Annotated[bool, typer.Option(help="Use SSH for git remote")] = False,
):
    """
    Create a new frontend
    """
    frontend_angular_create(
        create_remote_repository, answers_file, defaults, skip_answered, ssh
    )


@app.command()
def update(
    answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
    defaults: Annotated[
        bool, typer.Option(help="Use default answers and skip questions")
    ] = False,
    skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = True,
):
    """
    Update an existing frontend
    """
    frontend_angular_update(answers_file, defaults, skip_answered)


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


@app.command()
def release(
    version: Annotated[str, typer.Argument(help="Version of the release")] = None,
    title: Annotated[str, typer.Option(help="Title of the release")] = None,
    major: Annotated[
        bool, typer.Option(help="Increment major part of version")
    ] = False,
    minor: Annotated[
        bool, typer.Option(help="Increment minor part of version")
    ] = False,
    patch: Annotated[
        bool, typer.Option(help="Increment patch part of version")
    ] = False,
):
    """
    Create a GitHub release for an existing frontend
    """
    frontend_angular_release(version, title, major, minor, patch)
