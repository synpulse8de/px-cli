import os
import re
import subprocess
import typer
import yaml

from copier import run_copy, run_update
from rich import print
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pulse8_core_cli.shared.constants import (
    ENV_GITHUB_USER,
    ENV_GITHUB_TOKEN,
    MAVEN,
    POETRY,
    PNPM,
)
from pulse8_core_cli.shared.module import (
    get_env_variables,
    create_template_tmp_dir,
    rename_template_tmp_dir,
    git_init,
    git_create_remote,
    get_maven_wrapper_executable, get_env_variables_small,
)
from pulse8_core_cli.shared.platform_discovery import is_windows

if is_windows():
    from pulse8_core_cli.shared.windows_functions import setup_win_registry_admin


def template_precheck(check_win_registry: bool, caller_command: str = None):
    if check_win_registry and is_windows():
        setup_win_registry_admin(caller_command)
    print("[bold]running template precheck...[/bold]")
    try:
        env_vars = get_env_variables_small()
        github_token = env_vars[ENV_GITHUB_TOKEN]
        github_user = env_vars[ENV_GITHUB_USER]
    except KeyError:
        print("[bold][red]GitHub authentication not set...[/red][/bold]")
        print("[italic]Hint: Try [bold]pulse8 auth login[/bold][/italic]")
        exit(1)
    print("template precheck done - continue...")


def create_template(
    template_repo_name: str,
    create_remote_repo: bool,
    answers_file: str,
    defaults: bool,
    skip_answered: bool,
    ssh: bool,
    callback_after_git_init=None,
    check_win_registry: bool = False,
    caller_command: str = None,
):
    template_precheck(check_win_registry, caller_command=caller_command)
    env_vars = get_env_variables_small(silent=True)
    github_token = env_vars[ENV_GITHUB_TOKEN]
    github_user = env_vars[ENV_GITHUB_USER]

    if create_remote_repo is None:
        create_remote_repo = typer.confirm(
            "Do you want to create private remote repository ?"
        )

    print("Pulling latest template data...")

    tmp_dir = create_template_tmp_dir()

    if ssh:
        src_path = f"git@github.com:synpulse8de/{template_repo_name}.git"
    else:
        src_path = f"https://{github_user}:{github_token}@github.com/synpulse8de/{template_repo_name}.git"

    worker = run_copy(
        src_path,
        ".",
        unsafe=True,
        defaults=defaults,
        answers_file=answers_file,
        skip_answered=skip_answered,
    )

    update_answers_file_src_path()
    project_id = worker.answers.user.get("project_id")
    rename_template_tmp_dir(tmp_dir, project_id)

    git_init(callback_after_git_init)
    git_create_remote(create_remote_repo, project_id, github_user, github_token)


def update_template(
    template_repo_name: str,
    answers_file: str,
    defaults: bool,
    skip_answered: bool,
    callback_after_update=None,
    check_win_registry: bool = False,
    caller_command: str = None,
):
    template_precheck(check_win_registry, caller_command=caller_command)
    original_answers_file_path = get_answers_file_path(answers_file)

    print("Pulling latest template data...")

    answers_file = f"p8t_tmp_file_{str(uuid4())}.yaml"

    with open(original_answers_file_path, "r") as original_file, open(
        answers_file, "w"
    ) as tmp_file:
        for line in original_file:
            tmp_file.write(line)

    update_answers_file_src_path(False, template_repo_name, answers_file)

    run_update(
        ".",
        overwrite=True,
        unsafe=True,
        defaults=defaults,
        answers_file=answers_file,
        skip_answered=skip_answered,
    )

    with open(original_answers_file_path, "w") as original_file, open(
        answers_file, "r"
    ) as tmp_file:
        for line in tmp_file:
            original_file.write(line)

    os.remove(answers_file)
    update_answers_file_src_path(True, template_repo_name, original_answers_file_path)

    if callback_after_update is not None:
        callback_after_update()

    print("[green]Project successfully updated.[/green]")


def release_template(
    version: str,
    title: str,
    major: bool,
    minor: bool,
    patch: bool,
    versioning_tool: str,
):
    unreleased_header = "##[unreleased]"
    unreleased_header_idx = -1

    latest_header_idx = -1
    latest_header_version = ""

    unreleased_link = "[unreleased]:"
    unreleased_link_idx = -1

    line_idx = -1
    unreleased_notes_end_idx = -1
    line_ending = None

    try:
        remote_git_url = (
            subprocess.check_output(["git", "config", "--get", "remote.origin.url"])
            .strip()
            .decode()
        )
        remote_git_url = remote_git_url.replace(
            "git@github.com:", "https://github.com/"
        ).replace(".git", "/")
        if not remote_git_url.endswith("/"):
            remote_git_url += "/"
    except Exception:
        print(
            "[bold][red]Failed to obtain remote git URL. Release cannot be performed without git remote.[/red][/bold]"
        )
        exit(1)

    with open(f"{Path.cwd()}/CHANGELOG.md", "r", encoding="utf-8") as changelog:
        lines = changelog.readlines()
        for line in lines:
            line_idx += 1
            line_compare = line.lower().replace(" ", "")

            if line_ending is None:
                if line_compare.endswith("\r\n"):
                    line_ending = "\r\n"
                elif line_compare.endswith("\r"):
                    line_ending = "\r"
                else:
                    line_ending = "\n"

            if (
                latest_header_idx == -1
                and unreleased_header_idx != -1
                and line_compare.startswith("##[")
            ):
                latest_header_idx = line_idx
                unreleased_notes_end_idx = line_idx
                latest_header_version = (
                    re.findall(r"\[.*?]", line_compare)[0]
                    .replace("[", "")
                    .replace("]", "")
                )

            if line_compare.startswith(unreleased_header):
                unreleased_header_idx = line_idx
            elif line_compare.startswith(unreleased_link):
                unreleased_link_idx = line_idx
                if unreleased_notes_end_idx == -1:
                    unreleased_notes_end_idx = line_idx

    if version is None:
        if latest_header_idx != -1:
            version = latest_header_version
        else:
            version = "0.0.0"
        if major:
            version = bump_version_part(0, version)
        if minor:
            version = bump_version_part(1, version)
        if patch or (not major and not minor):
            version = bump_version_part(2, version)

    print(f"Setting release version {version}")

    release_view_pipe = subprocess.Popen(
        ["gh", "release", "view", f"v{version}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    release_view_res: tuple[bytes, bytes] = release_view_pipe.communicate()
    if release_view_pipe.returncode == 1:
        release_view_stderr = release_view_res[1].decode("utf8")
        if release_view_stderr.strip() != "release not found":
            print(
                f"[bold red]Failed to check if this release already exists: {release_view_stderr}[/bold red]"
            )
            exit(1)
    else:
        print(
            f"[bold red]Failed to create a release. Release already exists.[/bold red]"
        )
        exit(1)

    pr_body = ""
    for idx, line in enumerate(lines):
        if (
            unreleased_header_idx != -1
            and unreleased_notes_end_idx != -1
            and unreleased_header_idx < idx < unreleased_notes_end_idx
        ):
            pr_body += line
    pr_body = pr_body.strip()

    today = datetime.now().date().isoformat()

    lines.insert(unreleased_header_idx + 1, line_ending)
    lines.insert(unreleased_header_idx + 2, f"## [{version}] - {today}{line_ending}")

    lines[unreleased_link_idx + 2] = (
        f"[Unreleased]: {remote_git_url}compare/v{version}...HEAD{line_ending}"
    )

    if latest_header_idx == -1:
        full_changelog_url = f"{remote_git_url}releases/tag/v{version}{line_ending}"
    else:
        full_changelog_url = f"{remote_git_url}compare/v{latest_header_version}...v{version}{line_ending}"

    full_changelog = f"[{version}]: {full_changelog_url}"

    lines.insert(unreleased_link_idx + 3, full_changelog)
    pr_body += line_ending + line_ending + "**Full Changelog:** " + full_changelog_url

    with open(f"{Path.cwd()}/CHANGELOG.md", "w", encoding="utf-8") as changelog:
        changelog.truncate(0)
        changelog.writelines(lines)

    if versioning_tool == MAVEN:
        os.system(
            f'{get_maven_wrapper_executable()} versions:set -DnewVersion="{version}" -DgenerateBackupPoms=false --quiet'
        )
    elif versioning_tool == POETRY:
        os.system(f"poetry version {version}")
    elif versioning_tool == PNPM:
        os.system(
            f"pnpm version {version} --no-commit-hooks --no-git-tag-version --allow-same-version"
        )

    if title is not None:
        pr_title = f"release: v{version} | {title}"
    else:
        pr_title = f"release: v{version}"

    tmp_body_file_name = f"pr_body_{str(uuid4())}.txt"
    tmp_body_file_path = Path.home().joinpath(".pulse8").joinpath(tmp_body_file_name)

    with open(tmp_body_file_path, "w", encoding="utf-8") as pr_body_file:
        pr_body_file.write(pr_body)

    os.system("git add -u :/")
    os.system(f"git checkout -b release/v{version}")
    os.system(f'git commit -m "{pr_title}"')
    os.system(f"git push -u origin release/v{version}")
    os.system(f'gh pr create -t "{pr_title}" -F "{tmp_body_file_path}"')
    os.system(f"gh pr view -w release/v{version}")
    os.system("git fetch")
    os.remove(tmp_body_file_path)

    print(
        "[green]GitHub release PR was successfully created. You can merge it to create a release.[/green]"
    )


def bump_version_part(idx: int, version: str):
    version_split = version.split(".")
    version_split[idx] = str(int(version_split[idx]) + 1)
    return ".".join(version_split)


def update_answers_file_src_path(
    remove_github_user: bool = True,
    template_repo_name: str = None,
    answers_file_path: str = None,
):
    answers_file = None
    if answers_file_path is None:
        answers_file_path = get_answers_file_path()

    try:
        with open(answers_file_path, "r") as stream:
            try:
                answers_file = yaml.unsafe_load(stream)
            except yaml.YAMLError as exy:
                print("[bold][red]Failed to load .copier-answers file[/red][/bold]")
                print(exy)
    except FileNotFoundError:
        print("[bold][red]Could not find .copier-answers file[/red][/bold]")

    if (
        answers_file is not None
        and answers_file_path is not None
        and not re.match("git@github.com:", answers_file["_src_path"])
    ):
        if remove_github_user:
            answers_file["_src_path"] = re.sub(
                "//.*:.*@github\\.com/", "//github.com/", answers_file["_src_path"]
            )
        else:
            env_vars = get_env_variables(silent=True)
            github_token = env_vars[ENV_GITHUB_TOKEN]
            github_user = env_vars[ENV_GITHUB_USER]
            answers_file["_src_path"] = (
                f"https://{github_user}:{github_token}@github.com/synpulse-group/{template_repo_name}.git"
            )

        with open(answers_file_path, "w") as stream:
            try:
                yaml.dump(answers_file, stream, default_flow_style=False)
            except yaml.YAMLError as ex:
                print("[bold][red]Failed to edit .copier-answers file[/red][/bold]")
                print(ex)


def get_answers_file_path(path: str = None):
    if path is None:
        if os.path.isfile(".copier-answers.yaml"):
            return ".copier-answers.yaml"
        elif os.path.isfile(".copier-answers.yml"):
            return ".copier-answers.yml"
    else:
        return path
