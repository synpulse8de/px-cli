import os
import subprocess
from pathlib import Path
from typing import Annotated

import inquirer
import typer
import yaml
from dotenv import dotenv_values
from jinja2 import Environment, PackageLoader
from pulse8_core_cli.shared.module import execute_shell_command
from rich import print
from rich.prompt import Prompt

from .functions import (
    collect_multiple_inputs,
    get_deployment_repo_path_for_current_project_dir,
    get_deployments_git_repo,
    get_deployments_repo_directory,
    get_updated_local_clone_of_repo,
)
from pulse8_core_cli.shared.platform_discovery import is_windows

app = typer.Typer()


@app.command()
def create(
    project_id: Annotated[str, typer.Option(help="ID of project")] = None,
    branch: Annotated[
        str, typer.Option(help="Repository branch to deploy from")
    ] = None,
    env: Annotated[str, typer.Option(help="Environment to deploy to")] = None,
    deploy_port: Annotated[str, typer.Option(help="Port of deployment")] = None,
    ingress_path: Annotated[
        str, typer.Option(help="Ingress path of deployment")
    ] = None,
    env_var_file_path: Annotated[
        str, typer.Option(help="Path to .env file with environment variables")
    ] = None,
    env_secret_file_path: Annotated[
        str, typer.Option(help="Path to .env file with environment secrets")
    ] = None,
):
    """
    Create a deployment manifest for the project in your current working directory.
    """

    deployments_repo_directory: Path = get_deployments_repo_directory()

    get_updated_local_clone_of_repo(
        target_dir=deployments_repo_directory,
        repo_name=get_deployments_git_repo(),
    )

    # project inputs
    if project_id is None:
        project_id = Prompt.ask(
            "What is the [bold]ID[/bold] of your project? "
            "(name of project in machine-friendly format e.g. 'my-project-backend')"
        )
    if env is None:
        env = Prompt.ask(
            "What [bold]environment[/bold] do you want to deploy to?", default="dev"
        )

    # deployment details
    if deploy_port is None:
        deploy_port = Prompt.ask(
            "What is the [bold]port[/bold] of your deployment?", default="8000"
        )
    if branch is None:
        branch = Prompt.ask(
            "What [bold]branch[/bold] of your app repo do you want to deploy this environment from?",
            default="develop",
        )
    if ingress_path is None:
        ingress_path = Prompt.ask(
            "What is the [bold]ingress path[/bold] for your deployment?", default="/"
        )

    # env vars
    if env_var_file_path is None:
        print(
            "Configuring [bold]environment variables[/bold] for your deployment. [bold]Input `done` to finish.[/bold]"
        )
        env_vars = collect_multiple_inputs(
            input_prompt='Please enter an env var in the format `KEY: "VALUE"`',
        )
    else:
        env_vars = dotenv_values(dotenv_path=Path(env_var_file_path))

    # secrets
    if env_secret_file_path is None:
        print(
            "Configuring [bold]environment secrets[/bold] for your deployment, "
            "to be fetched from AWS SSM ([italic][link=https://github.com/synpulse-group/pulse8-app-deployments/blob/main/docs/accessing-secrets.md]see docs[/link][/italic]). "
            "[bold]Input `done` to finish.[/bold]"
        )
        print("")
        secret_vars = collect_multiple_inputs(
            input_prompt='Please enter an env var in the format `KEY: "/aws/ssm/path/to/secret"`',
        )
    else:
        secret_vars = dotenv_values(dotenv_path=Path(env_secret_file_path))

    # get current repo name - assume it's the current directory
    repository_name = os.path.basename(os.getcwd())

    # get deployment filepath
    deployment_filepath = get_deployment_repo_path_for_current_project_dir()

    environment = Environment(
        loader=PackageLoader("pulse8_core_cli.deploy", package_path="templates")
    )
    template = environment.get_template("helm-deployment.yaml")
    rendered_template = template.render(
        namespace=f"apps-{project_id}-{env}",
        helmrelease_name=project_id,
        chart_name=project_id,
        environment_abbreviation=env,
        image_repository=f"synpulse.jfrog.io/s8-docker-local/synpulse-group-{repository_name}-{branch}",
        application_port=deploy_port,
        ingress_route=ingress_path,
        automatic_deployment_filepath=deployment_filepath,
        env_vars=env_vars,
        env_secret_params=secret_vars,
    )

    # save into current directory, under k8s/helm/{{envname}}
    current_helm_dir = Path(".") / "k8s" / "helm"
    current_helm_dir.mkdir(parents=True, exist_ok=True)
    with open(current_helm_dir / f"{project_id}-{env}.yaml", "w") as f:
        [
            f.write(f"# {x}\n")
            for x in [
                "NOTICE: The file controlling your deployment is stored in the pulse8-app-deployments repository",
                "You must make changes there, or alternatively update this file and use `pulse8 deploy submit`",
                "to push an updated version to the deployments repository.",
            ]
        ]
        f.write(rendered_template)

    if is_windows():
        print(f"Your deployment manifest has been created in .\\{current_helm_dir}.")
    else:
        print(f"Your deployment manifest has been created in ./{current_helm_dir}.")
    print(
        "Please use [bold]`pulse8 deploy submit`[/bold] to submit your deployment manifest for review and deployment."
    )


@app.command()
def submit(
    deployment_to_submit: Annotated[
        str,
        typer.Option(help="Filename of your yaml helm deployment located in /k8s/helm"),
    ] = None,
    push_branch: Annotated[
        bool,
        typer.Option(help="Automatically push branch to pulse8-app-deployments repo"),
    ] = False,
):
    """
    Submit your project's deployment manifests to the master GitOps repo for review and deployment.
    """
    deployments_repo_directory: Path = get_deployments_repo_directory()
    get_updated_local_clone_of_repo(
        target_dir=deployments_repo_directory,
        repo_name=get_deployments_git_repo(),
    )

    if deployment_to_submit is None:
        # find all local deployment manifests in ./k8s/helm folder
        deployment_manifests = list(Path("./k8s/helm").glob("*.yaml"))
        # make user choose which one to submit
        deployment_to_submit = inquirer.prompt(
            [
                inquirer.List(
                    "deployment",
                    message="Which deployment do you want to submit?",
                    choices=[str(x) for x in deployment_manifests],
                )
            ]
        )
        # get the filename only, in a way that works across all OS
        deployment_to_submit = os.path.basename(deployment_to_submit["deployment"])

    # get repository name
    repository_name = os.path.basename(os.getcwd())

    # get the deployment repo and folder path
    deployments_helm_dir = get_deployment_repo_path_for_current_project_dir()
    deployments_helm_dir = deployments_repo_directory / deployments_helm_dir
    deployments_helm_dir.mkdir(parents=True, exist_ok=True)

    # read the local file
    with open(Path("./k8s/helm") / deployment_to_submit, "r") as f:
        deployment_manifest = f.read()

    # parse the yaml to get the value of environment_abbreviation
    document = next(yaml.safe_load_all(deployment_manifest))
    environment_abbreviation = document["metadata"]["labels"]["synpulse8.com/env"]

    # write to deployments repo
    with open(deployments_helm_dir / f"{deployment_to_submit}", "w") as f:
        f.write(deployment_manifest)

    # create a new branch and add the file to the current commit state
    execute_shell_command(
        command_array=[
            "git",
            "-C",
            str(deployments_repo_directory),
            "checkout",
            "-B",
            f"deploy/{repository_name}-{environment_abbreviation}",
        ],
    )
    execute_shell_command(
        command_array=[
            "git",
            "-C",
            str(deployments_repo_directory),
            "add",
            f"{deployments_helm_dir}/{deployment_to_submit}",
        ],
    )

    # create commit
    command = f'git -C {str(deployments_repo_directory)} commit -m "deploy({repository_name}-{environment_abbreviation}): add deployment {deployment_to_submit}"'
    subprocess.Popen(command, shell=True).communicate()

    # push branch automatically if set to true to skip prompt in "gh pr create" command
    if push_branch:
        command = f"git -C {str(deployments_repo_directory)} push -u origin"
        subprocess.Popen(command, shell=True).communicate()

    # create a draft PR
    command = f'cd {str(deployments_repo_directory)} && gh pr create --title "Deploy new app: {repository_name}" --draft --fill --body-file .github/new_deployment_pr_template.md'
    subprocess.Popen(command, shell=True).communicate()

    # open the created PR in the browser
    command = f"cd {str(deployments_repo_directory)} && gh pr view --web"
    subprocess.Popen(command, shell=True).communicate()
