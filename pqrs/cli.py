import itertools

import plumbum
import temppathlib
import typer

from plumbum.cmd import git
from plumbum import local, FG, BG

from pqrs import backend
from pqrs import paths
from pqrs import tui
from pqrs.config import Config


app = typer.Typer(add_completion=False)

@app.command()
def init():
    """
    Ensures the PQRS is ready to be used.
    """

    paths.PQRS_LOCATION.mkdir(exist_ok=True)

    with local.cwd(paths.PQRS_LOCATION):
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
    Select which roles you want to configure to be installed and updated by
    PQRS.
    """

    pqrs_roles = backend.discover_roles()
    config = Config.objects.get_or_create()

    # Toggle on all active roles
    active_roles = [
        role
        for collection, roles in pqrs_roles.items()
        for role in roles
        if role.name in (config.roles.get(collection) or [])
    ]
    for role in active_roles:
        role.selected = True

    # Ask user to (re)configure the roles
    for collection, roles in pqrs_roles.items():
        config.roles[collection] = [r.name for r in tui.select_roles(roles)]


@app.command()
def execute():
    """
    Select which roles you want to install.
    """

    pqrs_roles = backend.discover_roles()

    # Ask user to (re)configure the roles
    roles_to_run = {
        collection: [r.name for r in tui.select_roles(roles)]
        for collection, roles in pqrs_roles.items()
    }

    role_paths = [
        str(paths.COLLECTIONS / f"{collection.replace('.', '/')}/roles")
        for collection in roles_to_run
    ]
    role_path_args = itertools.chain(*[("--roles-path", p) for p in role_paths])
    runner = local["ansible-runner"]

    with temppathlib.TemporaryDirectory() as tmpdir:
        with open(tmpdir.path / "play.yml", "w") as f:
            f.write('\n'.join([
                '- hosts: localhost',
                '  roles:',
                *(f'    - {role}' for role in itertools.chain(*roles_to_run.values()))
            ]))
        args = ("--project-dir", str(tmpdir.path), "--play", "play.yml", "run", str(tmpdir.path))
        runner[(*role_path_args, *args)] & FG


def run():
    app()
