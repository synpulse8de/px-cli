import os
import subprocess
from pathlib import Path

from inquirer import Text, prompt
from rich import print
from pulse8_core_cli.shared.module import get_cli_dir

GIT_REPO_ORG = "synpulse-group"
GIT_REPO_NAME = "pulse8-app-deployments"


def get_deployments_repo_directory() -> Path:
    """
    Returns a Path object pointing to a local clone of the Pulse8 deployments repo. Creates
    the required folder structure if it doesn't exist yet.
    """
    directory = get_cli_dir().joinpath(f"deployments/{GIT_REPO_NAME}")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_deployments_git_repo() -> str:
    """
    Return GitOps deployment repo in format `ORG_NAME/REPO_NAME`
    """
    return f"{GIT_REPO_ORG}/{GIT_REPO_NAME}"


def get_updated_local_clone_of_repo(target_dir: str | Path, repo_name: str) -> int:
    """
    Given a repo, clones the repo if it doesn't exist or otherwise gets the latest changes from the main branch.
    """
    print(
        "[bold deep_sky_blue1]Initializing local clone of deployments GitOps repo... [/bold deep_sky_blue1]",
        end="",
    )
    pipe = subprocess.Popen(
        f"git switch main && git pull || git clone https://github.com/{repo_name} .",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=target_dir,
    )
    _, stderr = pipe.communicate()
    if pipe.returncode != 0:
        print("[bold red]failed to update repo.[/bold red]")
        print(stderr.decode("utf8"))
        exit(1)
    print("[bold green]done.[/bold green]")
    return pipe.returncode


def collect_multiple_inputs(input_prompt) -> dict[str, str]:
    """
    Given an input prompt, collects an arbitrary number of `KEY: "VALUE"` pairs from the user and
    provides them them as a dictionary. The format is enforced and invalid values are not returned.
    """
    env_vars = {}
    while True:
        questions = [Text("env_var", message=input_prompt)]
        answers = prompt(questions)
        env_var = answers["env_var"]
        if env_var.lower() == "done":
            break

        try:
            key, value = [x.strip() for x in env_var.split(":", 1)]
            if not (key and value.startswith('"') and value.endswith('"')):
                raise ValueError
            env_vars[key] = value.strip('"')
        except ValueError:
            print(
                'Invalid format. Please enter the environment variable in the format `KEY: "VALUE"`'
            )

    return env_vars


def get_deployment_repo_path_for_current_project_dir() -> Path:
    """
    Assembles a path inside the primary GitOps repo that stores the manifests for the current project.
    """
    repository_name = os.path.basename(os.getcwd())
    deployment_repo_path = (
        Path("clusters")
        / "aws"
        / "105815711361"
        / "pulse8-cluster-primary"
        / repository_name
    )
    return deployment_repo_path
