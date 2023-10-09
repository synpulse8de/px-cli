import os
import subprocess
import inquirer
import yaml
from rich import print


KEY_CHOICES_INFRA = "infra"
KEY_CHOICES_INFRA_POSTGRESQL = "postgresql"
KEY_CHOICES_INFRA_KAFKA = "kafka"
KEY_CHOICES_INFRA_REDIS = "redis"
KEY_CHOICES_INFRA_EXASOL = "exasol"
KEY_CHOICES_SERVICES_CORE = "services-core"
KEY_CHOICES_SERVICES_CORE_IAM = "pulse8-core-iam"
KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE = "pulse8-core-notfication-engine"
KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE = "pulse8-core-query-engine"
KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE = "pulse8-core-workflow-engine"


def env_create(identifier: str):
    print(f"[bold]starting environment (id: {identifier})...[/bold]")
    args = (f"k3d cluster create {identifier}")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed starting environment (id: {identifier})[/bold red]")
        print(res[1].decode('ascii'))
        exit(1)
    print(f"[green]started environment (id: {identifier})[/green]")
    print(res[0].decode('ascii'))
    questions = [
        inquirer.Checkbox(
            name=KEY_CHOICES_INFRA,
            message="Which infrastructure do you need?",
            choices=[
                ("PostgreSQL", KEY_CHOICES_INFRA_POSTGRESQL),
                ("Kafka", KEY_CHOICES_INFRA_KAFKA),
                ("Redis", KEY_CHOICES_INFRA_REDIS),
                ("Exasol", KEY_CHOICES_INFRA_EXASOL),
            ],
            default=[KEY_CHOICES_INFRA_POSTGRESQL, KEY_CHOICES_INFRA_KAFKA],
        ),
        inquirer.Checkbox(
            name=KEY_CHOICES_SERVICES_CORE,
            message="Which [bold]Pulse8 Core[/bold] services do you need?",
            choices=[
                KEY_CHOICES_SERVICES_CORE_IAM,
                KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE,
                KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE,
                KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE
            ],
            default=[KEY_CHOICES_SERVICES_CORE_IAM],
        )
    ]
    choices = inquirer.prompt(questions)
    choices_yaml = yaml.dump(choices)
    choices_yaml_path = "choices.yaml"
    with open(choices_yaml_path, "w") as choices_yaml_file:
        choices_yaml_file.write(choices_yaml)
    print(f"saving choices into configmap pulse8-core-cli-env...")
    args = ("kubectl create configmap pulse8-core-cli-config --from-file=choices.yaml")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed to save into configmap pulse8-core-cli-config[/bold red]")
        print(res[1].decode('ascii'))
        exit(1)
    print(f"[green]saved choices into configmap pulse8-core-cli-config[/green]")
    print(res[0].decode('ascii'))
    os.remove(choices_yaml_path)
    env_install_choices(choices)


def env_install_choices(choices: dict):
    if KEY_CHOICES_INFRA in choices:
        infra = choices[KEY_CHOICES_INFRA]
        if KEY_CHOICES_INFRA_POSTGRESQL in infra:
            print("[WIP]...")
        if KEY_CHOICES_INFRA_KAFKA in infra:
            print("[WIP]...")
        if KEY_CHOICES_INFRA_REDIS in infra:
            print("[WIP]...")
        if KEY_CHOICES_INFRA_EXASOL in infra:
            print("[WIP]...")
    if KEY_CHOICES_SERVICES_CORE in choices:
        services_core = choices[KEY_CHOICES_SERVICES_CORE]
        if KEY_CHOICES_SERVICES_CORE_IAM in services_core:
            print("[WIP]...")
        if KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE in services_core:
            print("[WIP]...")
        if KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE in services_core:
            print("[WIP]...")
        if KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE in services_core:
            print("[WIP]...")


def env_list():
    args = (f"k3d cluster list")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('ascii'))


def env_switch(identifier: str):
    print(f"[bold green]stopping all running environments...[/bold green]")
    args = ("k3d cluster list --no-headers | head -n3 | awk '{print $1;}' | xargs k3d cluster stop ")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('ascii'))
    print(f"[bold green]starting environment (id: {identifier})...[/bold green]")
    args = (f"k3d cluster start {identifier}")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('ascii'))
    print(f"[bold green]switching to environment context in kubeconfig (id: {identifier})...[/bold green]")
    args = (f"kubectl config use-context k3d-{identifier}")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('ascii'))


def env_delete(identifier: str):
    print(f"[bold red]deleting the environment (id: {identifier})...[/bold red]")
    args = (f"k3d cluster delete {identifier}")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('ascii'))
