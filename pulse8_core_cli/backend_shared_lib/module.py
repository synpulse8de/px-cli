import typer
from typing_extensions import Annotated

from pulse8_core_cli.backend_shared_lib.functions import backend_shared_lib_create, backend_shared_lib_update

app = typer.Typer()


@app.command()
def create(answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
           create_remote_repository: Annotated[str,
           typer.Option(help="Create remote repository [options: no/private/internal]")] = None,
           defaults: Annotated[bool, typer.Option(help="Use default answers and skip questions")] = False,
           skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = False):
    """
    Create a new backend shared lib
    """
    backend_shared_lib_create(create_remote_repository, answers_file, defaults, skip_answered)


@app.command()
def update(answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
           defaults: Annotated[bool, typer.Option(help="Use default answers and skip questions")] = False,
           skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = True):
    """
    Update an existing backend shared lib
    """
    backend_shared_lib_update(answers_file, defaults, skip_answered)


@app.command()
def delete():
    """
    Delete an existing backend shared lib
    """
    print(f"[WIP]...")
