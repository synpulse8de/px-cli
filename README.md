# 🚀 Pulse8 Core CLI

> This is the Command Line Interface to easy develop with the Pulse8 Core Templates and Environments

---

## ⚙️ Prerequisites 

- Runtimes
  - Python 3.11+
  - NodeJS 18.x+ (`curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash`)
  - Docker 20.10.5+
- Package manager
  - Homebrew (macOS) 
  - chocolatey (Windows) 
  - snap (Ubuntu)

---

## 🛫 Requirements installation

### macOS
1. Install pipx `brew install pipx && pipx ensurepath`
2. Install Poetry `pipx install poetry`
3. Install k3d `brew install k3d`
4. Install devspace `npm install -g devspace`
5. Install pnpm `npm install -g pnpm`
6. Install kubectl `brew install kubernetes-cli`
7. Install helm `brew install helm`
8. Install flux `brew install fluxcd/tap/flux`
9. Install GitHub CLI `brew install gh`
10. Install mkcert `brew install mkcert && brew install nss`
11. Install JFrog CLI `brew install jfrog-cli && jf intro`

### Windows
1. Install pipx `py -3 -m pip install --user pipx; py -3 -m pipx ensurepath`
2. Install Poetry `pipx install poetry`
3. Install k3d `choco install k3d`
4. Install devspace `npm install -g devspace`
5. Install pnpm `npm install -g pnpm`
6. Install kubectl `choco install kubernetes-cli`
7. Install helm `choco install kubernetes-helm`
8. Install flux `choco install flux`
9. Install GitHub CLI `choco install gh`
10. Install mkcert `choco install mkcert`
11. Install JFrog CLI `choco install jfrog-cli-v2-jf; jf intro`

### Ubuntu
1. Install pipx `python3 -m pip install --user pipx && python3 -m pipx ensurepath`
2. Install Poetry `pipx install poetry`
3. Install k3d `curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash`
4. Install devspace `npm install -g devspace`
5. Install pnpm `npm install -g pnpm`
6. Install kubectl `sudo snap install kubectl --classic`
7. Install helm `sudo snap install helm --classic`
8. Install flux `curl -s https://fluxcd.io/install.sh | sudo bash`
9. Install GitHub CLI https://github.com/cli/cli/blob/trunk/docs/install_linux.md
10. Install mkcert https://github.com/FiloSottile/mkcert#linux
11. Install JFrog CLI `wget -qO - https://releases.jfrog.io/artifactory/jfrog-gpg-public/jfrog_public_gpg.key | sudo apt-key add -
echo "deb https://releases.jfrog.io/artifactory/jfrog-debs xenial contrib" | sudo tee -a /etc/apt/sources.list &&    sudo apt update &&
sudo apt install -y jfrog-cli-v2-jf &&
jf intro`


## 🛠 Installation & Set Up

- Clone the project, install, install tools, build, install for user & use

```bash
git clone https://github.com/synpulse-group/pulse8-core-cli.git
cd pulse8-core-cli
poetry install
poetry build
pip install --user ./dist/pulse8_core_cli-0.1.0-py3-none-any.whl
```

#### Hint: 
if you want to clean reinstall after changes:

```bash
poetry build
pip install --user ./dist/pulse8_core_cli-0.1.0-py3-none-any.whl --force-reinstall
```

## 🚗 Usage

Run using the main command (for help and available commands use `--help`):
```bash
pulse8
```
Firstly you should authenticate to needed infrastructure to work with pulse8 cli commands
```bash
pulse8 auth login
```


## 😥 Troubleshooting

### Firefox `SEC_ERROR_UNKNOWN_ISSUER`
[https://github.com/FiloSottile/mkcert/issues/370](https://github.com/FiloSottile/mkcert/issues/370#issuecomment-1280377305)https://github.com/FiloSottile/mkcert/issues/370#issuecomment-1280377305

### JFrog `lock hasn't been acquired`
If you encounter timeout (freezing) during JFrog authentication and then a timeout error message "[Error] lock hasn't been acquired", please update JFrog CLI to the latest version

### GitHub `No such file or directory`
If you get "No such file or directory '.../hosts.yml" (system specific GitHub path) when running commands for templates, it can happen if you did not log in to needed infrastructure using command
```bash
pulse8 auth login
```

### command not found: pulse8
The logs state messages like these:
```
WARNING: The scripts p8 and pulse8 are installed in '<somepath>' which is not on PATH.
Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location
```
Just add the `<somepath>` from the message to your PATH.
