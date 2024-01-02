import base64
import json
import os
import shutil
import subprocess
import time
import winreg
from pathlib import Path

import typer
from rich import print

from pulse8_core_cli.shared.module import validate_email, get_env_variables, ENV_JFROG_TOKEN, get_dotm2_dir_path, \
    get_dotdocker_dir_path
from pulse8_core_cli.shared.platform_discovery import is_windows


def auth_login(email: str) -> None:
    if not validate_email(email):
        print(f"[bold red]your provided email {email} should fulfill the "
              f"pattern firstname.lastname@synpulse.com or @synpulse8.com...[/bold red]")
        exit(1)

    has_synpulse_access = typer.confirm(
        "Do you have access to GitHub (github.com, fistname-lastname_SYNPULSE) & JFrog (synpulse.jfrog.io, SAML SSO) ?")
    if not has_synpulse_access:
        print("[bold red]Please request access to GitHub and JFrog to continue.[/bold red]")
        print("You can request access to GitHub here: "
              "[link=https://support.synpulse.com/support/catalog/items/79]GitHub[/link]")
        print("You can request access to JFrog here: "
              "[link=https://support.synpulse.com/support/catalog/items/102]JFrog[/link]")
        exit(1)

    adjust_windows_registry()

    print("[bold]authenticate against github.com...[bold]")
    os.system("gh auth login --insecure-storage --git-protocol=https --hostname=github.com --web")
    adjust_git_config(email)
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
    docker_config_json_path = get_dotdocker_dir_path().joinpath("config.json")
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
    env_vars = get_env_variables(silent=True)
    if not check_npmrc_ready():
        setup_npmrc(access_token, email)
    if not check_maven_ready():
        setup_maven(access_token, email)


def check_npmrc_ready() -> bool:
    npmrc_file_path = Path.home().joinpath(".npmrc")
    if not npmrc_file_path.exists():
        print("~/.npmrc does not exist")
        return False
    npmrc_raw: str
    with open(npmrc_file_path) as npmrc_file:
        npmrc_raw = npmrc_file.read()
    if "@s8:registry" in npmrc_raw:
        print("~/.npmrc @s8 is set up")
        print("[italic]Hint: if you have problems cleanup the @s8 settings from ~/.npmrc[/italic]")
        return True
    print("~/.npmrc @s8 is not set up")
    return False


def check_maven_ready() -> bool:
    maven_settings_file_path = get_dotm2_dir_path().joinpath("settings.xml")
    if not maven_settings_file_path.exists():
        print("~/.m2/settings.xml does not exist")
        return False
    maven_settings_raw: str
    with open(maven_settings_file_path) as maven_settings_file:
        maven_settings_raw = maven_settings_file.read()
    if "<url>https://synpulse.jfrog.io/artifactory/s8-libs-release</url>" in maven_settings_raw and \
            "<url>https://synpulse.jfrog.io/artifactory/s8-libs-snapshot</url>" in maven_settings_raw:
        print("~/.m2/settings.xml s8-libs-release and s8-libs-snapshot is set up")
        print("[italic]Hint: if you have problems cleanup the settings from ~/.m2/settings.xml[/italic]")
        return True
    print("~/.m2/settings.xml s8-libs-release and s8-libs-snapshot is not set up")
    return False


def setup_maven(token: str, email: str) -> None:
    print("[bold]setting up maven [italic](~/.m2/settings.xml)[/italic]...[/bold]")
    curr_time = time.time()
    maven_settings_file_path = get_dotm2_dir_path().joinpath("settings.xml")
    if maven_settings_file_path.exists():
        maven_settings_file_backup_path = get_dotm2_dir_path().joinpath(f"settings.xml.backup-{curr_time}")
        print(f"performing backup of maven settings to [italic](~/.m2/settings.xml.backup-{curr_time})[/italic]...")
        shutil.copyfile(maven_settings_file_path, maven_settings_file_backup_path)
    jfrog_snippet = f"""<?xml version="1.0" encoding="UTF-8"?>
<settings xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.2.0 http://maven.apache.org/xsd/settings-1.2.0.xsd" xmlns="http://maven.apache.org/SETTINGS/1.2.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <servers>
    <server>
      <username>{email}</username>
      <password>{token}</password>
      <id>central</id>
    </server>
    <server>
      <username>{email}</username>
      <password>{token}</password>
      <id>snapshots</id>
    </server>
  </servers>
  <profiles>
    <profile>
      <repositories>
        <repository>
          <snapshots>
            <enabled>false</enabled>
          </snapshots>
          <id>central</id>
          <name>s8-libs-release</name>
          <url>https://synpulse.jfrog.io/artifactory/s8-libs-release</url>
        </repository>
        <repository>
          <snapshots />
          <id>snapshots</id>
          <name>s8-libs-snapshot</name>
          <url>https://synpulse.jfrog.io/artifactory/s8-libs-snapshot</url>
        </repository>
      </repositories>
      <pluginRepositories>
        <pluginRepository>
          <snapshots>
            <enabled>false</enabled>
          </snapshots>
          <id>central</id>
          <name>s8-libs-release</name>
          <url>https://synpulse.jfrog.io/artifactory/s8-libs-release</url>
        </pluginRepository>
        <pluginRepository>
          <snapshots />
          <id>snapshots</id>
          <name>s8-libs-snapshot</name>
          <url>https://synpulse.jfrog.io/artifactory/s8-libs-snapshot</url>
        </pluginRepository>
      </pluginRepositories>
      <id>artifactory</id>
    </profile>
  </profiles>
  <activeProfiles>
    <activeProfile>artifactory</activeProfile>
  </activeProfiles>
</settings>"""
    with open(maven_settings_file_path, "w") as maven_settings_file:
        maven_settings_file.write(jfrog_snippet)
    print("[green]maven setup finished[/green]")


def setup_npmrc(token: str, email: str) -> None:
    print("[bold]setting up npm [italic](~/.npmrc)[/italic]...[/bold]")
    curr_time = time.time()
    npmrc_file_path = Path.home().joinpath(".npmrc")
    if npmrc_file_path.exists():
        npmrc_file_backup_path = Path.home().joinpath(f".npmrc.backup-{curr_time}")
        print(f"performing backup of npm settings to [italic](~/.npmrc.backup-{curr_time})[/italic]...")
        shutil.copyfile(npmrc_file_path, npmrc_file_backup_path)
    jfrog_snippet = f"""@s8:registry=https://synpulse.jfrog.io/artifactory/api/npm/s8-npm/
//synpulse.jfrog.io/artifactory/api/npm/s8-npm/:_auth={token}
//synpulse.jfrog.io/artifactory/api/npm/s8-npm/:username={email}
//synpulse.jfrog.io/artifactory/api/npm/s8-npm/:email={email}
//synpulse.jfrog.io/artifactory/api/npm/s8-npm/:always-auth=true"""
    with open(npmrc_file_path, "a") as npmrc_file:
        npmrc_file.write(jfrog_snippet)
    print("[green]npm setup finished[/green]")


def adjust_git_config(email: str):
    os.system("git config --global core.longpaths true")
    try:
        name = email.split("@")[0]
        name_parts = name.split(".")
        first_name = name_parts[0]
        last_name = name_parts[1]
        username = (first_name + " " + last_name).title()
        os.system('git config --global user.name "' + username + '"')
        os.system('git config --global user.email "' + email + '"')
        print("email updated in git and username for git changed to " + username)
    except Exception:
        print(f"[bold red]creation of git username from email failed, skipping...[/bold red]")


def adjust_windows_registry():
    if is_windows():
        reg_file_system_key_read = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE,
                                                    r"SYSTEM\\CurrentControlSet\\Control\\FileSystem",
                                                    0, winreg.KEY_READ)
        long_paths_value = winreg.QueryValueEx(reg_file_system_key_read, 'LongPathsEnabled')[0]
        if long_paths_value == 0:
            try:
                reg_file_system_key = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE,
                                                       r"SYSTEM\\CurrentControlSet\\Control\\FileSystem",
                                                       0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(reg_file_system_key, 'LongPathsEnabled', 0, winreg.REG_DWORD, 1)
            except PermissionError:
                print("[red]Pulse8 CLI needs to update LongPathsEnabled registry key in order "
                      "to ensure templates are correctly created. Please run your terminal as "
                      "Administrator first time to set this value. Next time you don't have to "
                      "run it as Administrator.[/red]")
                exit(1)
