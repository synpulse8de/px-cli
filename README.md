# 🚀 Pulse8 Core CLI

> This is the Command Line Interface to easy develop with the Pulse8 Core Templates and Environments

---

## ⚙️ Prerequisites 

- Runtimes
  - Python 3.11+
  - NodeJS (`curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash`)
- Build tools
  - Poetry (`pipx install poetry`)
  - Docker
- Package manager
  - Homebrew (macOS) 
  - chocolatey (Windows) 
  - apt (Linux Debian-based)

---

## 🛠 Installation & Set Up

- Clone the project, install, install tools, build, install for user & use

```bash
git clone https://github.com/synpulse-group/pulse8-core-cli.git
cd pulse8-core-cli
poetry install
ansible-playbook ./dev-tools-playbook.yml
poetry build
pip install --user ./dist/pulse8_core_cli-X.Y.Z-py3-none-any.whl
```

## 💾 Ansible provided tools

- k3d
- devspace
- pnpm
- kubectl
- helm
