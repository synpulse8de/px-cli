import os

from pulse8_core_cli.shared.constants import TEMPLATE_REPO_BACKEND_SPRING
from pulse8_core_cli.shared.module import get_maven_wrapper_executable
from pulse8_core_cli.shared.template_management import create_template, update_template, release_template


def backend_create(
    create_remote_repo: str, answers_file: str, defaults: bool, skip_answered: bool
):
    create_template(
        TEMPLATE_REPO_BACKEND_SPRING,
        create_remote_repo,
        answers_file,
        defaults,
        skip_answered,
    )


def backend_update(answers_file: str, defaults: bool, skip_answered: bool):
    update_template(answers_file, defaults, skip_answered)


def backend_release(version: str, title: str):
    def callback_before_git_commit():
        os.system(f"{get_maven_wrapper_executable()} versions:set -DnewVersion=\"{version}\" -DgenerateBackupPoms=false")

    release_template(version, title, callback_before_git_commit)
