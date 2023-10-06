import typer

from pulse8_core_cli.environment import module as environment_module
from pulse8_core_cli.auth import module as auth_module
from pulse8_core_cli.backend import module as backend_module
from pulse8_core_cli.backend_fastapi import module as backend_fastapi_module
from pulse8_core_cli.frontend import module as frontend_module
from pulse8_core_cli.frontend_angular import module as frontend_angular_module

pulse8_cli = typer.Typer()


pulse8_cli.add_typer(auth_module.app, name="auth")

pulse8_cli.add_typer(backend_module.app, name="backend")
# pulse8_cli.add_typer(backend.app, name="be")
# pulse8_cli.add_typer(backend.app, name="spring")

pulse8_cli.add_typer(backend_fastapi_module.app, name="backend-fastapi")
# pulse8_cli.add_typer(backend_fastapi.app, name="fastapi")

pulse8_cli.add_typer(environment_module.app, name="environment")
# pulse8_cli.add_typer(environment.app, name="env")

pulse8_cli.add_typer(frontend_module.app, name="frontend")
# pulse8_cli.add_typer(frontend.app, name="fe")
# pulse8_cli.add_typer(frontend.app, name="nextjs")

pulse8_cli.add_typer(frontend_angular_module.app, name="frontend-angular")
# pulse8_cli.add_typer(frontend_angular.app, name="ng")


if __name__ == "__main__":
    pulse8_cli()
