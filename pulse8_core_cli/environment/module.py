import typer
from rich import print

from pulse8_core_cli.environment.functions import env_create, env_list, env_switch, env_delete, env_update, env_precheck
app = typer.Typer()


@app.command()
def create(identifier: str):
    env_precheck()
    env_create(identifier=identifier)


@app.command()
def list():
    env_precheck()
    env_list()


@app.command()
def switch(identifier: str):
    env_precheck()
    env_switch(identifier=identifier)


@app.command()
def update():
    env_precheck()
    env_update()


@app.command()
def delete(identifier: str):
    env_precheck()
    env_delete(identifier=identifier)
