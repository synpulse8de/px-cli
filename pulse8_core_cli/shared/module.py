import os
from rich import print

ENV_GITHUB_TOKEN = "GITHUB_TOKEN"
ENV_GITHUB_USER = "GITHUB_USER"
ENV_JFROG_TOKEN = "JFROG_TOKEN"
REPOSITORY_PRIVATE: str = "private"
REPOSITORY_INTERNAL: str = "internal"


def get_env_variables() -> dict[str, any]:
    try:
        github_user = os.environ[ENV_GITHUB_USER]
        github_token = os.environ[ENV_GITHUB_TOKEN]
        print(f"[green]Github authentication set to user {github_user}[/green]")
        return {ENV_GITHUB_USER: github_user, ENV_GITHUB_TOKEN: github_token}
    except KeyError:
        print("[bold red]Please set GITHUB_TOKEN and GITHUB_USER environment variables[/bold red]")
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
