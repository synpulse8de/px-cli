import os

from pulse8_core_cli.shared.constants import TEMPLATE_REPO_FRONTEND_ANGULAR
from pulse8_core_cli.shared.template_management import create_template, update_template


def frontend_angular_create(create_remote_repo: bool, answers_file: str, defaults: bool, skip_answered: bool):
    def callback_before_git_init():
        os.system("pnpm install")
        # os.system("husky install")

    create_template(TEMPLATE_REPO_FRONTEND_ANGULAR, create_remote_repo, answers_file, defaults,
                    skip_answered, callback_before_git_init)


def frontend_angular_update(answers_file: str, defaults: bool, skip_answered: bool):
    update_template(answers_file, defaults, skip_answered)
