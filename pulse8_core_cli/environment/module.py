from typing import Annotated

import typer
from rich import print

from pulse8_core_cli.environment.functions import env_create, env_list, env_switch, env_delete, env_update, env_precheck
app = typer.Typer()


@app.command()
def create(identifier: Annotated[str, typer.Argument(help="The identifier of the environment.")],
           from_env: Annotated[str, typer.Option(help="Create from existing environment config.")] = None,
           from_file: Annotated[str, typer.Option(help="Create from existing environment config file.")] = None):
    """
    Creates a new environment
    """
    env_precheck()
    env_create(identifier=identifier, from_env=from_env, from_file=from_file)


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
