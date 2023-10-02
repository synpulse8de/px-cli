import typer

from pulse8_core_cli.modules import auth, backend, backend_fastapi, environment, frontend, frontend_angular

pulse8_cli = typer.Typer()


pulse8_cli.add_typer(auth.app, name="auth")

pulse8_cli.add_typer(backend.app, name="backend")
# pulse8_cli.add_typer(backend.app, name="be")
# pulse8_cli.add_typer(backend.app, name="spring")

pulse8_cli.add_typer(backend_fastapi.app, name="backend-fastapi")
# pulse8_cli.add_typer(backend_fastapi.app, name="fastapi")

pulse8_cli.add_typer(environment.app, name="environment")
# pulse8_cli.add_typer(environment.app, name="env")

pulse8_cli.add_typer(frontend.app, name="frontend")
# pulse8_cli.add_typer(frontend.app, name="fe")
# pulse8_cli.add_typer(frontend.app, name="nextjs")

pulse8_cli.add_typer(frontend_angular.app, name="frontend-angular")
# pulse8_cli.add_typer(frontend_angular.app, name="ng")


if __name__ == "__main__":
    pulse8_cli()
