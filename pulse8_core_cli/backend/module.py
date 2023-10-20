import typer
from typing_extensions import Annotated

from pulse8_core_cli.backend.functions import backend_create, backend_update

app = typer.Typer()


@app.command()
def dev():
    print(f"[WIP]...")


@app.command()
def create(answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
           defaults: Annotated[bool, typer.Option(help="Use default answers and skip questions")] = False,
           skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = False):

    backend_create(answers_file, defaults, skip_answered)


@app.command()
def update(answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
           defaults: Annotated[bool, typer.Option(help="Use default answers and skip questions")] = False,
           skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = True):

    backend_update(answers_file, defaults, skip_answered)


@app.command()
def delete():
    print(f"[WIP]...")


@app.command()
def deploy():
    print(f"[WIP]...")
