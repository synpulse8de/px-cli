import os
import subprocess
from rich import print
from pathlib import Path
import inquirer
from inquirer import Checkbox

GIT_REPO_ORG = "synpulse-group"
GIT_REPO_NAME = "pulse8-app-deployments"


def get_deployments_repo_directory() -> Path:
    """
    Returns a Path object pointing to a local clone of the Pulse8 deployments repo. Creates
    the required folder structure if it doesn't exist yet.
    """
    directory = Path.home().joinpath(f".pulse8/deployments/{GIT_REPO_NAME}")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_deployments_git_repo() -> str:
    """
    Return GitOps deployment repo in format `ORG_NAME/REPO_NAME`
    """
    return f"{GIT_REPO_ORG}/{GIT_REPO_NAME}"

def get_updated_local_clone_of_repo(target_dir:str, repo_name:str, branch_name="main") -> int:
    print(
        "[bold deep_sky_blue1]Initializing local clone of deployments GitOps repo... [/bold deep_sky_blue1]",
        end="",
    )
    
    pipe = subprocess.Popen(
        f"git checkout {branch_name} && git pull || git clone https://github.com/{repo_name}".split(" "),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=target_dir,
    )
    _, stderr = pipe.communicate()
    if pipe.returncode == 0:
        print(f"[bold red]failed to update repo.[/bold red]")
        print(stderr.decode('utf8'))
        exit(1)
    print("[bold green]done.[/bold green]")
    return pipe.returncode
