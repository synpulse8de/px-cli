def render_ingress_manifest(name, port):
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": name,
                "annotations": {
                    "kubernetes.io/tls-acme": "true",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                    "nginx.ingress.kubernetes.io/proxy-body-size": "10m"
                }
            },
            "spec": {
                "ingressClassName" : "nginx",
                "rules": [
                    {
                        "host": f"DO NOT EDIT ; will be replaced at higher layer by Flux",
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": name,
                                            "port": {
                                                "number": port
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ],
                "tls": [
                    {
                        "hosts": [
                            f"DO NOT EDIT ; will be replaced at higher layer by Flux"
                        ],
                        "secretName": f"{name}-tls"
                    }
                ]
            }
        }