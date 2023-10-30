import typer
from typing_extensions import Annotated

from pulse8_core_cli.frontend_angular.functions import frontend_angular_create, frontend_angular_update

app = typer.Typer()


@app.command()
def dev():
    print(f"[WIP]...")


@app.command()
def create(answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
           create_remote_repository: Annotated[str,
           typer.Option(help="Create remote repository [options: no/private/internal]")] = None,
           defaults: Annotated[bool, typer.Option(help="Use default answers and skip questions")] = False,
           skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = False,
           folder_name: str = typer.Argument(None, help="Folder name for your project.")
           ):
    frontend_angular_create(create_remote_repository, answers_file, defaults, skip_answered, folder_name)


@app.command()
def update(
        answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
        defaults: Annotated[bool, typer.Option(help="Use default answers and skip questions")] = False,
        skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = True
):
    frontend_angular_update(answers_file, defaults, skip_answered)


@app.command()
def delete():
    print(f"[WIP]...")


@app.command()
def deploy():
    print(f"[WIP]...")
