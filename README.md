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
