import os

from pulse8_core_cli.shared.constants import (
    TEMPLATE_REPO_FRONTEND_SHARED_LIB_REACT,
    PNPM,
)
from pulse8_core_cli.shared.template_management import (
    create_template,
    update_template,
    release_template,
)


def frontend_shared_lib_create(
    create_remote_repo: bool,
    answers_file: str,
    defaults: bool,
    skip_answered: bool,
    ssh: bool,
):
    def callback_after_git_init():
        os.system(f"pnpm install")
        os.system(f"pnpm prepare")
        os.system(f"pnpm format")

    create_template(
        TEMPLATE_REPO_FRONTEND_SHARED_LIB_REACT,
        create_remote_repo,
        answers_file,
        defaults,
        skip_answered,
        ssh,
        callback_after_git_init=callback_after_git_init,
    )


def frontend_shared_lib_update(answers_file: str, defaults: bool, skip_answered: bool):
    def callback_after_update():
        os.system(f"pnpm install")
        os.system(f"pnpm format")
        os.system(f"git add -u :/")

    update_template(
        TEMPLATE_REPO_FRONTEND_SHARED_LIB_REACT,
        answers_file,
        defaults,
        skip_answered,
        callback_after_update=callback_after_update,
    )


def frontend_shared_lib_release(
    version: str, title: str, major: bool, minor: bool, patch: bool
):
    release_template(version, title, major, minor, patch, PNPM)
