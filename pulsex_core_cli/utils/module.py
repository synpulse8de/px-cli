import subprocess
from sys import platform

import typer

from pulsex_core_cli.shared.platform_discovery import is_windows, is_macos, is_linux

if is_windows():
    from pulsex_core_cli.shared.windows_functions import setup_win_registry

app = typer.Typer()


@app.command()
def setup_winreg():
    """
    Adjust Windows registry with Pulse8 requirements
    """
    if is_windows():
        setup_win_registry()


def run(cmd: str, shell: bool = True):
    typer.echo(f"Running: {cmd}")
    subprocess.run(cmd, shell=shell, check=True)

@app.command()
def install_dependencies():
    """Install all required external tools based on the operating system."""

    try:
        if is_macos():
            # macOS
            run("brew install pipx && pipx ensurepath")
            run("pipx install poetry")
            run("brew install k3d")
            run("sudo npm install -g devspace")
            run("sudo npm install -g pnpm")
            run("brew install kubernetes-cli")
            run("brew install helm")
            run("brew install fluxcd/tap/flux")
            run("brew install gh")
            run("brew install mkcert && brew install nss")
            run("brew install jfrog-cli && jf intro")

        elif is_windows():
            # Windows
            run("py -3 -m pip install --user pipx")
            run("py -3 -m pipx ensurepath")
            run("pipx install poetry")
            run("choco install -y k3d")
            run("npm install -g devspace")
            run("npm install -g pnpm")
            run("choco install -y kubernetes-cli")
            run("choco install -y kubernetes-helm")
            run("choco install -y flux")
            run("choco install -y gh")
            run("choco install -y mkcert")
            run("choco install -y jfrog-cli-v2-jf")
            run("jf intro")

        elif is_linux():
            # Ubuntu/Debian-style Linux
            run("python3 -m pip install --user pipx")
            run("python3 -m pipx ensurepath")
            run("pipx install poetry")
            run("curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash")
            run("sudo npm install -g devspace")
            run("sudo npm install -g pnpm")
            run("sudo snap install kubectl --classic")
            run("sudo snap install helm --classic")
            run("curl -s https://fluxcd.io/install.sh | sudo bash")
            typer.echo("Please manually install GitHub CLI: https://github.com/cli/cli/blob/trunk/docs/install_linux.md")
            typer.echo("Please manually install mkcert: https://github.com/FiloSottile/mkcert#linux")
            run("""bash -c 'wget -qO - https://releases.jfrog.io/artifactory/jfrog-gpg-public/jfrog_public_gpg.key | sudo apt-key add -'""")
            run("""bash -c 'echo "deb https://releases.jfrog.io/artifactory/jfrog-debs xenial contrib" | sudo tee -a /etc/apt/sources.list'""")
            run("sudo apt update && sudo apt install -y jfrog-cli-v2-jf")
            run("jf intro")

        else:
            typer.secho("Unsupported operating system", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    except subprocess.CalledProcessError as e:
        typer.secho(f"Command failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
