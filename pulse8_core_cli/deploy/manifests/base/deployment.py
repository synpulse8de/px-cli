def render_deployment_manifest(
    name, image, replicas, strategy, imagePullSecrets, imagePullPolicy, resources, port
):
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name},
        "spec": {
            "replicas": replicas,
            "strategy": strategy,
            "template": {
                "spec": {
                    "imagePullSecrets": imagePullSecrets,
                    "containers": [
                        {
                            "image": image,
                            "name": name,
                            "imagePullPolicy": imagePullPolicy,
                            "resources": resources,
                            "ports": [{"containerPort": port, "name": "service-port"}],
                            "envFrom": [
                                {"configMapRef": {"name": f"{name}-config"}},
                                {"secretRef": {"name": f"{name}-secrets"}},
                            ],
                        }
                    ],
                }
            },
        },
    }
