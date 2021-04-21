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

    if f"{namespace}.{collection}" not in config.channels:
        config.channels[f"{namespace}.{collection}"] = {'url': url, 'roles': None}
    else:
        config.channels[f"{namespace}.{collection}"]["url"] = url


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
        if (collection_cfg := config.channels.get(collection))
        and role.name in (collection_cfg.get('roles') or {})
    ]
    for role in active_roles:
        role.selected = True

    # Ask user to (re)configure the roles
    selected_roles, provided_vars = tui.select_roles(pqrs_roles)

    for collection, roles in pqrs_roles.items():
        # Update the selected roles
        config.channels[collection]["roles"] = {
            r.name: r.installed_version
            for r in selected_roles[collection]
        } or None

        # Update the configuration
        if config.variables is None:
            config.variables = {}

        for var, value in provided_vars.items():
            if '.' in var:
                group, var_name = var.split('.')
                if group not in config.variables:
                    config.variables[group] = {}
                config.variables[group][var_name] = value
            else:
                config.variables[var] = value


@app.command()
def update():
    """
    Fetch newest configuration info and update the setup.
    """

    galaxy = local["ansible-galaxy"]

    # Fetch the newest updates from channels
    for channel in config.channels.values():
        result = galaxy["collection", "install", "--force", channel["url"]].run()

    # Discover roles
    pqrs_roles = backend.discover_roles()

    roles_to_run = {
        collection: [
            r
            for r in roles
            if (collection_cfg := config.channels.get(collection))
            and r.name in (collection_cfg['roles'] or {})  # only install configured roles
            and r.is_outdated
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
        collection: tui.select_roles(roles)[0]
        for collection, roles in pqrs_roles.items()
    }

    backend.execute_roles(roles_to_run)


def run():
    app()
