import yaml
from pathlib import Path

from .base.service import render_service_manifest
from .base.deployment import render_deployment_manifest
from .base.ingress import render_ingress_manifest
from .base.kustomization import render_base_kustomization_yaml

class DeploymentManifests:
    def __init__(self,
                 name,
                 image,
                 imagePullSecrets,
                 resources,
                 port,
                 github_repo_path
                 ):
        # Defaults set at object level
        self.strategy = {
            "type": "RollingUpdate"
        }
        self.imagePullPolicy = "Always"
        self.replicas = 1
        
        # Set from initialization
        self.name = name
        self.image = image
        self.imagePullSecrets = imagePullSecrets
        self.port = port
        self.resources = resources
        self.github_repo_path = github_repo_path
        
    def build_service_manifest(self):
        return render_service_manifest(
            name=self.name,
            port=self.port,
        )
    
    def build_deployment_manifest(self):
        return render_deployment_manifest(
            name=self.name,
            image=self.image,
            replicas=self.replicas,
            strategy=self.strategy,
            imagePullSecrets=self.imagePullSecrets,
            imagePullPolicy=self.imagePullPolicy,
            resources=self.resources,
            port=self.port,
        )

    def build_ingress_manifest(self):
        return render_ingress_manifest(
            name=self.name,
            port=self.port,
        )

    def build_kustomization_manifest(self):
        return render_base_kustomization_yaml(
            name=self.name,
            github_repo_path=self.github_repo_path,
        )

    def build_all_base(self):
        return [
            self.build_service_manifest(),
            self.build_deployment_manifest(),
            self.build_ingress_manifest(),
            self.build_kustomization_manifest(),
        ]

    def dump_base_layer(self, target_dir):
        target_dir = target_dir.joinpath("base")
        target_dir.mkdir(parents=True, exist_ok=True)
        for manifest in self.build_all_base():
            print(f"writing {manifest['kind']}")
            with open(target_dir / f"{manifest['kind'].lower()}.yaml", "w") as stream:
                yaml.dump(manifest, stream)