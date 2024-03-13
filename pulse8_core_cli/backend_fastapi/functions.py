import os

from pulse8_core_cli.shared.constants import TEMPLATE_REPO_BACKEND_FASTAPI
from pulse8_core_cli.shared.template_management import (
    create_template,
    update_template,
    release_template,
)


def backend_fastapi_create(
    create_remote_repo: bool,
    answers_file: str,
    defaults: bool,
    skip_answered: bool,
    ssh: bool,
):
    def callback_after_git_init():
        os.system(f"poetry lock --no-update")
        os.system(f"poetry install --no-root")

    create_template(
        TEMPLATE_REPO_BACKEND_FASTAPI,
        create_remote_repo,
        answers_file,
        defaults,
        skip_answered,
        ssh,
        callback_after_git_init,
    )


def backend_fastapi_update(answers_file: str, defaults: bool, skip_answered: bool):
    def callback_after_update():
        os.system(f"poetry lock --no-update")
        os.system(f"poetry install --no-root")

    update_template(
        TEMPLATE_REPO_BACKEND_FASTAPI,
        answers_file,
        defaults,
        skip_answered,
        callback_after_update,
    )


def backend_fastapi_release(version: str, title: str):
    def callback_before_git_commit():
        os.system(f"poetry version {version}")

    release_template(version, title, callback_before_git_commit)
