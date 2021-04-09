import typer
import plumbum
from plumbum.cmd import git
from plumbum import local, FG, BG

app = typer.Typer(add_completion=False)

PQRS_LOCATION = local.env.home / '.pqrss'


@app.command()
def init():
    """
    Ensures the PQRS is ready to be used.
    """

    PQRS_LOCATION.mkdir(exist_ok=True)

    with local.cwd(PQRS_LOCATION):
        git["init"] & FG


@app.command()
def subscribe(url: str):
    """
    Subscribe to a given channel.
    """

    pass


def run():
    app()
