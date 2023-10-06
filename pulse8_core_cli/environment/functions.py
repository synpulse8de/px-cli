import subprocess


def env_create(identifier: str):
    print(f"[bold green]starting a environment (id: {identifier})...[/bold green]")
    args = (f"k3d cluster create {identifier}")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    popen.wait()
    output = popen.stdout.read()
    print(output.decode('ascii'))


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
