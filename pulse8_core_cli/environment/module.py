import typer
from rich import print

from pulse8_core_cli.environment.functions import env_create, env_list, env_switch, env_delete, env_update, env_precheck
app = typer.Typer()


@app.command()
def create(identifier: str):
    """
    Creates a new environment
    """
    env_precheck()
    env_create(identifier=identifier)


@app.command()
def list():
    """
    List all environments
    """
    env_precheck()
    env_list()


@app.command()
def switch(identifier: str):
    """
    Switch to given environment
    """
    env_precheck()
    env_switch(identifier=identifier)


@app.command()
def update():
    """
    Update settings of current environment
    """
    env_precheck()
    env_update()


@app.command()
def delete(identifier: str):
    """
    Delete environment
    """
    env_precheck()
    env_delete(identifier=identifier)
