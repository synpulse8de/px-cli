import typer
from typing_extensions import Annotated

app = typer.Typer()

@app.command()
def bootstrap():
    """
    Prepare a set of deployment-ready manifests based on the details of your project.
    """
    print("[WIP]...")


@app.command()
def update():
    """
    Update an existing set of deployment-ready manifests for your project.
    """
    print("[WIP]...")


@app.command()
def submit():
    """
    Submit your project's deployment manifests to the master GitOps repo for review and deployment.
    """
    print("[WIP]...")
