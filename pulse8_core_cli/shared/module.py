import json
import os
import re
from pathlib import Path

import yaml
from rich import print

from pulse8_core_cli.shared.platform_discovery import is_windows

ENV_GITHUB_TOKEN = "GITHUB_TOKEN"
ENV_GITHUB_USER = "GITHUB_USER"
ENV_JFROG_TOKEN = "JFROG_TOKEN"
ENV_JFROG_USER = "JFROG_USER"
REPOSITORY_PRIVATE: str = "private"
REPOSITORY_INTERNAL: str = "internal"


def get_env_variables(silent: bool = False) -> dict[str, any]:
    try:

        config_github_cli_path: Path
        if is_windows():
            config_github_cli_path = Path(os.getenv('APPDATA')).joinpath("GitHub CLI").joinpath("hosts.yml")
        else:
            config_github_cli_path = Path.home().joinpath(".config").joinpath("gh").joinpath("hosts.yml")
        config_github_cli_file_raw: str
        with open(config_github_cli_path) as config_github_cli_file:
            config_github_cli_file_raw = config_github_cli_file.read()
        config_github_cli = yaml.load(config_github_cli_file_raw, yaml.Loader)
        github_com = config_github_cli["github.com"]
        github_user = github_com["user"]
        github_token = github_com["oauth_token"]
        if not silent:
            print(f"[green]GitHub authentication set to user {github_user}[/green]")
        docker_config_json_path = Path.home().joinpath(".docker").joinpath("config.json")
        docker_config_json_raw: str
        with open(docker_config_json_path) as docker_config_json_file:
            docker_config_json_raw = docker_config_json_file.read()
        docker_config_json = json.loads(docker_config_json_raw)
        jfrog_token = docker_config_json["auths"]["synpulse.jfrog.io"]["auth"]
        jfrog_user = docker_config_json["auths"]["synpulse.jfrog.io"]["email"]
        return {ENV_GITHUB_USER: github_user, ENV_GITHUB_TOKEN: github_token,
                ENV_JFROG_TOKEN: jfrog_token, ENV_JFROG_USER: jfrog_user}
    except KeyError:
        print("[bold red]Error retrieving environment variables - please use 'pulse8 auth login'[/bold red]")
        exit(1)


def git_init():
    os.system('git init')
    os.system('git add .')
    os.system('git commit -m "[PULSE8] Generated using Pulse8 Core Template" --quiet')
    os.system('git branch -M main')


def git_create_remote(create_remote_repo: str, repository_name: str, github_user: str, github_token: str):
    if create_remote_repo is not None:
        print(f"[green]Creating {create_remote_repo} repository {repository_name}[/green]")

        os.system(f"gh repo create {repository_name} --{create_remote_repo} --source=. --remote=upstream")
        os.system(f"git remote add origin https://{github_token}@github.com/{github_user}/{repository_name}.git")
        os.system("git push -u origin main")

        print(f"[bold green]Pushed generated project to newly created {create_remote_repo} "
              f"repository. Happy coding![/bold green]")
    else:
        print("[bold green]Committed generated project. Happy coding![/bold green]")


def get_certificates_dir_path() -> Path:
    certificates_dir: Path = Path(f"{Path.home()}/.pulse8/certificates")
    certificates_dir.mkdir(parents=True, exist_ok=True)
    return certificates_dir


def validate_email(email):
    pattern = r'^[a-zA-Z]+\.[a-zA-Z]+@(synpulse\.com|synpulse8\.com)$'
    if re.match(pattern, email):
        return True
    return False
