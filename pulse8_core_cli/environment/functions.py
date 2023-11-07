import base64
import json
import os
import re
import subprocess

import inquirer
import yaml
from inquirer import Checkbox
from rich import print

from pulse8_core_cli.environment.constants import KEY_CHOICES_INFRA, KEY_CHOICES_INFRA_POSTGRESQL, \
    KEY_CHOICES_INFRA_REDIS, KEY_CHOICES_INFRA_KAFKA, KEY_CHOICES_INFRA_EXASOL, KEY_CHOICES_INFRA_TEEDY, \
    KEY_CHOICES_SERVICES_CORE, KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE, KEY_CHOICES_SERVICES_CORE_IAM, \
    KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE, KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE, SERVICES, \
    SERVICES_DEPENDENCIES_INFRA, SERVICES_DEPENDENCIES_SERVICES
from pulse8_core_cli.shared.module import ENV_GITHUB_TOKEN, ENV_GITHUB_USER, ENV_JFROG_TOKEN
from pulse8_core_cli.util.platform_discovery import is_cpu_arm


def env_precheck():
    print("[bold]running environment precheck...[bold]")
    try:
        github_token = os.environ[ENV_GITHUB_TOKEN]
        github_user = os.environ[ENV_GITHUB_USER]
        print(f"[green]github authentication set to user {github_user}[/green]")
        jfrog_token = os.environ[ENV_JFROG_TOKEN]
        print(f"[green]jfrog authentication set[/green]")
        print("environment precheck done - continue...")
    except KeyError:
        print("[bold red]please set GITHUB_TOKEN, GITHUB_USER and JFROG_TOKEN environment variables (more info: tbd)"
              "[/bold red]")
        exit(1)


def env_create(identifier: str):
    print(f"[bold]starting environment (id: {identifier})...[/bold]")
    args = ("k3d", "cluster", "create", identifier)
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed starting environment (id: {identifier})[/bold red]")
        print(res[1].decode('utf8'))
        exit(1)
    print(f"[green]started environment (id: {identifier})[/green]")
    print(res[0].decode('utf8'))
    print(f"installing flux into environment (id: {identifier})...")
    args = ("flux", "install")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed installing flux into environment (id: {identifier})[/bold red]")
        print(res[1].decode('utf8'))
        exit(1)
    print(f"[green]installed flux into environment (id: {identifier})[/green]")
    print(res[0].decode('utf8'))
    print(f"installing pull secrets into environment (id: {identifier})...")
    # github container registry (ghcr)
    ghcr_dockerconfigjson = dict()
    ghcr_dockerconfigjson["auths"] = dict()
    ghcr_dockerconfigjson["auths"]["ghcr.io"] = dict()
    ghcr_credentials_encoded = base64.b64encode(
        bytes(f"{os.environ[ENV_GITHUB_USER]}:{os.environ[ENV_GITHUB_TOKEN]}", "ascii")
    )
    ghcr_dockerconfigjson["auths"]["ghcr.io"]["auth"] = ghcr_credentials_encoded.decode("utf8")
    ghcr_dockerconfigjson_json = json.dumps(ghcr_dockerconfigjson)
    ghcr_dockerconfigjson_path = "ghcr_dockerconfig.json"
    with open(ghcr_dockerconfigjson_path, "w") as ghcr_dockerconfigjson_file:
        ghcr_dockerconfigjson_file.write(ghcr_dockerconfigjson_json)
    args = ("kubectl", "create", "secret", "generic", "synpulse-ghcr-docker-credential",
            f"--from-file=.dockerconfigjson={ghcr_dockerconfigjson_path}",
            "--type=kubernetes.io/dockerconfigjson")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed installing pull secrets (ghcr.io) into environment (id: {identifier})"
              f"[/bold red]")
        print(res[1].decode('utf8'))
        exit(1)
    print(res[0].decode('utf8'))
    # jfrog container registry
    jfrog_dockerconfigjson = dict()
    jfrog_dockerconfigjson["auths"] = dict()
    jfrog_dockerconfigjson["auths"]["ghcr.io"] = dict()
    jfrog_dockerconfigjson["auths"]["ghcr.io"]["auth"] = os.environ[ENV_JFROG_TOKEN]
    jfrog_dockerconfigjson_json = json.dumps(jfrog_dockerconfigjson)
    jfrog_dockerconfigjson_path = "jfrog_dockerconfig.json"
    with open(jfrog_dockerconfigjson_path, "w") as jfrog_dockerconfigjson_file:
        jfrog_dockerconfigjson_file.write(jfrog_dockerconfigjson_json)
    args = ("kubectl", "create", "secret", "generic", "synpulse-jfrog-docker-credential",
            f"--from-file=.dockerconfigjson={jfrog_dockerconfigjson_path}",
            "--type=kubernetes.io/dockerconfigjson")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed installing pull secrets (synpulse.jfrog.io) into environment (id: {identifier})"
              f"[/bold red]")
        print(res[1].decode('utf8'))
        exit(1)
    print(res[0].decode('utf8'))
    print(f"[green]installed pull secrets (ghcr.io, synpulse.jfrog.io) into environment (id: {identifier})[/green]\n")
    os.remove(ghcr_dockerconfigjson_path)
    os.remove(jfrog_dockerconfigjson_path)
    choices = inquirer.prompt(get_questions())
    choices_yaml = yaml.dump(choices)
    choices_yaml_path = "choices.yaml"
    with open(choices_yaml_path, "w") as choices_yaml_file:
        choices_yaml_file.write(choices_yaml)
    print(f"saving choices into configmap pulse8-core-cli-env...")
    args = ("kubectl", "create", "configmap", "pulse8-core-cli-config", "--from-file=choices.yaml")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed to save into configmap pulse8-core-cli-config[/bold red]")
        print(res[1].decode('utf8'))
        exit(1)
    print(f"[green]saved choices into configmap pulse8-core-cli-config[/green]")
    print(res[0].decode('utf8'))
    os.remove(choices_yaml_path)
    env_install_choices(choices)


def env_update():
    print(f"[bold]collecting information about current context...[/bold]")
    args = ("kubectl", "config", "current-context")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed collecting information - sandbox name[/bold red]")
        print(res[1].decode('utf8'))
        exit(1)
    identifier = res[0].decode('utf8')
    identifier = re.sub(r"^k3d-", "", identifier)
    identifier = re.sub(r"\s", "", identifier)
    args = ("kubectl", "--namespace", "default", "get", "configmap", "pulse8-core-cli-config", "-o", "yaml")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed collecting information - previous configuration[/bold red]")
        print(res[1].decode('utf8'))
        exit(1)
    configmap_raw = res[0].decode('utf8')
    configmap = yaml.load(configmap_raw, yaml.Loader)
    choices_old = yaml.load(configmap['data']['choices.yaml'], yaml.Loader)
    print(f"[green]collected information about current context[/green]")
    print(f"[bold]updating environment (id: {identifier})...[/bold]\n")
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
    args = ("kubectl", "delete", "configmap", "pulse8-core-cli-config")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed to delete previous configmap pulse8-core-cli-config[/bold red]")
        print(res[1].decode('utf8'))
        exit(1)
    print(res[0].decode('utf8'))
    args = ("kubectl", "create", "configmap", "pulse8-core-cli-config", "--from-file=choices.yaml")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed to save into configmap pulse8-core-cli-config[/bold red]")
        print(res[1].decode('utf8'))
        exit(1)
    print(f"[green]saved choices into configmap pulse8-core-cli-config[/green]")
    print(res[0].decode('utf8'))
    os.remove(choices_yaml_path)
    env_install_choices(choices=choices, choices_old=choices_old)


def env_install_choices(choices: dict, choices_old: dict | None = None):
    github_token = os.environ[ENV_GITHUB_TOKEN]
    github_user = os.environ[ENV_GITHUB_USER]
    print("Installing GitHub token using Flux...")
    args = ("flux", "create", "secret", "git", "github-token", "--url=https://github.com/synpulse-group/pulse8-core-env-postgresql.git", f"--username={github_user}", f"--password={github_token}", "--namespace=flux-system")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]Failed to install GitHub token using Flux[/bold red]")
        print(res[1].decode('utf8'))
        exit(1)
    print(res[0].decode('utf8'))
    print(f"[green]Installed GitHub token using Flux[/green]")
    # update choices using dependencies
    print(f"Making sure infrastructure dependencies are selected...")
    update_infra_choices_with_deps(choices)
    print(f"Making sure service dependencies are selected...")
    update_service_choices_with_deps(choices)
    if KEY_CHOICES_INFRA in choices:
        infra = choices[KEY_CHOICES_INFRA]
        if KEY_CHOICES_INFRA_POSTGRESQL in infra:
            print("Installing PostgreSQL using Flux...")
            args = ("flux", "create", "source", "git", "pulse8-core-env-postgresql-repo",
                    "--url=https://github.com/synpulse-group/pulse8-core-env-postgresql.git", "--branch=main",
                    "--secret-ref=github-token")
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install PostgreSQL git source using Flux[/bold red]")
                print(res[1].decode('utf8'))
                exit(1)
            print(f"[green]Installed PostgreSQL git source using Flux[/green]")
            print(res[0].decode('utf8'))
            args = ("flux", "create", "kustomization", "pulse8-core-env-postgresql",
                    "--source=GitRepository/pulse8-core-env-postgresql-repo", "--interval=1m", "--prune=true",
                    "--target-namespace=default")
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install PostgreSQL using Flux[/bold red]")
                print(res[1].decode('utf8'))
                exit(1)
            print(f"[green]Installed PostgreSQL using Flux[/green]")
            print(res[0].decode('utf8'))
        if KEY_CHOICES_INFRA_KAFKA in infra:
            print("Installing Kafka (Confluent for Kubernetes) using Flux...")
            args = ("flux", "create", "source", "git", "pulse8-core-env-kafka-repo",
                    "--url=https://github.com/synpulse-group/pulse8-core-env-kafka.git", "--branch=main",
                    "--secret-ref=github-token")
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Kafka git source using Flux[/bold red]")
                print(res[1].decode('utf8'))
                exit(1)
            print(f"[green]Installed Kafka git source using Flux[/green]")
            print(res[0].decode('utf8'))
            args = ("flux", "create", "kustomization", "pulse8-core-env-kafka",
                    "--source=GitRepository/pulse8-core-env-kafka-repo", "--interval=1m", "--prune=true",
                    "--target-namespace=default")
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Kafka (Confluent for Kubernetes) using Flux[/bold red]")
                print(res[1].decode('utf8'))
                exit(1)
            print(f"[green]Installed Kafka (Confluent for Kubernetes) using Flux[/green]")
            print(res[0].decode('utf8'))
        if KEY_CHOICES_INFRA_REDIS in infra:
            print("Installing Redis using Flux...")
            args = ("flux", "create", "source", "git", "pulse8-core-env-redis-repo",
                    "--url=https://github.com/synpulse-group/pulse8-core-env-redis.git", "--branch=main",
                    "--secret-ref=github-token")
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Redis git source using Flux[/bold red]")
                print(res[1].decode('utf8'))
                exit(1)
            print(f"[green]Installed Redis git source using Flux[/green]")
            print(res[0].decode('utf8'))
            args = ("flux", "create", "kustomization", "pulse8-core-env-redis",
                    "--source=GitRepository/pulse8-core-env-redis-repo", "--interval=1m", "--prune=true",
                    "--target-namespace=default")
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Redis using Flux[/bold red]")
                print(res[1].decode('utf8'))
                exit(1)
            print(f"[green]Installed Redis using Flux[/green]")
            print(res[0].decode('utf8'))
        if KEY_CHOICES_INFRA_EXASOL in infra:
            print("Installing Exasol using Flux...")
            args = ("flux", "create", "source", "git", "pulse8-core-env-exasol-repo",
                    "--url=https://github.com/synpulse-group/pulse8-core-env-exasol.git", "--branch=main",
                    "--secret-ref=github-token")
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Exasol git source using Flux[/bold red]")
                print(res[1].decode('utf8'))
                exit(1)
            print(f"[green]Installed Exasol git source using Flux[/green]")
            print(res[0].decode('utf8'))
            args = ("flux", "create", "kustomization", "pulse8-core-env-exasol",
                    "--source=GitRepository/pulse8-core-env-exasol-repo", "--interval=1m", "--prune=true",
                    "--target-namespace=default")
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Exasol using Flux[/bold red]")
                print(res[1].decode('utf8'))
                exit(1)
            print(f"[green]Installed Exasol using Flux[/green]")
            print(res[0].decode('utf8'))
        if KEY_CHOICES_INFRA_TEEDY in infra:
            print("Installing Teedy using Flux...")
            args = ("flux", "create", "source", "git", "pulse8-core-env-teedy-repo",
                    "--url=https://github.com/synpulse-group/pulse8-core-env-teedy.git", "--branch=main",
                    "--secret-ref=github-token")
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Teedy git source using Flux[/bold red]")
                print(res[1].decode('utf8'))
                exit(1)
            print(f"[green]Installed Teedy git source using Flux[/green]")
            print(res[0].decode('utf8'))
            args = ("flux", "create", "kustomization", "pulse8-core-env-teedy",
                    "--source=GitRepository/pulse8-core-env-teedy-repo", "--interval=1m", "--prune=true",
                    "--target-namespace=default")
            pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Teedy using Flux[/bold red]")
                print(res[1].decode('utf8'))
                exit(1)
            print(f"[green]Installed Teedy using Flux[/green]")
            print(res[0].decode('utf8'))
    if KEY_CHOICES_SERVICES_CORE in choices:
        services_core = choices[KEY_CHOICES_SERVICES_CORE]
        for service_core_key in services_core:
            install_service(service_core_key)
    if choices_old is not None:
        if KEY_CHOICES_INFRA in choices_old:
            choices_infra = choices[KEY_CHOICES_INFRA]
            choices_infra_old = choices_old[KEY_CHOICES_INFRA]
            if KEY_CHOICES_INFRA_POSTGRESQL not in choices_infra and KEY_CHOICES_INFRA_POSTGRESQL in choices_infra_old:
                print("Uninstalling PostgreSQL using Flux...")
                args = ("flux", "delete", "source", "git", "pulse8-core-env-postgresql-repo", "-s")
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall PostgreSQL git source using Flux[/bold red]")
                    print(res[1].decode('utf8'))
                    exit(1)
                print(res[0].decode('utf8'))
                args = ("flux", "delete", "kustomization", "pulse8-core-env-postgresql", "-s")
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall PostgreSQL using Flux[/bold red]")
                    print(res[1].decode('utf8'))
                    exit(1)
                print(f"[green]Uninstalled PostgreSQL using Flux[/green]")
                print(res[0].decode('utf8'))
            if KEY_CHOICES_INFRA_KAFKA not in choices_infra and KEY_CHOICES_INFRA_KAFKA in choices_infra_old:
                print("Uninstalling Kafka (Confluent for Kubernetes) using Flux...")
                args = ("flux", "delete", "source", "git", "pulse8-core-env-kafka-repo", "-s")
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Kafka (Confluent for Kubernetes) git source using Flux[/bold red]")
                    print(res[1].decode('utf8'))
                    exit(1)
                print(res[0].decode('utf8'))
                args = ("flux", "delete", "kustomization", "pulse8-core-env-kafka", "-s")
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Kafka (Confluent for Kubernetes) using Flux[/bold red]")
                    print(res[1].decode('utf8'))
                    exit(1)
                print(f"[green]Uninstalled Kafka (Confluent for Kubernetes) using Flux[/green]")
                print(res[0].decode('utf8'))
            if KEY_CHOICES_INFRA_REDIS not in choices_infra and KEY_CHOICES_INFRA_REDIS in choices_infra_old:
                print("Uninstalling Redis using Flux...")
                args = ("flux", "delete", "source", "git", "pulse8-core-env-redis-repo", "-s")
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Redis git source using Flux[/bold red]")
                    print(res[1].decode('utf8'))
                    exit(1)
                print(res[0].decode('utf8'))
                args = ("flux", "delete", "kustomization", "pulse8-core-env-redis", "-s")
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Redis using Flux[/bold red]")
                    print(res[1].decode('utf8'))
                    exit(1)
                print(f"[green]Uninstalled Redis using Flux[/green]")
                print(res[0].decode('utf8'))
            if KEY_CHOICES_INFRA_EXASOL not in choices_infra and KEY_CHOICES_INFRA_EXASOL in choices_infra_old:
                print("Uninstalling Exasol using Flux...")
                args = ("flux", "delete", "source", "git", "pulse8-core-env-exasol-repo", "-s")
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Exasol git source using Flux[/bold red]")
                    print(res[1].decode('utf8'))
                    exit(1)
                print(res[0].decode('utf8'))
                args = ("flux", "delete", "kustomization", "pulse8-core-env-exasol", "-s")
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Exasol using Flux[/bold red]")
                    print(res[1].decode('utf8'))
                    exit(1)
                print(f"[green]Uninstalled Exasol using Flux[/green]")
                print(res[0].decode('utf8'))
            if KEY_CHOICES_INFRA_TEEDY not in choices_infra and KEY_CHOICES_INFRA_TEEDY in choices_infra_old:
                print("Uninstalling Teedy using Flux...")
                args = ("flux", "delete", "source", "git", "pulse8-core-env-teedy-repo", "-s")
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Teedy git source using Flux[/bold red]")
                    print(res[1].decode('utf8'))
                    exit(1)
                print(res[0].decode('utf8'))
                args = ("flux", "delete", "kustomization", "pulse8-core-env-teedy", "-s")
                pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Teedy using Flux[/bold red]")
                    print(res[1].decode('utf8'))
                    exit(1)
                print(f"[green]Uninstalled Teedy using Flux[/green]")
                print(res[0].decode('utf8'))


def env_list():
    args = ("k3d", "cluster", "list")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('utf8'))


def env_switch(identifier: str):
    print(f"[bold]stopping all running environments...[/bold]")
    args = ("k3d", "cluster", "stop", "--all")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('utf8'))
    print(f"[bold]starting target environment (id: {identifier})...[/bold]")
    args = ("k3d", "cluster", "start", f"{identifier}")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('utf8'))
    print(f"[green]switching to target environment context in kubeconfig (id: {identifier})...[/green]")
    args = ("kubectl", "config", "use-context", f"k3d-{identifier}")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('utf8'))


def env_delete(identifier: str):
    print(f"[bold red]deleting the environment (id: {identifier})...[/bold red]")
    args = ("k3d", "cluster", "delete", f"{identifier}")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('utf8'))


def get_questions(preselection_infra: list[str] = None,
                  preselection_services_core: list[str] = None) -> list[Checkbox]:
    if preselection_infra is None:
        preselection_infra = [KEY_CHOICES_INFRA_POSTGRESQL, KEY_CHOICES_INFRA_KAFKA]
    if preselection_services_core is None:
        preselection_services_core = [KEY_CHOICES_SERVICES_CORE_IAM]
    if is_cpu_arm():
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


def update_infra_choices_with_deps(choices: dict) -> None:
    needed_infrastructure = choices[KEY_CHOICES_INFRA]
    for service_core in choices[KEY_CHOICES_SERVICES_CORE]:
        needed_infrastructure_for_service = SERVICES_DEPENDENCIES_INFRA[service_core]
        needed_infrastructure = needed_infrastructure + needed_infrastructure_for_service
    needed_infrastructure = list(set(needed_infrastructure))
    choices[KEY_CHOICES_INFRA] = needed_infrastructure


def update_service_choices_with_deps(choices: dict) -> None:
    needed_services_core = choices[KEY_CHOICES_SERVICES_CORE]
    for service_core in choices[KEY_CHOICES_SERVICES_CORE]:
        needed_services_core_for_service = SERVICES_DEPENDENCIES_SERVICES[service_core]
        needed_services_core = needed_services_core + needed_services_core_for_service
    needed_services_core = list(set(needed_services_core))
    choices[KEY_CHOICES_SERVICES_CORE] = needed_services_core
    update_infra_choices_with_deps(choices)


def install_service(service_key: str) -> None:
    print(f"Installing {SERVICES[service_key][0]} ({service_key}) using Flux...")
    args = ("flux", "create", "source", "git", f"{service_key}-repo", f"--url={SERVICES[service_key][1]}",
            "--branch=main", "--secret-ref=github-token")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]Failed to install {SERVICES[service_key][0]} ({service_key}) git source using Flux"
              f"[/bold red]")
        print(res[1].decode('utf8'))
        exit(1)
    print(res[0].decode('utf8'))
    print(f"[green]Installed {SERVICES[service_key][0]} ({service_key}) git source using Flux[/green]")
    args = ("flux", "create", "kustomization", f"{service_key}", f"--source=GitRepository/{service_key}-repo",
            "--interval=1m", "--prune=true", "--path=\"./k8s\"", "--target-namespace=default",
            "--wait=true", "--health-check-timeout=30s")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]Failed to install {SERVICES[service_key][0]} ({service_key}) using Flux"
              f"[/bold red]")
        print(res[1].decode('utf8'))
        exit(1)
    print(res[0].decode('utf8'))
    print(f"[green]Installed {SERVICES[service_key][0]} ({service_key}) using Flux[/green]")
