import os

from pulse8_core_cli.shared.constants import TEMPLATE_REPO_FRONTEND_NEXTJS
from pulse8_core_cli.shared.template_management import (
    create_template,
    update_template,
    release_template,
)


def frontend_create(
    create_remote_repo: bool, answers_file: str, defaults: bool, skip_answered: bool
):
    create_template(
        TEMPLATE_REPO_FRONTEND_NEXTJS,
        create_remote_repo,
        answers_file,
        defaults,
        skip_answered,
    )


def frontend_update(answers_file: str, defaults: bool, skip_answered: bool):
    update_template(answers_file, defaults, skip_answered)


def frontend_release(version: str, title: str):
    def callback_before_git_commit():
        os.system(
            f"pnpm version {version} --no-commit-hooks --no-git-tag-version --allow-same-version"
        )

    release_template(version, title, callback_before_git_commit)
