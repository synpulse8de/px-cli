import json
import os
import re
import subprocess

from pathlib import Path
from uuid import uuid4

import yaml
from rich import print

from pulse8_core_cli.shared.constants import (
    ENV_GITHUB_USER,
    ENV_JFROG_TOKEN,
    ENV_JFROG_USER,
    ENV_GITHUB_TOKEN,
    ENV_GITHUB_GHCR_TOKEN,
)
from pulse8_core_cli.shared.platform_discovery import is_windows


def get_env_variables(silent: bool = False) -> dict[str, any]:
    try:
        config_github_cli_path: Path
        try:
            if is_windows():
                config_github_cli_path = (
                    Path(os.getenv("APPDATA"))
                    .joinpath("GitHub CLI")
                    .joinpath("hosts.yml")
                )
            else:
                config_github_cli_path = (
                    Path.home().joinpath(".config").joinpath("gh").joinpath("hosts.yml")
                )
        except Exception as e:
            print(f"[red]Error reading from GitHub CLI hosts.yml[/red]")
            print(
                f"[italic]Hint: Please try to reauthorize using [bold]pulse8 auth login[/bold][/italic]"
            )
            raise e
        config_github_cli_file_raw: str
        with open(config_github_cli_path) as config_github_cli_file:
            config_github_cli_file_raw = config_github_cli_file.read()
        config_github_cli = yaml.load(config_github_cli_file_raw, yaml.Loader)
        github_com = config_github_cli["github.com"]
        github_user = github_com["user"]
        github_token = github_com["oauth_token"]
        with open(get_ghcrtoken_path(), "r") as file:
            ghcr_token = file.read()
        if not silent:
            print(f"[green]GitHub authentication set to user {github_user}[/green]")
        docker_config_json_path = get_dotdocker_config_file_path()
        docker_config_json_raw: str
        with open(docker_config_json_path) as docker_config_json_file:
            docker_config_json_raw = docker_config_json_file.read()
        docker_config_json = json.loads(docker_config_json_raw)
        jfrog_token = docker_config_json["auths"]["synpulse.jfrog.io"]["auth"]
        jfrog_user = docker_config_json["auths"]["synpulse.jfrog.io"]["email"]
        return {
            ENV_GITHUB_GHCR_TOKEN: ghcr_token,
            ENV_GITHUB_USER: github_user,
            ENV_GITHUB_TOKEN: github_token,
            ENV_JFROG_TOKEN: jfrog_token,
            ENV_JFROG_USER: jfrog_user,
        }
    except KeyError:
        print(
            "[bold red]Error retrieving environment variables - please use 'pulse8 auth login'[/bold red]"
        )
        exit(1)

def get_env_variables_small(silent: bool = False) -> dict[str, any]:
    try:
        config_github_cli_path: Path
        try:
            if is_windows():
                config_github_cli_path = (
                    Path(os.getenv("APPDATA"))
                    .joinpath("GitHub CLI")
                    .joinpath("hosts.yml")
                )
            else:
                config_github_cli_path = (
                    Path.home().joinpath(".config").joinpath("gh").joinpath("hosts.yml")
                )
        except Exception as e:
            print(f"[red]Error reading from GitHub CLI hosts.yml[/red]")
            print(
                f"[italic]Hint: Please try to reauthorize using [bold]pulse8 auth login[/bold][/italic]"
            )
            raise e
        config_github_cli_file_raw: str
        with open(config_github_cli_path) as config_github_cli_file:
            config_github_cli_file_raw = config_github_cli_file.read()
        config_github_cli = yaml.load(config_github_cli_file_raw, yaml.Loader)
        github_com = config_github_cli["github.com"]
        github_user = github_com["user"]
        github_token = github_com["oauth_token"]
        return {
            ENV_GITHUB_USER: github_user,
            ENV_GITHUB_TOKEN: github_token,
        }
    except KeyError:
        print(
            "[bold red]Error retrieving environment variables - please use 'pulse8 auth login'[/bold red]"
        )
        exit(1)

def git_init(callback_after_git_init):
    os.system("git init")
    if callback_after_git_init is not None:
        callback_after_git_init()
    os.system("git add .")
    os.system('git commit -m "[PULSE8] Generated using Pulse8 Core Template" --quiet')
    os.system("git branch -M main")
    current_git_path = os.getcwd().replace("\\", "/")
    os.system(f"git config --global --add safe.directory {current_git_path}")


def git_create_remote(
    create_remote_repo: bool, repository_name: str, github_user: str, github_token: str
):
    if create_remote_repo:
        print(f"[green]Creating private remote repository {repository_name}[/green]")

        os.system(
            f"gh repo create {repository_name} --private --source=. --remote=upstream"
        )
        os.system(
            f"git remote add origin https://{github_token}@github.com/{github_user}/{repository_name}.git"
        )
        os.system("git push -u origin main")

        print(
            f"[bold green]Pushed generated project to newly created {create_remote_repo} "
            f"repository. Happy coding![/bold green]"
        )
    else:
        print("[bold green]Committed generated project. Happy coding![/bold green]")


def get_cli_dir() -> Path:
    cli_dir: Path = Path(f"{Path.home()}/.pulse8")
    cli_dir.mkdir(parents=True, exist_ok=True)
    return cli_dir


def get_certificates_dir_path() -> Path:
    certificates_dir: Path = get_cli_dir().joinpath("certificates")
    certificates_dir.mkdir(parents=True, exist_ok=True)
    return certificates_dir


def get_environments_dir_path() -> Path:
    environments_dir: Path = get_cli_dir().joinpath("environments")
    environments_dir.mkdir(parents=True, exist_ok=True)
    return environments_dir


def get_dotdocker_dir_path() -> Path:
    docker_dir: Path = Path.home().joinpath(".docker")
    docker_dir.mkdir(parents=True, exist_ok=True)
    return docker_dir


def get_ghcrtoken_path() -> Path:
    return get_cli_dir().joinpath("ghcr_token")


def get_dotdocker_config_file_path() -> Path:
    docker_config_json_path = get_dotdocker_dir_path().joinpath("config.json")
    if not docker_config_json_path.exists():
        with open(docker_config_json_path, "w") as file:
            file.write("{}")
    return docker_config_json_path


def get_dotm2_dir_path() -> Path:
    m2_dir: Path = Path.home().joinpath(".m2")
    m2_dir.mkdir(parents=True, exist_ok=True)
    return m2_dir


def validate_email(email):
    pattern = r"^[a-zA-Z]+\.[a-zA-Z]+@(synpulse\.com|synpulse8\.com|synpulse8\.de)$"
    if re.match(pattern, email):
        return True
    return False


def create_template_tmp_dir():
    new_dir: Path = Path(f"{Path.cwd()}/p8t_tmp_dir_{str(uuid4())}")
    new_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(new_dir)
    return new_dir


def rename_template_tmp_dir(tmp_dir, new_name):
    os.chdir(os.path.dirname(os.getcwd()))
    tmp_dir = tmp_dir.rename(new_name)
    os.chdir(tmp_dir)
    return tmp_dir


def get_maven_wrapper_executable():
    if is_windows():
        return "mvnw.cmd"
    else:
        return "./mvnw"


def execute_shell_command(
    command_array: list[str],
    message_success: str = "",
    message_failure: str = "",
    print_output: bool = True,
) -> str:
    """
    Execute a command and print the output.
    If the command fails, print the error message and exit with error code 1.
    """

    pipe = subprocess.Popen(
        command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        if message_failure:
            print(f"[bold red]{message_failure})[/bold red]")
        print(res[0].decode("utf8"))
        print(res[1].decode("utf8"))
        exit(1)
    if print_output:
        print(res[0].decode("utf8"))
    if message_success:
        print(f"[green]{message_success}[/green]")
    return res[0].decode("utf8")
