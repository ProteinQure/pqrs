import typer
import plumbum
from datafiles import datafile
from plumbum.cmd import git
from plumbum import local, FG, BG

from pqrs.selector import run_selector


PQRS_LOCATION = local.env.home / '.pqrss'

app = typer.Typer(add_completion=False)

@datafile(str(PQRS_LOCATION / "pqrs.yml"))
class Config:
    channels: dict[str, str] = None
    roles: dict[str, list[str]] = None


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

    galaxy = local["ansible-galaxy"]
    result = galaxy["collection", "install", "--force", url].run()
    namespace, collection = result[1].splitlines()[-1].split()[0].split('.')

    config = Config.objects.get_or_create()
    config.channels[f"{namespace}.{collection}"] = url
    config.roles[f"{namespace}.{collection}"] = None


@app.command()
def configure():
    """
    Select which roles you want to install.
    """

    data = {
        'basic': ["All the usual stuff"],
        'cli-vim': ["Vim goodies"],
        'cli-bash': ["You should probably install this", "also configures history"],
    }

    config = Config.objects.get_or_create()
    config.roles["pq.config"] = run_selector(data)


def run():
    app()
