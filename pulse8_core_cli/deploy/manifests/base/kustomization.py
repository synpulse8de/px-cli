def render_base_kustomization_yaml(name, github_repo_path):
    return {
        "apiVersion": "kustomize.config.k8s.io/v1beta1",
        "kind": "Kustomization",
        "resources": [
            "deployment.yaml",
            "service.yaml",
            "ingress.yaml",
        ],
        "commonAnnotations": {
            "synpulse8.com/repository": github_repo_path,
        },
        "commonLabels": {
            "app": name,
        },
        "components": ["../../../../shared/jfrog-secret"],
    }
