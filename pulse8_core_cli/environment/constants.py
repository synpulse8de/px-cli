KEY_CHOICES_INFRA = "infra"
KEY_CHOICES_INFRA_POSTGRESQL = "postgresql"
KEY_CHOICES_INFRA_KAFKA = "kafka"
KEY_CHOICES_INFRA_REDIS = "redis"
KEY_CHOICES_INFRA_EXASOL = "exasol"
KEY_CHOICES_INFRA_MARIADB = "mariadb"
KEY_CHOICES_INFRA_TEEDY = "teedy"
KEY_CHOICES_INFRA_KEYCLOAK = "keycloak"
KEY_CHOICES_INFRA_SPARK = "spark"
KEY_CHOICES_INFRA_NIFI = "nifi"
KEY_CHOICES_INFRA_CLOUDSERVER = "cloudserver"
KEY_CHOICES_SERVICES = "services"
KEY_CHOICES_SERVICES_IAM = "pulse8-core-iam"
KEY_CHOICES_SERVICES_NOTIFICATION_ENGINE = "pulse8-core-notification-engine"
KEY_CHOICES_SERVICES_QUERY_ENGINE = "pulse8-core-query-engine"
KEY_CHOICES_SERVICES_WORKFLOW_ENGINE = "pulse8-core-workflow-engine"
KEY_CHOICES_SERVICES_DOCUMENT_MANAGEMENT = "pulse8-core-document-management"

SERVICES = {
    KEY_CHOICES_SERVICES_IAM: {
        "name": "Pulse8 Core Identity & Access Management",
        "repository": "https://github.com/synpulse-group/pulse8-core-iam.git",
        "branch": "develop",
        "ref-name": None,
        "suspend": False,
    },
    KEY_CHOICES_SERVICES_NOTIFICATION_ENGINE: {
        "name": "Pulse8 Core Notification Engine",
        "repository": "https://github.com/synpulse-group/pulse8-core-notification-engine.git",
        "branch": "develop",
        "ref-name": None,
        "suspend": False,
    },
    KEY_CHOICES_SERVICES_QUERY_ENGINE: {
        "name": "Pulse8 Core Query Engine",
        "repository": "https://github.com/synpulse-group/pulse8-core-backend-queryengine.git",
        "branch": "main",
        "ref-name": None,
        "suspend": False,
    },
    KEY_CHOICES_SERVICES_WORKFLOW_ENGINE: {
        "name": "Pulse8 Core Workflow Engine",
        "repository": "https://github.com/synpulse-group/pulse8-core-workflow-engine.git",
        "branch": "develop",
        "ref-name": None,
        "suspend": False,
    },
    KEY_CHOICES_SERVICES_DOCUMENT_MANAGEMENT: {
        "name": "Pulse8 Core Document Management",
        "repository": "https://github.com/synpulse-group/pulse8-core-document-management.git",
        "branch": "main",
        "ref-name": None,
        "suspend": False,
    },
}

INFRA_DEPENDENCIES_INFRA = {
    KEY_CHOICES_INFRA_KEYCLOAK: [
        KEY_CHOICES_INFRA_POSTGRESQL,
    ],
    KEY_CHOICES_INFRA_SPARK: [
        KEY_CHOICES_INFRA_CLOUDSERVER,
    ]
}

SERVICES_DEPENDENCIES_INFRA = {
    KEY_CHOICES_SERVICES_IAM: [
        KEY_CHOICES_INFRA_KEYCLOAK,
        KEY_CHOICES_INFRA_POSTGRESQL,
        KEY_CHOICES_INFRA_KAFKA,
    ],
    KEY_CHOICES_SERVICES_NOTIFICATION_ENGINE: [KEY_CHOICES_INFRA_KAFKA],
    KEY_CHOICES_SERVICES_QUERY_ENGINE: [
        KEY_CHOICES_INFRA_POSTGRESQL,
        KEY_CHOICES_INFRA_MARIADB,
    ],
    KEY_CHOICES_SERVICES_WORKFLOW_ENGINE: [
        KEY_CHOICES_INFRA_POSTGRESQL,
        KEY_CHOICES_INFRA_KAFKA,
    ],
    KEY_CHOICES_SERVICES_DOCUMENT_MANAGEMENT: [KEY_CHOICES_INFRA_POSTGRESQL],
}

SERVICES_DEPENDENCIES_SERVICES = {
    KEY_CHOICES_SERVICES_IAM: [
        KEY_CHOICES_SERVICES_NOTIFICATION_ENGINE,
        KEY_CHOICES_SERVICES_WORKFLOW_ENGINE,
    ],
    KEY_CHOICES_SERVICES_NOTIFICATION_ENGINE: [],
    KEY_CHOICES_SERVICES_QUERY_ENGINE: [],
    KEY_CHOICES_SERVICES_WORKFLOW_ENGINE: [],
}
