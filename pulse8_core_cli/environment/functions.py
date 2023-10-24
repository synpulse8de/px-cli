import os
import re
import subprocess

import inquirer
import yaml
from inquirer import Checkbox
from rich import print

from pulse8_core_cli.util.platform_discovery import is_cpu_arm

ENV_GITHUB_TOKEN = "GITHUB_TOKEN"
ENV_GITHUB_USER = "GITHUB_USER"
KEY_CHOICES_INFRA = "infra"
KEY_CHOICES_INFRA_POSTGRESQL = "postgresql"
KEY_CHOICES_INFRA_KAFKA = "kafka"
KEY_CHOICES_INFRA_REDIS = "redis"
KEY_CHOICES_INFRA_EXASOL = "exasol"
KEY_CHOICES_INFRA_TEEDY = "teedy"
KEY_CHOICES_SERVICES_CORE = "services-core"
KEY_CHOICES_SERVICES_CORE_IAM = "pulse8-core-iam"
KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE = "pulse8-core-notfication-engine"
KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE = "pulse8-core-query-engine"
KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE = "pulse8-core-workflow-engine"


def env_precheck():
    print("[bold]running environment precheck...[bold]")
    try:
        github_token = os.environ[ENV_GITHUB_TOKEN]
        github_user = os.environ[ENV_GITHUB_USER]
        print(f"[green]github authentication set to user {github_user}[/green]")
        print("environment precheck done - continue...")
    except KeyError:
        print("[bold red]please set GITHUB_TOKEN and GITHUB_USER environment variables (more info: tbd)[/bold red]")
        exit(1)


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
    print(f"installing flux into environment (id: {identifier})...")
    args = ("flux install")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed installing flux into environment (id: {identifier})[/bold red]")
        print(res[1].decode('ascii'))
        exit(1)
    print(f"[green]installed flux into environment (id: {identifier})[/green]")
    print(res[0].decode('ascii'))
    choices = inquirer.prompt(get_questions())
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


def env_update():
    print(f"[bold]collecting information about current context...[/bold]")
    args = (f"kubectl config current-context")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed collecting information - sandbox name[/bold red]")
        print(res[1].decode('ascii'))
        exit(1)
    identifier = res[0].decode('ascii')
    identifier = re.sub(r"^k3d-", "", identifier)
    identifier = re.sub(r"\s", "", identifier)
    args = (f"kubectl --namespace default get configmap pulse8-core-cli-config -o yaml")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed collecting information - previous configuration[/bold red]")
        print(res[1].decode('ascii'))
        exit(1)
    configmap_raw = res[0].decode('ascii')
    configmap = yaml.load(configmap_raw, yaml.Loader)
    choices_old = yaml.load(configmap['data']['choices.yaml'], yaml.Loader)
    print(choices_old)
    print(f"[green]collected information about current context[/green]")
    print(f"[bold]updating environment (id: {identifier})...[/bold]")
    preselection_infra = []
    preselection_services_core = []
    if choices_old is not None:
        if KEY_CHOICES_INFRA in choices_old:
            choices_infra = choices_old[KEY_CHOICES_INFRA]
            if KEY_CHOICES_INFRA_POSTGRESQL in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_POSTGRESQL)
            if KEY_CHOICES_INFRA_REDIS in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_REDIS)
            if KEY_CHOICES_INFRA_KAFKA in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_KAFKA)
            if KEY_CHOICES_INFRA_EXASOL in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_EXASOL)
            if KEY_CHOICES_INFRA_TEEDY in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_TEEDY)
        if KEY_CHOICES_SERVICES_CORE in choices_old:
            choices_services_core = choices_old[KEY_CHOICES_SERVICES_CORE]
            if KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE in choices_services_core:
                preselection_services_core.append(KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE)
            if KEY_CHOICES_SERVICES_CORE_IAM in choices_services_core:
                preselection_services_core.append(KEY_CHOICES_SERVICES_CORE_IAM)
            if KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE in choices_services_core:
                preselection_services_core.append(KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE)
            if KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE in choices_services_core:
                preselection_services_core.append(KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE)
    choices = inquirer.prompt(get_questions(preselection_infra, preselection_services_core))
    choices_yaml = yaml.dump(choices)
    choices_yaml_path = "choices.yaml"
    with open(choices_yaml_path, "w") as choices_yaml_file:
        choices_yaml_file.write(choices_yaml)
    print(f"saving choices into configmap pulse8-core-cli-env...")
    args = ("kubectl delete configmap pulse8-core-cli-config ; kubectl create configmap pulse8-core-cli-config --from-file=choices.yaml")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed to save into configmap pulse8-core-cli-config[/bold red]")
        print(res[1].decode('ascii'))
        exit(1)
    print(f"[green]saved choices into configmap pulse8-core-cli-config[/green]")
    print(res[0].decode('ascii'))
    os.remove(choices_yaml_path)
    env_install_choices(choices=choices, choices_old=choices_old)


def env_install_choices(choices: dict, choices_old: dict | None = None):
    github_token = os.environ[ENV_GITHUB_TOKEN]
    github_user = os.environ[ENV_GITHUB_USER]
    if KEY_CHOICES_INFRA in choices:
        infra = choices[KEY_CHOICES_INFRA]
        if KEY_CHOICES_INFRA_POSTGRESQL in infra:
            print("Installing PostgreSQL using Flux...")
            args = (f"""
            flux create secret git github-token --url=https://github.com/synpulse-group/pulse8-core-env-postgresql.git --username={github_user} --password={github_token} --namespace=flux-system ;
            flux create source git pulse8-core-env-postgresql-repo --url=https://github.com/synpulse-group/pulse8-core-env-postgresql.git --branch=main --secret-ref=github-token ;
            flux create kustomization pulse8-core-env-postgresql --source=GitRepository/pulse8-core-env-postgresql-repo --interval=1m --prune=true --target-namespace=default ;
            """)
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install PostgreSQL using Flux[/bold red]")
                print(res[1].decode('ascii'))
                exit(1)
            print(f"[green]Installed PostgreSQL using Flux[/green]")
            print(res[0].decode('ascii'))
        if KEY_CHOICES_INFRA_KAFKA in infra:
            print("Installing Kafka (Confluent for Kubernetes) using Flux...")
            args = (f"""
            flux create secret git github-token --url=https://github.com/synpulse-group/pulse8-core-env-postgresql.git --username={github_user} --password={github_token} --namespace=flux-system ;
            flux create source git pulse8-core-env-kafka-repo --url=https://github.com/synpulse-group/pulse8-core-env-kafka.git --branch=main --secret-ref=github-token ;
            flux create kustomization pulse8-core-env-kafka --source=GitRepository/pulse8-core-env-kafka-repo --interval=1m --prune=true --target-namespace=default ;
            """)
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Kafka (Confluent for Kubernetes) using Flux[/bold red]")
                print(res[1].decode('ascii'))
                exit(1)
            print(f"[green]Installed Kafka (Confluent for Kubernetes) using Flux[/green]")
            print(res[0].decode('utf8'))
        if KEY_CHOICES_INFRA_REDIS in infra:
            print("Installing Redis using Flux...")
            args = (f"""
            flux create secret git github-token --url=https://github.com/synpulse-group/pulse8-core-env-postgresql.git --username={github_user} --password={github_token} --namespace=flux-system ;
            flux create source git pulse8-core-env-redis-repo --url=https://github.com/synpulse-group/pulse8-core-env-redis.git --branch=main --secret-ref=github-token ;
            flux create kustomization pulse8-core-env-redis --source=GitRepository/pulse8-core-env-redis-repo --interval=1m --prune=true --target-namespace=default ;
            """)
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Redis using Flux[/bold red]")
                print(res[1].decode('ascii'))
                exit(1)
            print(f"[green]Installed Redis using Flux[/green]")
            print(res[0].decode('ascii'))
        if KEY_CHOICES_INFRA_EXASOL in infra:
            print("Installing Exasol using Flux...")
            args = (f"""
            flux create secret git github-token --url=https://github.com/synpulse-group/pulse8-core-env-postgresql.git --username={github_user} --password={github_token} --namespace=flux-system ;
            flux create source git pulse8-core-env-exasol-repo --url=https://github.com/synpulse-group/pulse8-core-env-exasol.git --branch=main --secret-ref=github-token ;
            flux create kustomization pulse8-core-env-exasol --source=GitRepository/pulse8-core-env-exasol-repo --interval=1m --prune=true --target-namespace=default ;
            """)
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Exasol using Flux[/bold red]")
                print(res[1].decode('ascii'))
                exit(1)
            print(f"[green]Installed Exasol using Flux[/green]")
            print(res[0].decode('utf8'))
        if KEY_CHOICES_INFRA_TEEDY in infra:
            print("Installing Teedy using Flux...")
            args = (f"""
            flux create secret git github-token --url=https://github.com/synpulse-group/pulse8-core-env-postgresql.git --username={github_user} --password={github_token} --namespace=flux-system ;
            flux create source git pulse8-core-env-teedy-repo --url=https://github.com/synpulse-group/pulse8-core-env-teedy.git --branch=main --secret-ref=github-token ;
            flux create kustomization pulse8-core-env-teedy --source=GitRepository/pulse8-core-env-teedy-repo --interval=1m --prune=true --target-namespace=default ;
            """)
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Teedy using Flux[/bold red]")
                print(res[1].decode('ascii'))
                exit(1)
            print(f"[green]Installed Teedy using Flux[/green]")
            print(res[0].decode('utf8'))
    if KEY_CHOICES_SERVICES_CORE in choices:
        services_core = choices[KEY_CHOICES_SERVICES_CORE]
        if KEY_CHOICES_SERVICES_CORE_IAM in services_core:
            print("Deployment of Pulse8 Core IAM not yet implemented...")
        if KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE in services_core:
            print("Deployment of Pulse8 Core Notification Engine not yet implemented...")
        if KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE in services_core:
            print("Deployment of Pulse8 Core Query Engine not yet implemented...")
        if KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE in services_core:
            print("Deployment of Pulse8 Core Workflow Engine not yet implemented...")
    if choices_old is not None:
        if KEY_CHOICES_INFRA in choices_old:
            choices_infra = choices[KEY_CHOICES_INFRA]
            choices_infra_old = choices_old[KEY_CHOICES_INFRA]
            if KEY_CHOICES_INFRA_POSTGRESQL not in choices_infra and KEY_CHOICES_INFRA_POSTGRESQL in choices_infra_old:
                print("Uninstalling PostgreSQL using Flux...")
                args = (f"""
                flux delete source git pulse8-core-env-postgresql-repo -s ;
                flux delete kustomization pulse8-core-env-postgresql -s
                """)
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall PostgreSQL using Flux[/bold red]")
                    print(res[1].decode('ascii'))
                    exit(1)
                print(f"[green]Uninstalled PostgreSQL using Flux[/green]")
                print(res[0].decode('ascii'))
            if KEY_CHOICES_INFRA_KAFKA not in choices_infra and KEY_CHOICES_INFRA_KAFKA in choices_infra_old:
                print("Uninstalling Kafka (Confluent for Kubernetes) using Flux...")
                args = (f"""
                flux delete source git pulse8-core-env-kafka-repo -s ;
                flux delete kustomization pulse8-core-env-kafka -s
                """)
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Kafka (Confluent for Kubernetes) using Flux[/bold red]")
                    print(res[1].decode('ascii'))
                    exit(1)
                print(f"[green]Uninstalled Kafka (Confluent for Kubernetes) using Flux[/green]")
                print(res[0].decode('ascii'))
            if KEY_CHOICES_INFRA_REDIS not in choices_infra and KEY_CHOICES_INFRA_REDIS in choices_infra_old:
                print("Uninstalling Redis using Flux...")
                args = (f"""
                flux delete source git pulse8-core-env-redis-repo -s ;
                flux delete kustomization pulse8-core-env-redis -s
                """)
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Redis using Flux[/bold red]")
                    print(res[1].decode('ascii'))
                    exit(1)
                print(f"[green]Uninstalled Redis using Flux[/green]")
                print(res[0].decode('ascii'))
            if KEY_CHOICES_INFRA_EXASOL not in choices_infra and KEY_CHOICES_INFRA_EXASOL in choices_infra_old:
                print("Uninstalling Exasol using Flux...")
                args = (f"""
                flux delete source git pulse8-core-env-exasol-repo -s ;
                flux delete kustomization pulse8-core-env-exasol -s
                """)
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Exasol using Flux[/bold red]")
                    print(res[1].decode('ascii'))
                    exit(1)
                print(f"[green]Uninstalled Exasol using Flux[/green]")
                print(res[0].decode('ascii'))
            if KEY_CHOICES_INFRA_TEEDY not in choices_infra and KEY_CHOICES_INFRA_TEEDY in choices_infra_old:
                print("Uninstalling Teedy using Flux...")
                args = (f"""
                flux delete source git pulse8-core-env-teedy-repo -s ;
                flux delete kustomization pulse8-core-env-teedy -s
                """)
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Teedy using Flux[/bold red]")
                    print(res[1].decode('ascii'))
                    exit(1)
                print(f"[green]Uninstalled Teedy using Flux[/green]")
                print(res[0].decode('ascii'))


def env_list():
    args = (f"k3d cluster list")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('ascii'))


def env_switch(identifier: str):
    print(f"[bold]stopping all running environments...[/bold]")
    args = ("k3d cluster list --no-headers | head -n3 | awk '{print $1;}' | xargs k3d cluster stop ")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('ascii'))
    print(f"[bold]starting environment (id: {identifier})...[/bold]")
    args = (f"k3d cluster start {identifier}")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('ascii'))
    print(f"[green]switching to environment context in kubeconfig (id: {identifier})...[/green]")
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


def get_questions(preselection_infra: list[str] = None,
                  preselection_services_core: list[str] = None) -> list[Checkbox]:
    if preselection_infra is None:
        preselection_infra = [KEY_CHOICES_INFRA_POSTGRESQL, KEY_CHOICES_INFRA_KAFKA]
    if preselection_services_core is None:
        preselection_services_core = [KEY_CHOICES_SERVICES_CORE_IAM]
    if is_cpu_arm:
        choices_infra = [
            ("PostgreSQL", KEY_CHOICES_INFRA_POSTGRESQL),
            ("Kafka (Confluent for Kubernetes)", KEY_CHOICES_INFRA_KAFKA),
            ("Redis", KEY_CHOICES_INFRA_REDIS),
            # not supported on arm64 - maybe bring proxy solution in place
            # ("Exasol", KEY_CHOICES_INFRA_EXASOL),
            ("Teedy", KEY_CHOICES_INFRA_TEEDY),
        ]
    else:
        choices_infra = [
            ("PostgreSQL", KEY_CHOICES_INFRA_POSTGRESQL),
            ("Kafka (Confluent for Kubernetes)", KEY_CHOICES_INFRA_KAFKA),
            ("Redis", KEY_CHOICES_INFRA_REDIS),
            ("Exasol", KEY_CHOICES_INFRA_EXASOL),
            ("Teedy", KEY_CHOICES_INFRA_TEEDY),
        ]
    questions = [
        inquirer.Checkbox(
            name=KEY_CHOICES_INFRA,
            message="Which infrastructure do you need?",
            choices=choices_infra,
            default=preselection_infra
        ),
        inquirer.Checkbox(
            name=KEY_CHOICES_SERVICES_CORE,
            message="Which Pulse8 Core services do you need?",
            choices=[
                KEY_CHOICES_SERVICES_CORE_IAM,
                KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE,
                KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE,
                KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE
            ],
            default=preselection_services_core,
        )
    ]
    return questions
