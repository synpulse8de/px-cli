import typer

from pulse8_core_cli.environment import module as environment_module
from pulse8_core_cli.auth import module as auth_module
from pulse8_core_cli.backend import module as backend_module
from pulse8_core_cli.backend_fastapi import module as backend_fastapi_module
from pulse8_core_cli.backend_shared_lib import module as backend_shared_lib_module
from pulse8_core_cli.frontend import module as frontend_module
from pulse8_core_cli.frontend_angular import module as frontend_angular_module
from pulse8_core_cli.frontend_shared_lib import module as frontend_shared_lib_module
from pulse8_core_cli.utils import module as utils_module

pulse8_cli = typer.Typer(no_args_is_help=True)


pulse8_cli.add_typer(
    auth_module.app,
    name="auth",
    help="Manage Authentication (Synpulse8 infrastructure)",
    no_args_is_help=True,
)

pulse8_cli.add_typer(
    backend_module.app,
    name="backend",
    help="Manage Pulse8 Spring Boot backends",
    no_args_is_help=True,
)

pulse8_cli.add_typer(
    backend_fastapi_module.app,
    name="backend-fastapi",
    help="Manage Pulse8 FastAPI backends",
    no_args_is_help=True,
)

pulse8_cli.add_typer(
    backend_shared_lib_module.app,
    name="backend-shared-lib",
    help="Manage Pulse8 Java backend shared libs",
    no_args_is_help=True,
)

pulse8_cli.add_typer(
    environment_module.app,
    name="environment",
    help="Manage Pulse8 environments",
    no_args_is_help=True,
)

pulse8_cli.add_typer(
    frontend_module.app,
    name="frontend",
    help="Manage Pulse8 NextJS frontends",
    no_args_is_help=True,
)

pulse8_cli.add_typer(
    frontend_angular_module.app,
    name="frontend-angular",
    help="Manage Pulse8 Angular frontends",
    no_args_is_help=True,
)

pulse8_cli.add_typer(
    frontend_shared_lib_module.app,
    name="frontend-shared-lib",
    help="Manage Pulse8 React frontend shared libs",
    no_args_is_help=True,
)

pulse8_cli.add_typer(
    utils_module.app,
    name="utils",
    help="Pulse8 utility commands",
    no_args_is_help=True,
)


if __name__ == "__main__":
    pulse8_cli()
