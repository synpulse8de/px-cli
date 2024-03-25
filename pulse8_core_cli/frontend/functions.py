import os

from pulse8_core_cli.shared.constants import TEMPLATE_REPO_FRONTEND_NEXTJS, PNPM
from pulse8_core_cli.shared.template_management import (
    create_template,
    update_template,
    release_template,
)


def frontend_create(
    create_remote_repo: bool,
    answers_file: str,
    defaults: bool,
    skip_answered: bool,
    ssh: bool,
):
    create_template(
        TEMPLATE_REPO_FRONTEND_NEXTJS,
        create_remote_repo,
        answers_file,
        defaults,
        skip_answered,
        ssh,
    )


def frontend_update(answers_file: str, defaults: bool, skip_answered: bool):
    update_template(
        TEMPLATE_REPO_FRONTEND_NEXTJS, answers_file, defaults, skip_answered
    )


def frontend_release(version: str, title: str, major: bool, minor: bool, patch: bool):
    release_template(version, title, major, minor, patch, PNPM)
