import os

from pulse8_core_cli.shared.constants import TEMPLATE_REPO_BACKEND_SPRING
from pulse8_core_cli.shared.module import get_maven_wrapper_executable
from pulse8_core_cli.shared.template_management import (
    create_template,
    update_template,
    release_template,
)


def backend_create(
    create_remote_repo: bool,
    answers_file: str,
    defaults: bool,
    skip_answered: bool,
    ssh: bool,
):
    def callback_after_git_init():
        os.system(f"{get_maven_wrapper_executable()} spotless:apply")
        os.system(f"{get_maven_wrapper_executable()} clean install")

    create_template(
        TEMPLATE_REPO_BACKEND_SPRING,
        create_remote_repo,
        answers_file,
        defaults,
        skip_answered,
        ssh,
        callback_after_git_init=callback_after_git_init,
        check_win_registry=True,
        caller_command="pulse8 backend create",
    )


def backend_update(answers_file: str, defaults: bool, skip_answered: bool):
    def callback_after_update():
        os.system(f"{get_maven_wrapper_executable()} spotless:apply")
        os.system(f"git add -u :/")
        os.system(f"{get_maven_wrapper_executable()} clean install")

    update_template(
        TEMPLATE_REPO_BACKEND_SPRING,
        answers_file,
        defaults,
        skip_answered,
        callback_after_update=callback_after_update,
        check_win_registry=True,
        caller_command="pulse8 backend update",
    )


def backend_release(version: str, title: str):
    def callback_before_git_commit():
        os.system(
            f'{get_maven_wrapper_executable()} versions:set -DnewVersion="{version}" -DgenerateBackupPoms=false'
        )

    release_template(version, title, callback_before_git_commit)
