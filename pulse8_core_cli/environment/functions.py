import base64
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import inquirer
import yaml
from inquirer import Checkbox
from rich import print

from pulse8_core_cli.shared.module import execute_shell_command
from pulse8_core_cli.environment.constants import (
    KEY_CHOICES_INFRA,
    KEY_CHOICES_INFRA_POSTGRESQL,
    KEY_CHOICES_INFRA_REDIS,
    KEY_CHOICES_INFRA_KAFKA,
    KEY_CHOICES_INFRA_EXASOL,
    KEY_CHOICES_INFRA_TEEDY,
    KEY_CHOICES_SERVICES,
    KEY_CHOICES_SERVICES_NOTIFICATION_ENGINE,
    KEY_CHOICES_SERVICES_IAM,
    KEY_CHOICES_SERVICES_WORKFLOW_ENGINE,
    KEY_CHOICES_SERVICES_QUERY_ENGINE,
    SERVICES,
    SERVICES_DEPENDENCIES_INFRA,
    SERVICES_DEPENDENCIES_SERVICES,
    KEY_CHOICES_INFRA_KEYCLOAK,
    INFRA_DEPENDENCIES_INFRA,
    KEY_CHOICES_SERVICES_DOCUMENT_MANAGEMENT,
    KEY_CHOICES_INFRA_SPARK,
    KEY_CHOICES_INFRA_NIFI,
    KEY_CHOICES_INFRA_AIRFLOW,
    KEY_CHOICES_INFRA_SUPERSET,
    KEY_CHOICES_INFRA_MARIADB,
    KEY_CHOICES_INFRA_CLOUDSERVER,
    KEY_CHOICES_INFRA_PINOT,
    KEY_CHOICES_SERVICES_ACCESS_CONTROL,
)
from pulse8_core_cli.shared.constants import (
    ENV_GITHUB_TOKEN,
    ENV_GITHUB_USER,
    ENV_JFROG_TOKEN,
    ENV_JFROG_USER,
    ENV_GITHUB_GHCR_TOKEN,
)
from pulse8_core_cli.shared.module import (
    get_certificates_dir_path,
    get_env_variables,
    get_environments_dir_path,
)
from pulse8_core_cli.shared.platform_discovery import is_cpu_arm


def env_precheck():
    print("[bold]running environment precheck...[/bold]")
    try:
        env_vars = get_env_variables()
        github_ghcr_token = env_vars[ENV_GITHUB_GHCR_TOKEN]
        github_token = env_vars[ENV_GITHUB_TOKEN]
        github_user = env_vars[ENV_GITHUB_USER]
        jfrog_token = env_vars[ENV_JFROG_TOKEN]
        jfrog_user = env_vars[ENV_JFROG_USER]
        print(f"[green]JFrog authentication set[/green]")
    except KeyError:
        print(
            "[bold][red]environment precheck failed - env variables not set...[/red][/bold]"
        )
        print("[italic]Hint: Try [bold]pulse8 auth login[/bold][/italic]")
        exit(1)
    create_certificates()
    print("environment precheck done - continue...")


def env_create(
    identifier: str, from_env: str | None = None, from_file: str | None = None
):
    env_vars = get_env_variables(silent=True)
    stop_all_env()
    print(f"preparing environment (id: {identifier})...")
    print(f"[bold]starting environment (id: {identifier})...[/bold]")
    args = (
        "k3d",
        "cluster",
        "create",
        "-p80:80@loadbalancer",
        "-p443:443@loadbalancer",
        "--k3s-arg",
        "--disable=traefik@server:0",
        identifier,
    )
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed starting environment (id: {identifier})[/bold red]")
        print(res[1].decode("utf8"))
        exit(1)
    print(f"[green]started environment (id: {identifier})[/green]")
    print(res[0].decode("utf8"))
    print(
        f"[bold]starting post creation steps for environment (id: {identifier})...[/bold]"
    )
    execute_shell_command(
        command_array=[
            "kubectl",
            "-n",
            "kube-system",
            "rollout",
            "status",
            "deployment",
            "coredns",
        ],
        message_failure=f"[bold red]failed to wait for coredns init[/bold red]",
        message_success=f"[green]coredns init[/green]",
    )
    configmap_coredns_source = execute_shell_command(
        command_array=[
            "kubectl",
            "-n",
            "kube-system",
            "get",
            "configmap",
            "coredns",
            "-o",
            "yaml",
        ],
        message_failure=f"[bold red]failed read coredns configuration[/bold red]",
        message_success=f"[green]read coredns configuration[/green]",
    )
    configmap_coredns_source_path = "configmap_coredns_source.yaml"
    with open(configmap_coredns_source_path, "w") as configmap_coredns_source_file:
        configmap_coredns_source = configmap_coredns_source.replace(
            "ready\n        kubernetes",
            "ready\n"
            "        rewrite stop {\n"
            "          name regex (.*\.)?local\.synpulse8\.com host.k3d.internal\n"
            "        }\n"
            "        kubernetes",
            1,
        )
        configmap_coredns_source_file.write(configmap_coredns_source)
    execute_shell_command(
        command_array=[
            "kubectl",
            "-n",
            "kube-system",
            "apply",
            "-f",
            configmap_coredns_source_path,
        ],
        message_failure=f"[bold red]failed to apply new coredns configuration[/bold red]",
        message_success=f"[green]applied new coredns configuration[/green]",
    )
    execute_shell_command(
        command_array=[
            "kubectl",
            "-n",
            "kube-system",
            "rollout",
            "restart",
            "deployment",
            "coredns",
        ],
        message_failure=f"[bold red]failed to restart coredns deployment[/bold red]",
        message_success=f"[green]restarted coredns deployment[/green]",
    )
    os.remove(configmap_coredns_source_path)
    print(f"installing flux into environment (id: {identifier})...")
    args = ("flux", "install")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(
            f"[bold red]failed installing flux into environment (id: {identifier})[/bold red]"
        )
        print(res[1].decode("utf8"))
        exit(1)
    print(f"[green]installed flux into environment (id: {identifier})[/green]")
    print(res[0].decode("utf8"))
    print(f"installing pull secrets into environment (id: {identifier})...")
    # github container registry (ghcr)
    ghcr_dockerconfigjson = dict()
    ghcr_dockerconfigjson["auths"] = dict()
    ghcr_dockerconfigjson["auths"]["ghcr.io"] = dict()
    ghcr_credentials_encoded = base64.b64encode(
        bytes(env_vars[ENV_GITHUB_GHCR_TOKEN], "ascii")
    )
    ghcr_dockerconfigjson["auths"]["ghcr.io"]["auth"] = ghcr_credentials_encoded.decode(
        "utf8"
    )
    ghcr_dockerconfigjson_json = json.dumps(ghcr_dockerconfigjson)
    ghcr_dockerconfigjson_path = "ghcr_dockerconfig.json"
    with open(ghcr_dockerconfigjson_path, "w") as ghcr_dockerconfigjson_file:
        ghcr_dockerconfigjson_file.write(ghcr_dockerconfigjson_json)
    args = (
        "kubectl",
        "create",
        "secret",
        "generic",
        "synpulse-ghcr-docker-credential",
        f"--from-file=.dockerconfigjson={ghcr_dockerconfigjson_path}",
        "--type=kubernetes.io/dockerconfigjson",
    )
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(
            f"[bold red]failed installing pull secrets (ghcr.io) into environment (id: {identifier})"
            f"[/bold red]"
        )
        print(res[1].decode("utf8"))
        exit(1)
    print(res[0].decode("utf8"))
    # jfrog container registry
    jfrog_dockerconfigjson = dict()
    jfrog_dockerconfigjson["auths"] = dict()
    jfrog_dockerconfigjson["auths"]["synpulse.jfrog.io"] = dict()
    jfrog_dockerconfigjson["auths"]["synpulse.jfrog.io"]["auth"] = env_vars[
        ENV_JFROG_TOKEN
    ]
    jfrog_dockerconfigjson_json = json.dumps(jfrog_dockerconfigjson)
    jfrog_dockerconfigjson_path = "jfrog_dockerconfig.json"
    with open(jfrog_dockerconfigjson_path, "w") as jfrog_dockerconfigjson_file:
        jfrog_dockerconfigjson_file.write(jfrog_dockerconfigjson_json)
    args = (
        "kubectl",
        "create",
        "secret",
        "generic",
        "synpulse-jfrog-docker-credential",
        f"--from-file=.dockerconfigjson={jfrog_dockerconfigjson_path}",
        "--type=kubernetes.io/dockerconfigjson",
    )
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(
            f"[bold red]failed installing pull secrets (synpulse.jfrog.io) into environment (id: {identifier})[/bold red]"
        )
        print(res[1].decode("utf8"))
        exit(1)
    print(res[0].decode("utf8"))
    execute_shell_command(
        command_array=[
            "kubectl",
            "-n",
            "flux-system",
            "create",
            "secret",
            "generic",
            "synpulse-jfrog-docker-credential",
            f"--from-file=.dockerconfigjson={jfrog_dockerconfigjson_path}",
            "--type=kubernetes.io/dockerconfigjson",
        ],
        message_failure=f"[bold red]failed installing pull secrets (synpulse.jfrog.io/flux-system) into environment (id: {identifier})[/bold red]",
        message_success=f"[green]installed pull secrets (synpulse.jfrog.io/flux-system) into environment (id: {identifier})[/green]",
    )
    print(
        f"[green]installed pull secrets (ghcr.io, synpulse.jfrog.io) into environment (id: {identifier})[/green]"
    )
    os.remove(ghcr_dockerconfigjson_path)
    os.remove(jfrog_dockerconfigjson_path)

    # Pulse8 helm charts repo
    execute_shell_command(
        command_array=[
            "flux",
            "create",
            "source",
            "helm",
            "pulse8-helm-charts-oci",
            "--url=oci://synpulse.jfrog.io/pulse8-helm-charts",
            "--secret-ref=synpulse-jfrog-docker-credential",
            "--interval=15m",
        ],
        message_failure=f"failed installing pulse8-helm-charts-oci repository (synpulse.jfrog.io/pulse8-helm-charts) into environment (id: {identifier})",
        message_success=f"installed pulse8-helm-charts-oci repository (synpulse.jfrog.io/pulse8-helm-charts) into environment (id: {identifier})",
    )

    if from_env is not None:
        choices, services = get_choices_from_env(from_env)
        env_check_and_update_deps(choices)
    elif from_file is not None:
        choices, services = get_choices_from_file(from_file)
        env_check_and_update_deps(choices)
    else:
        choices = inquirer.prompt(get_questions())
        services = SERVICES
    env_check_and_update_deps(choices)
    env_install_choices(choices=choices, services=services)
    store_env_setup(identifier=identifier, choices=choices, services=services)


def env_update():
    print(f"[bold]collecting information about current context...[/bold]")
    args = ("kubectl", "config", "current-context")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]failed collecting information - sandbox name[/bold red]")
        print(res[1].decode("utf8"))
        exit(1)
    identifier = res[0].decode("utf8")
    identifier = re.sub(r"^k3d-", "", identifier)
    identifier = re.sub(r"\s", "", identifier)
    (choices_fs, choices_configmap) = read_env_setup(identifier)
    print(f"[green]collected information about current context[/green]")
    print(f"[bold]updating environment (id: {identifier})...[/bold]")
    (preselection_infra, preselection_services) = get_preselection_from_setup(
        choices_configmap
    )
    choices = inquirer.prompt(get_questions(preselection_infra, preselection_services))
    env_check_and_update_deps(choices)
    env_install_choices(
        choices=choices, choices_old=choices_fs, services=choices_configmap["services"]
    )
    store_env_setup(identifier, choices)


def env_install_ingress_nginx() -> None:
    do_default_tls_install: bool
    args = ("kubectl", "get", "secret", "pulse8-localhost", "--namespace=kube-system")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        do_default_tls_install = True
    else:
        do_default_tls_install = False
    if not do_default_tls_install:
        return
    print("Installing ingress-nginx using Flux...")
    key_path = get_certificates_dir_path().joinpath("key.pem")
    cert_path = get_certificates_dir_path().joinpath("cert.pem")
    print("Installing default tls certificate...")
    args = (
        "kubectl",
        "create",
        "secret",
        "tls",
        "pulse8-localhost",
        f"--key={str(key_path)}",
        f"--cert={str(cert_path)}",
        "--namespace=kube-system",
    )
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]Failed to install default tls certificate[/bold red]")
        print(res[1].decode("utf8"))
        exit(1)
    print(res[0].decode("utf8"))
    print(f"[green]Installed default tls certificate[/green]")
    print("Installing default tls certificate into default namespace...")
    args = (
        "kubectl",
        "create",
        "secret",
        "tls",
        "pulse8-localhost",
        f"--key={str(key_path)}",
        f"--cert={str(cert_path)}",
        "--namespace=default",
    )
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(
            f"[bold red]Failed to install default tls certificate into default namespace[/bold red]"
        )
        print(res[1].decode("utf8"))
        exit(1)
    print(res[0].decode("utf8"))
    print(f"[green]Installed default tls certificate into default namespace[/green]")
    args = (
        "flux",
        "create",
        "source",
        "git",
        "pulse8-core-env-ingress-nginx-repo",
        "--url=https://github.com/synpulse-group/pulse8-core-env-ingress-nginx.git",
        "--branch=main",
        "--secret-ref=github-token",
    )
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(
            f"[bold red]Failed to install ingress-nginx git source using Flux[/bold red]"
        )
        print(res[1].decode("utf8"))
        exit(1)
    print(res[0].decode("utf8"))
    print(f"[green]Installed ingress-nginx git source using Flux[/green]")
    args = (
        "flux",
        "create",
        "kustomization",
        "pulse8-core-env-ingress-nginx",
        "--source=GitRepository/pulse8-core-env-ingress-nginx-repo",
        "--interval=1m",
        "--prune=true",
        "--target-namespace=kube-system",
    )
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]Failed to install ingress-nginx using Flux[/bold red]")
        print(res[1].decode("utf8"))
        exit(1)
    print(res[0].decode("utf8"))
    print(f"[green]Installed ingress-nginx using Flux[/green]")


def env_install_choices(
    choices: dict, choices_old: dict | None = None, services=SERVICES
) -> None:
    env_vars = get_env_variables(silent=True)
    github_token = env_vars[ENV_GITHUB_TOKEN]
    github_user = env_vars[ENV_GITHUB_USER]
    print("Installing GitHub token using Flux...")
    args = (
        "flux",
        "create",
        "secret",
        "git",
        "github-token",
        "--url=https://github.com/synpulse-group/pulse8-core-env-postgresql.git",
        f"--username={github_user}",
        f"--password={github_token}",
        "--namespace=flux-system",
    )
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]Failed to install GitHub token using Flux[/bold red]")
        print(res[1].decode("utf8"))
        exit(1)
    print(res[0].decode("utf8"))
    print(f"[green]Installed GitHub token using Flux[/green]")
    # install ingress-nginx
    env_install_ingress_nginx()
    if KEY_CHOICES_INFRA in choices:
        infra = choices[KEY_CHOICES_INFRA]
        if KEY_CHOICES_INFRA_POSTGRESQL in infra:
            print("Installing PostgreSQL using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-postgresql-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-postgresql.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install PostgreSQL git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed PostgreSQL git source using Flux[/green]")
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-postgresql",
                "--source=GitRepository/pulse8-core-env-postgresql-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install PostgreSQL using Flux[/bold red]")
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed PostgreSQL using Flux[/green]")
            print(res[0].decode("utf8"))
        if KEY_CHOICES_INFRA_KAFKA in infra:
            print("Installing Kafka (Confluent for Kubernetes) using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-kafka-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-kafka.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Kafka git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Kafka git source using Flux[/green]")
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-kafka",
                "--source=GitRepository/pulse8-core-env-kafka-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Kafka (Confluent for Kubernetes) using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(
                f"[green]Installed Kafka (Confluent for Kubernetes) using Flux[/green]"
            )
            print(res[0].decode("utf8"))
        if KEY_CHOICES_INFRA_REDIS in infra:
            print("Installing Redis using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-redis-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-redis.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Redis git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Redis git source using Flux[/green]")
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-redis",
                "--source=GitRepository/pulse8-core-env-redis-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Redis using Flux[/bold red]")
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Redis using Flux[/green]")
            print(res[0].decode("utf8"))
        if KEY_CHOICES_INFRA_EXASOL in infra:
            print("Installing Exasol using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-exasol-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-exasol.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Exasol git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Exasol git source using Flux[/green]")
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-exasol",
                "--source=GitRepository/pulse8-core-env-exasol-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Exasol using Flux[/bold red]")
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Exasol using Flux[/green]")
            print(res[0].decode("utf8"))
        if KEY_CHOICES_INFRA_MARIADB in infra:
            print("Installing MariaDB using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-mariadb-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-mariadb.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install MariaDB git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed MariaDB git source using Flux[/green]")
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-mariadb",
                "--source=GitRepository/pulse8-core-env-mariadb-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install MariaDB using Flux[/bold red]")
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed MariaDB using Flux[/green]")
            print(res[0].decode("utf8"))
        if KEY_CHOICES_INFRA_PINOT in infra:
            print("Installing Pinot using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-pinot-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-pinot.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Pinot git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Pinot git source using Flux[/green]")
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-pinot",
                "--source=GitRepository/pulse8-core-env-pinot-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Pinot using Flux[/bold red]")
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Pinot using Flux[/green]")
            print(res[0].decode("utf8"))
        if KEY_CHOICES_INFRA_TEEDY in infra:
            print("Installing Teedy using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-teedy-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-teedy.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Teedy git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Teedy git source using Flux[/green]")
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-teedy",
                "--source=GitRepository/pulse8-core-env-teedy-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Teedy using Flux[/bold red]")
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Teedy using Flux[/green]")
            print(res[0].decode("utf8"))
        if KEY_CHOICES_INFRA_KEYCLOAK in infra:
            print("Installing Keycloak using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-keycloak-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-keycloak.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Keycloak git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Keycloak git source using Flux[/green]")
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-keycloak",
                "--source=GitRepository/pulse8-core-env-keycloak-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Keycloak using Flux[/bold red]")
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Keycloak using Flux[/green]")
            print(res[0].decode("utf8"))
        if KEY_CHOICES_INFRA_SPARK in infra:
            print("Installing Apache Spark using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-spark-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-spark.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Apache Spark git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Apache Spark git source using Flux[/green]")
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-spark",
                "--source=GitRepository/pulse8-core-env-spark-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Apache Spark using Flux[/bold red]")
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Apache Spark using Flux[/green]")
            print(res[0].decode("utf8"))
        if KEY_CHOICES_INFRA_NIFI in infra:
            print("Installing Apache NiFi using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-nifi-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-nifi.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Apache NiFi git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Apache NiFi git source using Flux[/green]")
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-nifi",
                "--source=GitRepository/pulse8-core-env-nifi-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(f"[bold red]Failed to install Apache NiFi using Flux[/bold red]")
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Apache NiFi using Flux[/green]")
            print(res[0].decode("utf8"))
        if KEY_CHOICES_INFRA_AIRFLOW in infra:
            print("Installing Apache Airflow using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-airflow-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-airflow.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Apache Airflow git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Apache Airflow git source using Flux[/green]")
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-airflow",
                "--source=GitRepository/pulse8-core-env-airflow-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Apache Airflow using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Apache Airflow using Flux[/green]")
            print(res[0].decode("utf8"))
        if KEY_CHOICES_INFRA_SUPERSET in infra:
            print("Installing Apache Superset using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-superset-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-superset.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Apache Superset git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Apache Superset git source using Flux[/green]")
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-superset",
                "--source=GitRepository/pulse8-core-env-superset-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Apache Superset using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Apache Superset using Flux[/green]")
            print(res[0].decode("utf8"))
        if KEY_CHOICES_INFRA_CLOUDSERVER in infra:
            print("Installing Zenko Cloudserver (S3) using Flux...")
            args = (
                "flux",
                "create",
                "source",
                "git",
                "pulse8-core-env-cloudserver-repo",
                "--url=https://github.com/synpulse-group/pulse8-core-env-cloudserver.git",
                "--branch=main",
                "--secret-ref=github-token",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Zenko Cloudserver (S3) git source using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(
                f"[green]Installed Zenko Cloudserver (S3) git source using Flux[/green]"
            )
            print(res[0].decode("utf8"))
            args = (
                "flux",
                "create",
                "kustomization",
                "pulse8-core-env-cloudserver",
                "--source=GitRepository/pulse8-core-env-cloudserver-repo",
                "--interval=1m",
                "--prune=true",
                "--target-namespace=default",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]Failed to install Zenko Cloudserver (S3) using Flux[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            print(f"[green]Installed Zenko Cloudserver (S3) using Flux[/green]")
            print(res[0].decode("utf8"))
    if KEY_CHOICES_SERVICES in choices:
        services_core = choices[KEY_CHOICES_SERVICES]
        for service_core_key in services_core:
            install_service(service_core_key)
    if choices_old is not None:
        if KEY_CHOICES_INFRA in choices_old:
            choices_infra = choices[KEY_CHOICES_INFRA]
            choices_infra_old = choices_old[KEY_CHOICES_INFRA]
            if (
                KEY_CHOICES_INFRA_POSTGRESQL not in choices_infra
                and KEY_CHOICES_INFRA_POSTGRESQL in choices_infra_old
            ):
                print("Uninstalling PostgreSQL using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-postgresql-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall PostgreSQL git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = (
                    "flux",
                    "delete",
                    "kustomization",
                    "pulse8-core-env-postgresql",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall PostgreSQL using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(f"[green]Uninstalled PostgreSQL using Flux[/green]")
                print(res[0].decode("utf8"))
            if (
                KEY_CHOICES_INFRA_KAFKA not in choices_infra
                and KEY_CHOICES_INFRA_KAFKA in choices_infra_old
            ):
                print("Uninstalling Kafka (Confluent for Kubernetes) using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-kafka-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Kafka (Confluent for Kubernetes) git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = (
                    "flux",
                    "delete",
                    "kustomization",
                    "pulse8-core-env-kafka",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Kafka (Confluent for Kubernetes) using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(
                    f"[green]Uninstalled Kafka (Confluent for Kubernetes) using Flux[/green]"
                )
                print(res[0].decode("utf8"))
            if (
                KEY_CHOICES_INFRA_REDIS not in choices_infra
                and KEY_CHOICES_INFRA_REDIS in choices_infra_old
            ):
                print("Uninstalling Redis using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-redis-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Redis git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = (
                    "flux",
                    "delete",
                    "kustomization",
                    "pulse8-core-env-redis",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Redis using Flux[/bold red]")
                    print(res[1].decode("utf8"))
                    exit(1)
                print(f"[green]Uninstalled Redis using Flux[/green]")
                print(res[0].decode("utf8"))
            if (
                KEY_CHOICES_INFRA_EXASOL not in choices_infra
                and KEY_CHOICES_INFRA_EXASOL in choices_infra_old
            ):
                print("Uninstalling Exasol using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-exasol-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Exasol git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = (
                    "flux",
                    "delete",
                    "kustomization",
                    "pulse8-core-env-exasol",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Exasol using Flux[/bold red]")
                    print(res[1].decode("utf8"))
                    exit(1)
                print(f"[green]Uninstalled Exasol using Flux[/green]")
                print(res[0].decode("utf8"))
            if (
                KEY_CHOICES_INFRA_MARIADB not in choices_infra
                and KEY_CHOICES_INFRA_MARIADB in choices_infra_old
            ):
                print("Uninstalling MariaDB using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-mariadb-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall MariaDB git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = (
                    "flux",
                    "delete",
                    "kustomization",
                    "pulse8-core-env-mariadb",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall MariaDB using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(f"[green]Uninstalled MariaDB using Flux[/green]")
                print(res[0].decode("utf8"))
            if (
                KEY_CHOICES_INFRA_PINOT not in choices_infra
                and KEY_CHOICES_INFRA_PINOT in choices_infra_old
            ):
                print("Uninstalling Pinot using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-pinot-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Pinot git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = (
                    "flux",
                    "delete",
                    "kustomization",
                    "pulse8-core-env-pinot",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Pinot using Flux[/bold red]")
                    print(res[1].decode("utf8"))
                    exit(1)
                print(f"[green]Uninstalled Pinot using Flux[/green]")
                print(res[0].decode("utf8"))
            if (
                KEY_CHOICES_INFRA_TEEDY not in choices_infra
                and KEY_CHOICES_INFRA_TEEDY in choices_infra_old
            ):
                print("Uninstalling Teedy using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-teedy-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Teedy git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = (
                    "flux",
                    "delete",
                    "kustomization",
                    "pulse8-core-env-teedy",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(f"[bold red]Failed to uninstall Teedy using Flux[/bold red]")
                    print(res[1].decode("utf8"))
                    exit(1)
                print(f"[green]Uninstalled Teedy using Flux[/green]")
                print(res[0].decode("utf8"))
            if (
                KEY_CHOICES_INFRA_KEYCLOAK not in choices_infra
                and KEY_CHOICES_INFRA_KEYCLOAK in choices_infra_old
            ):
                print("Uninstalling Keycloak using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-keycloak-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Keycloak git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = (
                    "flux",
                    "delete",
                    "kustomization",
                    "pulse8-core-env-keycloak",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Keycloak using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(f"[green]Uninstalled Keycloak using Flux[/green]")
                print(res[0].decode("utf8"))
            if (
                KEY_CHOICES_INFRA_SPARK not in choices_infra
                and KEY_CHOICES_INFRA_SPARK in choices_infra_old
            ):
                print("Uninstalling Apache Spark using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-spark-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Apache Spark git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = (
                    "flux",
                    "delete",
                    "kustomization",
                    "pulse8-core-env-spark",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Apache Spark using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(f"[green]Uninstalled Apache Spark using Flux[/green]")
                print(res[0].decode("utf8"))
            if (
                KEY_CHOICES_INFRA_NIFI not in choices_infra
                and KEY_CHOICES_INFRA_NIFI in choices_infra_old
            ):
                print("Uninstalling Apache NiFi using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-nifi-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Apache NiFi git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = ("flux", "delete", "kustomization", "pulse8-core-env-nifi", "-s")
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Apache NiFi using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(f"[green]Uninstalled Apache NiFi using Flux[/green]")
                print(res[0].decode("utf8"))
            if (
                KEY_CHOICES_INFRA_AIRFLOW not in choices_infra
                and KEY_CHOICES_INFRA_AIRFLOW in choices_infra_old
            ):
                print("Uninstalling Apache Airflow using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-airflow-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Apache Airflow git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = (
                    "flux",
                    "delete",
                    "kustomization",
                    "pulse8-core-env-airflow",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Apache Airflow using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(f"[green]Uninstalled Apache Airflow using Flux[/green]")
                print(res[0].decode("utf8"))
            if (
                KEY_CHOICES_INFRA_SUPERSET not in choices_infra
                and KEY_CHOICES_INFRA_SUPERSET in choices_infra_old
            ):
                print("Uninstalling Apache Superset using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-superset-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Apache Superset git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = (
                    "flux",
                    "delete",
                    "kustomization",
                    "pulse8-core-env-superset",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Apache Superset using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(f"[green]Uninstalled Apache Superset using Flux[/green]")
                print(res[0].decode("utf8"))
            if (
                KEY_CHOICES_INFRA_CLOUDSERVER not in choices_infra
                and KEY_CHOICES_INFRA_CLOUDSERVER in choices_infra_old
            ):
                print("Uninstalling Zenko Cloudserver (S3) using Flux...")
                args = (
                    "flux",
                    "delete",
                    "source",
                    "git",
                    "pulse8-core-env-cloudserver-repo",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Zenko Cloudserver (S3) git source using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(res[0].decode("utf8"))
                args = (
                    "flux",
                    "delete",
                    "kustomization",
                    "pulse8-core-env-cloudserver",
                    "-s",
                )
                pipe = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                res: tuple[bytes, bytes] = pipe.communicate()
                if pipe.returncode == 1:
                    print(
                        f"[bold red]Failed to uninstall Zenko Cloudserver (S3) using Flux[/bold red]"
                    )
                    print(res[1].decode("utf8"))
                    exit(1)
                print(f"[green]Uninstalled Zenko Cloudserver (S3) using Flux[/green]")
                print(res[0].decode("utf8"))
        if KEY_CHOICES_SERVICES in choices_old:
            choices_services_core = choices[KEY_CHOICES_SERVICES]
            choices_services_core_old = choices_old[KEY_CHOICES_SERVICES]
            for service_core_old_key in choices_services_core_old:
                if (
                    service_core_old_key not in choices_services_core
                    and not choices_services_core_old[service_core_old_key]["suspend"]
                ):
                    uninstall_service(service_core_old_key)


def env_list():
    args = ("k3d", "cluster", "list")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode("utf8"))


def env_switch(identifier: str):
    stop_all_env()
    print(f"[bold]starting target environment (id: {identifier})...[/bold]")
    args = ("k3d", "cluster", "start", f"{identifier}")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode("utf8"))
    print(
        f"[green]switching to target environment context in kubeconfig (id: {identifier})...[/green]"
    )
    args = ("kubectl", "config", "use-context", f"k3d-{identifier}")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode("utf8"))


def env_delete(identifier: str):
    print(f"[bold red]deleting the environment (id: {identifier})...[/bold red]")
    args = ("k3d", "cluster", "delete", f"{identifier}")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode("utf8"))
    delete_env_setup(identifier)


def get_questions(
    preselection_infra: list[str] = None, preselection_services_core: list[str] = None
) -> list[Checkbox]:
    if preselection_infra is None:
        preselection_infra = [KEY_CHOICES_INFRA_POSTGRESQL, KEY_CHOICES_INFRA_KAFKA]
    if preselection_services_core is None:
        preselection_services_core = [KEY_CHOICES_SERVICES_IAM]
    if is_cpu_arm():
        choices_infra = [
            ("PostgreSQL", KEY_CHOICES_INFRA_POSTGRESQL),
            ("Kafka (Confluent for Kubernetes)", KEY_CHOICES_INFRA_KAFKA),
            ("Redis", KEY_CHOICES_INFRA_REDIS),
            # not supported on arm64 - maybe bring proxy solution in place
            # ("Exasol", KEY_CHOICES_INFRA_EXASOL),
            ("MariaDB", KEY_CHOICES_INFRA_MARIADB),
            ("Pinot", KEY_CHOICES_INFRA_PINOT),
            ("Teedy", KEY_CHOICES_INFRA_TEEDY),
            ("Keycloak", KEY_CHOICES_INFRA_KEYCLOAK),
            ("Apache Spark", KEY_CHOICES_INFRA_SPARK),
            ("Apache NiFi", KEY_CHOICES_INFRA_NIFI),
            ("Apache Airflow", KEY_CHOICES_INFRA_AIRFLOW),
            ("Apache Superset", KEY_CHOICES_INFRA_SUPERSET),
            ("Zenko Cloudserver (S3)", KEY_CHOICES_INFRA_CLOUDSERVER),
        ]
    else:
        choices_infra = [
            ("PostgreSQL", KEY_CHOICES_INFRA_POSTGRESQL),
            ("Kafka (Confluent for Kubernetes)", KEY_CHOICES_INFRA_KAFKA),
            ("Redis", KEY_CHOICES_INFRA_REDIS),
            ("Exasol", KEY_CHOICES_INFRA_EXASOL),
            ("MariaDB", KEY_CHOICES_INFRA_MARIADB),
            ("Pinot", KEY_CHOICES_INFRA_PINOT),
            ("Teedy", KEY_CHOICES_INFRA_TEEDY),
            ("Keycloak", KEY_CHOICES_INFRA_KEYCLOAK),
            ("Apache Spark", KEY_CHOICES_INFRA_SPARK),
            ("Apache NiFi", KEY_CHOICES_INFRA_NIFI),
            ("Apache Airflow", KEY_CHOICES_INFRA_AIRFLOW),
            ("Apache Superset", KEY_CHOICES_INFRA_SUPERSET),
            ("Zenko Cloudserver (S3)", KEY_CHOICES_INFRA_CLOUDSERVER),
        ]
    questions = [
        inquirer.Checkbox(
            name=KEY_CHOICES_INFRA,
            message="Which infrastructure do you need?",
            choices=choices_infra,
            default=preselection_infra,
        ),
        inquirer.Checkbox(
            name=KEY_CHOICES_SERVICES,
            message="Which Pulse8 Core services do you need?",
            choices=[
                KEY_CHOICES_SERVICES_IAM,
                KEY_CHOICES_SERVICES_NOTIFICATION_ENGINE,
                KEY_CHOICES_SERVICES_QUERY_ENGINE,
                KEY_CHOICES_SERVICES_WORKFLOW_ENGINE,
                KEY_CHOICES_SERVICES_DOCUMENT_MANAGEMENT,
                KEY_CHOICES_SERVICES_ACCESS_CONTROL,
            ],
            default=preselection_services_core,
        ),
    ]
    return questions


def get_choices_from_env(identifier: str) -> (dict, dict):
    (choices_fs, choices_configmap) = read_env_setup(identifier, file_only=True)
    (preselection_infra, preselection_services) = get_preselection_from_setup(
        choices_fs
    )
    choices = dict()
    choices[KEY_CHOICES_INFRA] = preselection_infra
    choices[KEY_CHOICES_SERVICES] = preselection_services
    print(choices)
    return choices, choices_fs["services"]


def get_choices_from_file(path: str) -> (dict, dict):
    path_obj = Path(path)
    if path_obj.exists():
        choices_fs = read_env_setup_from_path(path_obj)
        (preselection_infra, preselection_services) = get_preselection_from_setup(
            choices_fs
        )
        choices = dict()
        choices[KEY_CHOICES_INFRA] = preselection_infra
        choices[KEY_CHOICES_SERVICES] = preselection_services
        return choices, choices_fs["services"]
    else:
        print(f"[red]{path} does not exist![/red]")
        exit(1)


def get_preselection_from_setup(setup: dict) -> (list, list):
    preselection_infra = []
    preselection_services = []
    if setup is not None:
        if KEY_CHOICES_INFRA in setup:
            choices_infra = setup[KEY_CHOICES_INFRA]
            if KEY_CHOICES_INFRA_POSTGRESQL in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_POSTGRESQL)
            if KEY_CHOICES_INFRA_REDIS in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_REDIS)
            if KEY_CHOICES_INFRA_KAFKA in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_KAFKA)
            if KEY_CHOICES_INFRA_EXASOL in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_EXASOL)
            if KEY_CHOICES_INFRA_MARIADB in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_MARIADB)
            if KEY_CHOICES_INFRA_PINOT in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_PINOT)
            if KEY_CHOICES_INFRA_TEEDY in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_TEEDY)
            if KEY_CHOICES_INFRA_KEYCLOAK in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_KEYCLOAK)
            if KEY_CHOICES_INFRA_SPARK in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_SPARK)
            if KEY_CHOICES_INFRA_NIFI in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_NIFI)
            if KEY_CHOICES_INFRA_AIRFLOW in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_AIRFLOW)
            if KEY_CHOICES_INFRA_SUPERSET in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_SUPERSET)
            if KEY_CHOICES_INFRA_CLOUDSERVER in choices_infra:
                preselection_infra.append(KEY_CHOICES_INFRA_CLOUDSERVER)
        if KEY_CHOICES_SERVICES in setup:
            choices_services = setup[KEY_CHOICES_SERVICES]
            if (
                KEY_CHOICES_SERVICES_NOTIFICATION_ENGINE in choices_services
                and not choices_services[KEY_CHOICES_SERVICES_NOTIFICATION_ENGINE][
                    "suspend"
                ]
            ):
                preselection_services.append(KEY_CHOICES_SERVICES_NOTIFICATION_ENGINE)
            if (
                KEY_CHOICES_SERVICES_IAM in choices_services
                and not choices_services[KEY_CHOICES_SERVICES_IAM]["suspend"]
            ):
                preselection_services.append(KEY_CHOICES_SERVICES_IAM)
            if (
                KEY_CHOICES_SERVICES_WORKFLOW_ENGINE in choices_services
                and not choices_services[KEY_CHOICES_SERVICES_WORKFLOW_ENGINE][
                    "suspend"
                ]
            ):
                preselection_services.append(KEY_CHOICES_SERVICES_WORKFLOW_ENGINE)
            if (
                KEY_CHOICES_SERVICES_QUERY_ENGINE in choices_services
                and not choices_services[KEY_CHOICES_SERVICES_QUERY_ENGINE]["suspend"]
            ):
                preselection_services.append(KEY_CHOICES_SERVICES_QUERY_ENGINE)
    return preselection_infra, preselection_services


def update_infra_choices_with_deps(choices: dict) -> None:
    needed_infrastructure = choices[KEY_CHOICES_INFRA]
    for infra in choices[KEY_CHOICES_INFRA]:
        if infra in INFRA_DEPENDENCIES_INFRA:
            needed_infrastructure_for_infra = INFRA_DEPENDENCIES_INFRA[infra]
            needed_infrastructure = (
                needed_infrastructure + needed_infrastructure_for_infra
            )
    for service in choices[KEY_CHOICES_SERVICES]:
        if service in SERVICES_DEPENDENCIES_INFRA:
            needed_infrastructure_for_service = SERVICES_DEPENDENCIES_INFRA[service]
            needed_infrastructure = (
                needed_infrastructure + needed_infrastructure_for_service
            )
    needed_infrastructure = list(set(needed_infrastructure))
    choices[KEY_CHOICES_INFRA] = needed_infrastructure


def update_service_choices_with_deps(choices: dict) -> None:
    needed_services = choices[KEY_CHOICES_SERVICES]
    for service in choices[KEY_CHOICES_SERVICES]:
        if service in SERVICES_DEPENDENCIES_SERVICES:
            needed_services_core_for_service = SERVICES_DEPENDENCIES_SERVICES[service]
            needed_services = needed_services + needed_services_core_for_service
    needed_services = list(set(needed_services))
    choices[KEY_CHOICES_SERVICES] = needed_services
    update_infra_choices_with_deps(choices)


def install_service(service_key: str, services=SERVICES) -> None:
    print(f"Installing {services[service_key]['name']} ({service_key}) using Flux...")
    args = (
        "flux",
        "create",
        "source",
        "git",
        f"{service_key}-repo",
        f"--url={services[service_key]['repository']}",
        "--secret-ref=github-token",
    )
    if services[service_key]["branch"] is not None:
        args = args + (f"--branch={services[service_key]['branch']}",)
    if services[service_key]["ref-name"] is not None:
        args = args + (f"--ref-name={services[service_key]['ref-name']}",)
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(
            f"[bold red]Failed to install {services[service_key]['name']} ({service_key}) git source using Flux"
            f"[/bold red]"
        )
        print(res[1].decode("utf8"))
        exit(1)
    print(res[0].decode("utf8"))
    print(
        f"[green]Installed {services[service_key]['name']} ({service_key}) git source using Flux[/green]"
    )
    args = (
        "flux",
        "create",
        "kustomization",
        f"{service_key}",
        f"--source=GitRepository/{service_key}-repo",
        "--interval=1m",
        "--prune=true",
        "--path=k8s",
        "--target-namespace=default",
        "--wait=false",
        "--health-check-timeout=30s",
    )
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(
            f"[bold red]Failed to install {services[service_key]['name']} ({service_key}) using Flux"
            f"[/bold red]"
        )
        print(res[1].decode("utf8"))
        exit(1)
    print(res[0].decode("utf8"))
    print(
        f"[green]Installed {services[service_key]['name']} ({service_key}) using Flux[/green]"
    )


def uninstall_service(service_key: str, services=SERVICES) -> None:
    print(f"Uninstalling {services[service_key]['name']} ({service_key}) using Flux...")
    args = ("flux", "delete", "source", "git", f"{service_key}-repo", "-s")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(
            f"[bold red]Failed to uninstall {services[service_key]['name']} ({service_key}) git source using Flux"
            f"[/bold red]"
        )
        print(res[1].decode("utf8"))
        exit(1)
    print(res[0].decode("utf8"))
    print(
        f"[green]Uninstalled {services[service_key]['name']} ({service_key}) git source using Flux[/green]"
    )
    args = ("flux", "delete", "kustomization", f"{service_key}", "-s")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res: tuple[bytes, bytes] = pipe.communicate()
    if pipe.returncode == 1:
        print(
            f"[bold red]Failed to uninstall {services[service_key]['name']} ({service_key}) using Flux[/bold red]"
        )
        print(res[1].decode("utf8"))
        exit(1)
    print(res[0].decode("utf8"))
    print(
        f"[green]Uninstalled {services[service_key]['name']} ({service_key}) using Flux[/green]"
    )


def stop_all_env() -> None:
    print(f"[bold]stopping all running environments...[/bold]")
    args = ("k3d", "cluster", "stop", "--all")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode("utf8"))


def create_certificates() -> None:
    print("creating certificates...")
    key_path = get_certificates_dir_path().joinpath("key.pem")
    cert_path = get_certificates_dir_path().joinpath("cert.pem")
    if cert_path.exists() and key_path.exists():
        print("[green]certificates already exist[/green]")
    else:
        args = ("mkcert", "--install")
        pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res: tuple[bytes, bytes] = pipe.communicate()
        if pipe.returncode == 1:
            print(res[1].decode("utf8"))
            exit(1)
        print(res[0].decode("utf8"))
        args = (
            "mkcert",
            "-key-file",
            key_path,
            "-cert-file",
            cert_path,
            "local.synpulse8.com",
            "*.local.synpulse8.com",
            "pulse8.localhost",
            "*.pulse8.localhost",
            "localhost",
            "127.0.0.1",
            "::1",
        )
        pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res: tuple[bytes, bytes] = pipe.communicate()
        if pipe.returncode == 1:
            print(res[1].decode("utf8"))
            exit(1)
        print(res[0].decode("utf8"))
        print("[green]certificates created[/green]")


def store_env_setup(identifier: str, choices: dict, services=SERVICES) -> bool:
    print(f"Storing environment setup ({identifier})")
    env_setup = dict()
    env_setup["name"] = identifier
    env_setup["infra"] = choices["infra"]
    env_setup["services"] = dict()
    for service_key in services:
        env_setup["services"][service_key] = services[service_key]
        if service_key in choices["services"]:
            env_setup["services"][service_key]["suspend"] = False
        else:
            env_setup["services"][service_key]["suspend"] = True
    try:
        env_file_path = get_environments_dir_path().joinpath(f"{identifier}.yaml")
        with open(env_file_path, "w") as env_file:
            env_file.write(yaml.dump(env_setup))
        print(f"saving choices into configmap pulse8-core-cli-config...")
        os.system(
            "kubectl delete configmap pulse8-core-cli-config --ignore-not-found=true"
        )
        args = (
            "kubectl",
            "create",
            "configmap",
            "pulse8-core-cli-config",
            f"--from-file={env_file_path}",
        )
        pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res: tuple[bytes, bytes] = pipe.communicate()
        if pipe.returncode == 1:
            print(
                f"[bold red]failed to save into configmap pulse8-core-cli-config[/bold red]"
            )
            print(res[1].decode("utf8"))
            exit(1)
        print(f"[green]saved choices into configmap pulse8-core-cli-config[/green]")
        print(res[0].decode("utf8"))
        print(
            f"[italic]Hint: You can edit your environment setup using the configmap pulse8-core-cli-config.[/italic]"
        )
        print(
            f"[italic]Hint: You must not edit the environment setup stored under {env_file_path}![/italic]"
        )
        return True
    except OSError:
        return False


def read_env_setup(identifier: str, file_only: bool = False) -> (dict, dict | None):
    print(f"Reading environment setup ({identifier})")
    try:
        env_file_path = get_environments_dir_path().joinpath(f"{identifier}.yaml")
        env_setup_fs: dict
        with open(env_file_path, "r") as env_file:
            env_setup_raw = env_file.read()
            env_setup_fs = yaml.load(env_setup_raw, yaml.Loader)
        if not file_only:
            args = (
                "kubectl",
                "--namespace",
                "default",
                "get",
                "configmap",
                "pulse8-core-cli-config",
                "-o",
                "yaml",
            )
            pipe = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            res: tuple[bytes, bytes] = pipe.communicate()
            if pipe.returncode == 1:
                print(
                    f"[bold red]failed collecting information - previous configuration from configmap[/bold red]"
                )
                print(res[1].decode("utf8"))
                exit(1)
            configmap_raw = res[0].decode("utf8")
            configmap = yaml.load(configmap_raw, yaml.Loader)
            env_setup_configmap = yaml.load(
                configmap["data"][f"{identifier}.yaml"], yaml.Loader
            )
        else:
            env_setup_configmap = None
        return env_setup_fs, env_setup_configmap
    except OSError:
        raise OSError


def read_env_setup_from_path(path: Path) -> dict:
    print(f"Reading environment setup from ({path})")
    try:
        env_setup_fs: dict
        with open(path, "r") as env_file:
            env_setup_raw = env_file.read()
            env_setup_fs = yaml.load(env_setup_raw, yaml.Loader)
        return env_setup_fs
    except OSError:
        raise OSError


def delete_env_setup(identifier: str) -> bool:
    print(f"Removing environment setup ({identifier})")
    try:
        env_file_path = get_environments_dir_path().joinpath(f"{identifier}.yaml")
        os.remove(env_file_path)
        print(f"Removed environment setup ({identifier})")
        return True
    except (OSError, FileNotFoundError) as e:
        print(e)
        print(f"[red]Failed to remove environment setup ({identifier})[/red]")
        return False


def env_check_and_update_deps(choices: dict):
    # update choices using dependencies
    print(f"Making sure infrastructure dependencies are selected...")
    update_infra_choices_with_deps(choices)
    print(f"Making sure service dependencies are selected...")
    update_service_choices_with_deps(choices)
