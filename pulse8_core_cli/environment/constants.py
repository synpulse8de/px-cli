KEY_CHOICES_INFRA = "infra"
KEY_CHOICES_INFRA_POSTGRESQL = "postgresql"
KEY_CHOICES_INFRA_KAFKA = "kafka"
KEY_CHOICES_INFRA_REDIS = "redis"
KEY_CHOICES_INFRA_EXASOL = "exasol"
KEY_CHOICES_INFRA_TEEDY = "teedy"
KEY_CHOICES_SERVICES_CORE = "services-core"
KEY_CHOICES_SERVICES_CORE_IAM = "pulse8-core-iam"
KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE = "pulse8-core-notfication-engine"
KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE = "pulse8-core-query-engine"
KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE = "pulse8-core-workflow-engine"

SERVICES = {
    KEY_CHOICES_SERVICES_CORE_IAM: ("Pulse8 Core Identity & Access Management", "https://github.com/synpulse-group/"
                                                                                "pulse8-core-iam.git"),
    KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE: ("Pulse8 Core Notification Engine", "https://github.com/synpulse"
                                                                                       "-group/pulse8-core"
                                                                                       "-notification-engine.git"),
    KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE: ("Pulse8 Core Query Engine", "https://github.com/synpulse-group/pulse8"
                                                                         "-core-backend-queryengine.git"),
    KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE: ("Pulse8 Core Workflow Engine", "https://github.com/synpulse-group"
                                                                               "/pulse8-core-workflow-engine.git")
}

SERVICES_DEPENDENCIES_INFRA = {
    KEY_CHOICES_SERVICES_CORE_IAM: [KEY_CHOICES_INFRA_POSTGRESQL, KEY_CHOICES_INFRA_KAFKA],
    KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE: [],
    KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE: [KEY_CHOICES_INFRA_POSTGRESQL],
    KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE: []
}

SERVICES_DEPENDENCIES_SERVICES = {
    KEY_CHOICES_SERVICES_CORE_IAM: [KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE,
                                    KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE],
    KEY_CHOICES_SERVICES_CORE_NOTIFICATION_ENGINE: [],
    KEY_CHOICES_SERVICES_CORE_QUERY_ENGINE: [],
    KEY_CHOICES_SERVICES_CORE_WORKFLOW_ENGINE: []
}
