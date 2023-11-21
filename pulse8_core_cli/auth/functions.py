import base64
import json
import os
import subprocess
from pathlib import Path

from rich import print

from pulse8_core_cli.shared.module import validate_email


def auth_login(email: str) -> None:
    if not validate_email(email):
        print(f"[bold red]your provided email {email} should fulfill the "
              f"pattern firstname.lastname@synpulse.com or @synpulse8.com...[/bold red]")
        exit(1)
    print("[bold]authenticate against github.com...[bold]")
    os.system("gh auth login --insecure-storage --git-protocol=https --hostname=github.com --web")
    print("[bold]authenticate against synpulse.jfrog.io...[bold]")
    print("[italic]"
          "Help: "
          "Save and continue, Web Login, No client certificate, Login in Browser using 'SAML SSO'"
          "[/italic]")
    os.system("jf config add synpulse.jfrog.io --url https://synpulse.jfrog.io --overwrite=true")
    print("creating of access token...")
    args = ("jf", "rt", "access-token-create", "--expiry", "31535999")
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = pipe.communicate()
    if pipe.returncode == 1:
        print(f"[bold red]creation of access token failed[/bold red]")
        print(stderr.decode('utf8'))
        exit(1)
    access_token_result_raw = stdout.decode('utf8')
    access_token_dict = json.loads(access_token_result_raw)
    access_token: str = access_token_dict['access_token']
    print("created access token")
    print("[italic]Hint: Token expires in one year[/italic]")
    docker_auth_raw = f"{email}:{access_token}"
    docker_auth_raw_bytes = docker_auth_raw.encode('utf8')
    docker_auth_encoded_bytes = base64.b64encode(docker_auth_raw_bytes)
    docker_auth_encoded = docker_auth_encoded_bytes.decode('utf8')
    docker_config_json_path = Path.home().joinpath(".docker").joinpath("config.json")
    with open(docker_config_json_path) as docker_config_json_file:
        docker_config_json_raw = docker_config_json_file.read()
    docker_config_json = json.loads(docker_config_json_raw)
    try:
        docker_config_json_auths = docker_config_json["auths"]
    except KeyError:
        docker_config_json["auths"] = dict()
        docker_config_json_auths = docker_config_json["auths"]
    try:
        docker_config_json_auths_spjfrog = docker_config_json_auths["synpulse.jfrog.io"]
    except KeyError:
        try:
            docker_config_json_auths_spjfrog = docker_config_json_auths["https://synpulse.jfrog.io"]
        except KeyError:
            docker_config_json_auths["synpulse.jfrog.io"] = dict()
            docker_config_json_auths_spjfrog = docker_config_json_auths["synpulse.jfrog.io"]
    docker_config_json_auths_spjfrog["auth"] = docker_auth_encoded
    docker_config_json_auths_spjfrog["email"] = email
    with open(docker_config_json_path, "w") as docker_config_json_file:
        docker_config_json_file.write(json.dumps(docker_config_json, indent=4))

