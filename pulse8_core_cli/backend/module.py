import typer
from typing_extensions import Annotated

from pulse8_core_cli.backend.functions import backend_create, backend_update

app = typer.Typer()


@app.command()
def dev():
    print(f"[WIP]...")


@app.command()
def create(github_username: Annotated[str,
           typer.Option(prompt=True, confirmation_prompt=False, help="Synpulse github username")],
           answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
           defaults: Annotated[bool, typer.Option(help="Use default answers and skip questions")] = False,
           skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = False):

    backend_create(github_username, answers_file, defaults, skip_answered)


@app.command()
def update(answers_file: Annotated[str, typer.Option(help="Copier answers file path")] = None,
           defaults: Annotated[bool, typer.Option(help="Use default answers and skip questions")] = False,
           skip_answered: Annotated[bool, typer.Option(help="Skip answered questions")] = True):

    backend_update(answers_file, defaults, skip_answered)


@app.command()
def delete():
    print(f"[WIP]...")
