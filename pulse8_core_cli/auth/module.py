import typer

from pulse8_core_cli.auth.functions import auth_login

app = typer.Typer()


@app.command()
def login(email: str):
    """
    Authenticate against Synpulse8 infrastructure
    """
    auth_login(email)


@app.command()
def logout():
    """
    Clean up authentication
    """
    print(f"[WIP]...")
