import os

import typer
from copier import run_copy, run_update
from rich import print

from pulse8_core_cli.environment.functions import ENV_GITHUB_USER, ENV_GITHUB_TOKEN
from pulse8_core_cli.shared.module import git_init, get_env_variables, REPOSITORY_PRIVATE, REPOSITORY_INTERNAL, \
    git_create_remote


def frontend_angular_create(create_remote_repo: str, answers_file: str, defaults: bool, skip_answered: bool,
                            folder_name: str):
    if not folder_name:
        folder_name = typer.prompt("Enter a folder name")

    env_variables = get_env_variables()
    github_user = env_variables[ENV_GITHUB_USER]
    github_token = env_variables[ENV_GITHUB_TOKEN]

    if create_remote_repo is None:
        create_remote_input = typer.prompt(
            "Do you want to create private or internal repository ? [no/private/internal]")

        if create_remote_input == REPOSITORY_PRIVATE or create_remote_input == REPOSITORY_INTERNAL:
            create_remote_repo = create_remote_input
    elif create_remote_repo != REPOSITORY_PRIVATE and create_remote_repo != REPOSITORY_INTERNAL:
        create_remote_repo = None

    print("Pulling latest template data...")

    worker = run_copy(
        f"https://{github_user}:{github_token}@github.com/synpulse-group/pulse8-core-frontend-angular-template.git",
        folder_name, unsafe=True, defaults=defaults, answers_file=answers_file, skip_answered=skip_answered)

    project_id = worker.answers.user.get("project_id")

    os.chdir(folder_name)
    os.system("pnpm install")
    # os.system("husky install")

    git_init()
    git_create_remote(create_remote_repo, project_id, github_user, github_token)


def frontend_angular_update(answers_file: str, defaults: bool, skip_answered: bool):
    print("Pulling latest template data...")

    run_update(".", overwrite=True, unsafe=True, defaults=defaults,
               answers_file=answers_file, skip_answered=skip_answered)

    print("[green]Project successfully updated.[/green]")
