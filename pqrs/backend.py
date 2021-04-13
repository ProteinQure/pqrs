"""
Implements backend-related functionality.
"""

import dataclasses
import itertools
import json
from typing import Optional, Any

import temppathlib
import yaml
from plumbum import local, FG, BG

from pqrs import paths
from pqrs.config import config
from pqrs.version import Version


@dataclasses.dataclass
class Role:
    name: str
    collection: str
    description: list[str]
    variables: dict[str, Any]
    available_version: Version
    installed_version: Optional[Version] = None
    selected: bool = False

    @classmethod
    def from_path(cls, path, collection):
        name = path.stem

        metadata = {}
        metadata_path = path / 'meta/pqrs.yml'

        if metadata_path.exists():
            with open(path / 'meta/pqrs.yml') as f:
                metadata = yaml.safe_load(f)

        description = metadata.get('description', '')
        available = Version(metadata.get('version', '0.0.0'))
        installed = (config.channels[collection]['roles'] or {}).get(name)
        config_vars = metadata.get('config', {})

        return cls(
            name,
            collection,
            [line.strip() for line in description.splitlines()],
            config_vars,
            available,
            Version(installed) if installed else None,
        )

    @property
    def is_outdated(self):
        return self.installed_version is None or self.available_version > self.installed_version


def discover_roles():
    """
    Discovers PQRS-enabled roles on the filesystem.
    """

    # Discover the PQRS-enabled collections
    pqrs_collections = {
        f"{path.parent.parent.stem}.{path.parent.stem}": path.parent
        for path in paths.COLLECTIONS.glob('*/*/MANIFEST.json')
        if len(list(path.parent.glob('roles/*/meta/pqrs.yml'))) > 0
    }

    # Locate the roles for each collection
    return {
        collection: [
            Role.from_path(p, collection)
            for p in path.glob('roles/*')
            if (p / 'meta/pqrs.yml').exists()
        ]
        for collection, path in pqrs_collections.items()
    }


def execute_roles(roles_to_run):
    """
    Executes the given roles using ansible-runner.
    """

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
                *(f'    - {role.name}' for role in itertools.chain(*roles_to_run.values()))
            ]))
        args = ("--project-dir", str(tmpdir.path), "--play", "play.yml", "run", str(tmpdir.path))
        runner[(*role_path_args, *args)] & FG

    for collection, roles in roles_to_run.items():
        # Store the executed roles. Prefer None over empty dict to ensure
        #     roles:
        #       collection.name:
        # over
        #     roles:
        #       collection.name: {}
        config.channels[collection]["roles"] = {r.name: r.available_version for r in roles} or None
