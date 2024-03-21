import typer

from pulse8_core_cli.shared.platform_discovery import is_windows

if is_windows():
    from pulse8_core_cli.auth.windows_functions import setup_win_registry

app = typer.Typer()


@app.command()
def setup_winreg():
    """
    Adjust Windows registry with Pulse8 requirements
    """
    if is_windows():
        setup_win_registry()
