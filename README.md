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
  - apt (Linux Debian-based)

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

### Windows [WIP]
1. Install pipx
2. Install Poetry
3. Install k3d
4. Install devspace `npm install -g devspace`
5. Install pnpm `npm install -g pnpm`
6. Install kubectl
7. Install helm
8. Install flux

### Ubuntu [WIP]
1. Install pipx
2. Install Poetry
3. Install k3d
4. Install devspace `npm install -g devspace`
5. Install pnpm `npm install -g pnpm`
6. Install kubectl
7. Install helm
8. Install flux


## 🛠 Installation & Set Up

- Clone the project, install, install tools, build, install for user & use

```bash
git clone https://github.com/synpulse-group/pulse8-core-cli.git
cd pulse8-core-cli
poetry install
poetry build
pip install --user ./dist/pulse8_core_cli-0.1.0-py3-none-any.whl
```

Hint: `pip install --user ./dist/pulse8_core_cli-0.1.0-py3-none-any.whl --force-reinstall` if you want to proper reinstall after changes

## 💾 Ansible provided tools

- k3d
- devspace
- pnpm
- kubectl
- helm
- flux
