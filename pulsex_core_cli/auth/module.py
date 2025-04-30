import typer

from pulsex_core_cli.auth.functions import auth_login, auth_logout

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
    auth_logout()
