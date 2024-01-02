import typer
from copier import run_copy, run_update
from rich import print

from pulse8_core_cli.shared.constants import ENV_GITHUB_USER, ENV_GITHUB_TOKEN, REPOSITORY_PRIVATE, REPOSITORY_INTERNAL
from pulse8_core_cli.shared.module import (get_env_variables, create_template_tmp_dir,
                                           rename_template_tmp_dir, git_init, git_create_remote)


def template_precheck():
    try:
        env_vars = get_env_variables()
        github_token = env_vars[ENV_GITHUB_TOKEN]
        github_user = env_vars[ENV_GITHUB_USER]
    except KeyError:
        print("[bold][red]GitHub authentication not set...[/red][/bold]")
        print("[italic]Hint: Try [bold]pulse8 auth login[/bold][/italic]")
        exit(1)


def create_template(template_repo_name: str, create_remote_repo: str, answers_file: str, defaults: bool,
                    skip_answered: bool, callback_before_git_init=None):
    template_precheck()
    env_vars = get_env_variables(silent=True)
    github_token = env_vars[ENV_GITHUB_TOKEN]
    github_user = env_vars[ENV_GITHUB_USER]

    if create_remote_repo is None:
        create_remote_input = typer.prompt(
            "Do you want to create private or internal repository ? [no/private/internal]")

        if create_remote_input == REPOSITORY_PRIVATE or create_remote_input == REPOSITORY_INTERNAL:
            create_remote_repo = create_remote_input
    elif create_remote_repo != REPOSITORY_PRIVATE and create_remote_repo != REPOSITORY_INTERNAL:
        create_remote_repo = None

    print("Pulling latest template data...")

    tmp_dir = create_template_tmp_dir()

    worker = run_copy(
        f"https://{github_user}:{github_token}@github.com/synpulse-group/{template_repo_name}.git",
        ".", unsafe=True, defaults=defaults, answers_file=answers_file, skip_answered=skip_answered)

    project_id = worker.answers.user.get("project_id")

    rename_template_tmp_dir(tmp_dir, project_id)

    if callback_before_git_init is not None:
        callback_before_git_init()

    git_init()
    git_create_remote(create_remote_repo, project_id, github_user, github_token)


def update_template(answers_file: str, defaults: bool, skip_answered: bool):
    template_precheck()

    print("Pulling latest template data...")

    run_update(".", overwrite=True, unsafe=True, defaults=defaults,
               answers_file=answers_file, skip_answered=skip_answered)

    print("[green]Project successfully updated.[/green]")