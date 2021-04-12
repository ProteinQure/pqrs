import dataclasses
import pathlib
import json

import plumbum
import typer
import yaml

from datafiles import datafile
from plumbum.cmd import git
from plumbum import local, FG, BG

from pqrs.selector import run_selector


PQRS_LOCATION = local.env.home / '.pqrss'
COLLECTIONS_LOCATION = pathlib.Path('~/.ansible/collections/ansible_collections/').expanduser()

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


@dataclasses.dataclass
class Role:
    name: str
    description: list[str]

    @classmethod
    def from_path(cls, path):
        name = path.stem

        metadata = {}
        metadata_path = path / 'meta/main.yml'

        if metadata_path.exists():
            with open(path / 'meta/main.yml') as f:
                metadata = yaml.load(f)

        description = metadata.get('pqrs_info', {}).get('description', '')

        return cls(name, [line.strip() for line in description.splitlines()])


@app.command()
def configure():
    """
    Select which roles you want to install.
    """

    # Discover the PQRS-enabled collections
    pqrs_collections = {
        f"{path.parent.parent.stem}.{path.parent.stem}": path.parent
        for path in COLLECTIONS_LOCATION.glob('*/*/MANIFEST.json')
        if 'pqrs' in json.load(open(path)).get('collection_info', {}).get('tags', [])
    }

    # Locate the roles for each collection
    pqrs_roles = {
        collection: [Role.from_path(p) for p in path.glob('roles/*')]
        for collection, path in pqrs_collections.items()
    }

    config = Config.objects.get_or_create()

    for collection, roles in pqrs_roles.items():
        config.roles[collection] = run_selector(roles)


def run():
    app()
