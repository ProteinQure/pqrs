import typer
from plumbum.cmd import git
from plumbum import local, FG, BG

from pqrs import backend
from pqrs import paths
from pqrs import tui
from pqrs.config import config


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

    config.channels[f"{namespace}.{collection}"] = url
    config.roles[f"{namespace}.{collection}"] = None


@app.command()
def configure():
    """
    Select which roles you want to configure to be installed and updated by
    PQRS.
    """

    pqrs_roles = backend.discover_roles()

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
        config.roles[collection] = {
            r.name: r.installed_version
            for r in tui.select_roles(roles)
        }


@app.command()
def update():
    """
    Fetch newest configuration info and update the setup.
    """

    galaxy = local["ansible-galaxy"]

    # Fetch the newest updates from channels
    for url in config.channels.values():
        result = galaxy["collection", "install", "--force", url].run()

    # Discover roles
    pqrs_roles = backend.discover_roles()

    roles_to_run = {
        collection: [
            r
            for r in roles
            if r.name in config.roles.get(collection, []) and r.is_outdated
        ]
        for collection, roles in pqrs_roles.items()
    }

    backend.execute_roles(roles_to_run)


@app.command()
def execute():
    """
    Select which roles you want to install.
    """

    pqrs_roles = backend.discover_roles()

    # Ask user to (re)configure the roles
    roles_to_run = {
        collection: tui.select_roles(roles)
        for collection, roles in pqrs_roles.items()
    }

    backend.execute_roles(roles_to_run)


def run():
    app()
