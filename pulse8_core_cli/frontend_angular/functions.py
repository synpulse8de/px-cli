import os

from pulse8_core_cli.shared.constants import TEMPLATE_REPO_FRONTEND_ANGULAR, PNPM
from pulse8_core_cli.shared.template_management import (
    create_template,
    update_template,
    release_template,
)


def frontend_angular_create(
    create_remote_repo: bool,
    answers_file: str,
    defaults: bool,
    skip_answered: bool,
    ssh: bool,
):
    def callback_after_git_init():
        os.system("pnpm install")
        # os.system("husky install")

    create_template(
        TEMPLATE_REPO_FRONTEND_ANGULAR,
        create_remote_repo,
        answers_file,
        defaults,
        skip_answered,
        ssh,
        callback_after_git_init=callback_after_git_init,
    )


def frontend_angular_update(answers_file: str, defaults: bool, skip_answered: bool):
    update_template(
        TEMPLATE_REPO_FRONTEND_ANGULAR, answers_file, defaults, skip_answered
    )


def frontend_angular_release(
    version: str, title: str, major: bool, minor: bool, patch: bool
):
    release_template(version, title, major, minor, patch, PNPM)
