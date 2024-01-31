from pulse8_core_cli.shared.constants import TEMPLATE_REPO_BACKEND_SHARED_LIB_JAVA
from pulse8_core_cli.shared.template_management import create_template, update_template


def backend_shared_lib_create(
    create_remote_repo: bool, answers_file: str, defaults: bool, skip_answered: bool
):
    create_template(
        TEMPLATE_REPO_BACKEND_SHARED_LIB_JAVA,
        create_remote_repo,
        answers_file,
        defaults,
        skip_answered,
    )


def backend_shared_lib_update(answers_file: str, defaults: bool, skip_answered: bool):
    update_template(answers_file, defaults, skip_answered)
