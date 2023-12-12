import json
import os
import re
import subprocess

from pathlib import Path
from uuid import uuid4

import yaml
from rich import print

from pulse8_core_cli.shared.constants import ENV_GITHUB_USER, ENV_JFROG_TOKEN, ENV_JFROG_USER, ENV_GITHUB_TOKEN
from pulse8_core_cli.shared.platform_discovery import is_windows
from pulse8_core_cli.shared.privileges_discovery import is_admin


def get_env_variables(silent: bool = False) -> dict[str, any]:
    try:

        config_github_cli_path: Path
        try:
            if is_windows():
                config_github_cli_path = Path(os.getenv('APPDATA')).joinpath("GitHub CLI").joinpath("hosts.yml")
            else:
                config_github_cli_path = Path.home().joinpath(".config").joinpath("gh").joinpath("hosts.yml")
        except Exception as e:
            print(f"[red]Error reading from GitHub CLI hosts.yml[/red]")
            print(f"[italic]Hint: Please try to reauthorize using [bold]pulse8 auth login[/bold][/italic]")
            raise e
        config_github_cli_file_raw: str
        with open(config_github_cli_path) as config_github_cli_file:
            config_github_cli_file_raw = config_github_cli_file.read()
        config_github_cli = yaml.load(config_github_cli_file_raw, yaml.Loader)
        github_com = config_github_cli["github.com"]
        github_user = github_com["user"]
        github_token = github_com["oauth_token"]
        if not silent:
            print(f"[green]GitHub authentication set to user {github_user}[/green]")
        docker_config_json_path = get_dotdocker_dir_path().joinpath("config.json")
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


def check_create_certificates() -> None:
    print("creating certificates...")
    key_path = get_certificates_dir_path().joinpath("key.pem")
    cert_path = get_certificates_dir_path().joinpath("cert.pem")
    if cert_path.exists() and key_path.exists():
        print("[green]certificates already exist[/green]")
    else:
        args = ("mkcert", "--install")
        pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res: tuple[bytes, bytes] = pipe.communicate()
        if pipe.returncode == 1:
            print(res[1].decode('utf8'))
            exit(1)
        print(res[0].decode('utf8'))
        args = ("mkcert",
                "-key-file", key_path, "-cert-file", cert_path,
                "pulse8.dev", "*.pulse8.dev", "localhost", "127.0.0.1", "::1")
        pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res: tuple[bytes, bytes] = pipe.communicate()
        if pipe.returncode == 1:
            print(res[1].decode('utf8'))
            exit(1)
        print(res[0].decode('utf8'))
        print("[green]certificates created[/green]")


def check_hosts(silent: bool = False) -> bool:
    hosts_path: Path
    if is_windows():
        hosts_path = Path("c:\\Windows\\System32\\Drivers\\etc\\hosts")
    else:
        hosts_path = Path("/etc/hosts")
    hosts_file_raw: str
    if not silent:
        print(f"Checking hosts file ({hosts_path})")
    with open(hosts_path, "r") as hosts_file:
        hosts_file_raw = hosts_file.read()
    if "pulse8.dev" in hosts_file_raw:
        if not silent:
            print(f"pulse8.dev entries found")
        return True
    if not silent:
        print(f"[red]pulse8.dev entries not found[/red]")
        if is_windows():
            print("Run [italic]pulse8 environment init[/italic] "
                  "as [bold]Administrator[/bold] to add pulse8.dev entries!")
        else:
            print("Run [italic]pulse8 environment init[/italic] "
                  "as [bold]root[/bold] to add pulse8.dev entries!")
    return False


def setup_hosts():
    if not is_admin():
        if is_windows():
            print("[red]Run again as Administrator![/red]")
        else:
            print("[red]Run again as root[/red]")
        exit(1)
    if check_hosts(silent=True):
        print(f"Hosts file already set up.")
        return
    hosts_path: Path
    if is_windows():
        hosts_path = Path("c:\\Windows\\System32\\Drivers\\etc\\hosts")
    else:
        hosts_path = Path("/etc/hosts")
    hosts_file_raw: str
    print(f"Updating hosts file ({hosts_path})")
    with open(hosts_path, "a") as hosts_file:
        hosts_file.write("127.0.0.1 pulse8.dev\n")
        hosts_file.write("::1 pulse8.dev\n")


def get_certificates_dir_path() -> Path:
    certificates_dir: Path = Path(f"{Path.home()}/.pulse8/certificates")
    certificates_dir.mkdir(parents=True, exist_ok=True)
    return certificates_dir


def get_environments_dir_path() -> Path:
    environments_dir: Path = Path(f"{Path.home()}/.pulse8/.environments")
    environments_dir.mkdir(parents=True, exist_ok=True)
    return environments_dir


def get_dotdocker_dir_path() -> Path:
    docker_dir: Path = Path.home().joinpath(".docker")
    docker_dir.mkdir(parents=True, exist_ok=True)
    return docker_dir


def get_dotm2_dir_path() -> Path:
    m2_dir: Path = Path.home().joinpath(".m2")
    m2_dir.mkdir(parents=True, exist_ok=True)
    return m2_dir


def validate_email(email):
    pattern = r'^[a-zA-Z]+\.[a-zA-Z]+@(synpulse\.com|synpulse8\.com)$'
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

