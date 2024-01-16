import os
import typer
from typing_extensions import Annotated
from pathlib import Path
from rich import print
import inquirer
from .functions import (
    get_deployments_repo_directory,
    get_deployments_git_repo,
    get_updated_local_clone_of_repo,
)
from .manifests.main import DeploymentManifests

app = typer.Typer()


@app.command()
def bootstrap():
    """
    Prepare a set of deployment-ready manifests based on the details of your project.
    """
    print("[WIP]...")


@app.command()
def update():
    """
    Update an existing set of deployment-ready manifests for your project.
    """
    print("[WIP]...")


@app.command()
def submit():
    """
    Submit your project's deployment manifests to the master GitOps repo for review and deployment.
    """
    print("[WIP]...")


# TODO: perhaps to be deleted later, but just do this as a bootstrap thing
@app.command()
def init():
    """
    Initialize a new Pulse8 deploy project.
    """

    deployments_repo_directory: Path = get_deployments_repo_directory()

    get_updated_local_clone_of_repo(
        target_dir=deployments_repo_directory,
        repo_name=get_deployments_git_repo(),
        branch_name="main",
    )
    
    # parse project name
    input_project_name = typer.prompt("What is the name of your project?")
    input_deployment_port = typer.prompt("What is the port of your deployment?")
    
    
    project_manifests_directory = deployments_repo_directory.joinpath("clusters/aws/105815711361/pulse8-cluster-primary").joinpath(input_project_name)
    
    # ask which registry it is using
    
    # check if this project exists in the deployments repo - if so, what to do?
    
    deployment = DeploymentManifests(
        name=input_project_name,
        image="nginx:1.19.10",
        imagePullSecrets=[],
        resources={
            "limits" : {
                "cpu": "100m",
                "memory": "128Mi"
            },
            "requests": {
                "cpu": "100m",
                "memory": "128Mi"
            },
        },
        port=input_deployment_port,
        github_repo_path="https://github.com/synpulse-group/pulse8-core-cli"
    )
    
    
    # Should I dump this into the local project's folder, or directly to the app deployments repo?
    deployment.dump_base_layer(
        project_manifests_directory
    )    
    
    # for each env, we need the layer to:
    # - set up configs
    # - set up secrets
    # - set up imageautomation
    # - dump in the right place
    
