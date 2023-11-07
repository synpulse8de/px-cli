import typer


app = typer.Typer()


@app.command()
def dev():
    """
    Develop on an existing backend
    """
    print(f"[WIP]...")


@app.command()
def create():
    """
    Create a new backend
    """
    print(f"[WIP]...")


@app.command()
def update():
    """
    Update an existing backend
    """
    print(f"[WIP]...")


@app.command()
def delete():
    """
    Delete an existing backend
    """
    print(f"[WIP]...")


@app.command()
def deploy():
    """
    Start the deployment workflow for an existing backend
    """
    print(f"[WIP]...")
