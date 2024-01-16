def render_service_manifest(name, port):
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": name},
        "spec": {
            "ports": [
                {
                    "port": port,
                    "targetPort": port,
                    "protocol": "TCP",
                    "name": "service-port",
                }
            ],
        },
    }
