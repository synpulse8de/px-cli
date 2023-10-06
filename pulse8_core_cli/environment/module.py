import typer
from rich import print

from pulse8_core_cli.environment.functions import env_create, env_list, env_switch, env_delete

app = typer.Typer()


@app.command()
def create(identifier: str):
    env_create(identifier=identifier)


@app.command()
def list():
    env_list()


@app.command()
def switch(identifier: str):
    env_switch(identifier=identifier)


@app.command()
def update():
    print(f"[WIP]...")


@app.command()
def delete(identifier: str):
    env_delete(identifier=identifier)
