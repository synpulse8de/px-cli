import typer

from pulsex_core_cli.auth import module as auth_module
from pulsex_core_cli.backend import module as backend_module
from pulsex_core_cli.backend_shared_lib import module as backend_shared_lib_module
from pulsex_core_cli.frontend_angular import module as frontend_angular_module
from pulsex_core_cli.frontend_shared_lib import module as frontend_shared_lib_module
from pulsex_core_cli.utils import module as utils_module

pulseX_cli = typer.Typer(no_args_is_help=True)


pulseX_cli.add_typer(
    auth_module.app,
    name="auth",
    help="Manage Authentication (SynpulseX infrastructure)",
    no_args_is_help=True,
)

pulseX_cli.add_typer(
    backend_module.app,
    name="backend",
    help="Manage PulseX Spring Boot backends",
    no_args_is_help=True,
)

pulseX_cli.add_typer(
    backend_shared_lib_module.app,
    name="backend-shared-lib",
    help="Manage PulseX Java backend shared libs",
    no_args_is_help=True,
)


pulseX_cli.add_typer(
    frontend_angular_module.app,
    name="frontend-angular",
    help="Manage PulseX Angular frontends",
    no_args_is_help=True,
)

pulseX_cli.add_typer(
    frontend_shared_lib_module.app,
    name="frontend-shared-lib",
    help="Manage PulseX React frontend shared libs",
    no_args_is_help=True,
)

pulseX_cli.add_typer(
    utils_module.app,
    name="utils",
    help="PulseX utility commands",
    no_args_is_help=True,
)


if __name__ == "__main__":
    pulseX_cli()
