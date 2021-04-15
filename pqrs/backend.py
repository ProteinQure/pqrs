"""
Implements backend-related functionality.
"""

import dataclasses
import itertools
import json
from typing import Optional, Any

import datafiles.formats
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
        # Dump the configuration values into a temp file
        with open(tmpdir.path / "vars.yml", "w") as f:
            # We need to use datafiles serializer directly to turn just one
            # attribute of the class into yaml
            content = datafiles.formats.RuamelYAML.serialize(config.variables)
            f.write(content)

        # Prepare the playbook
        playbook = [{
            'hosts': 'localhost',
            'roles': [
                {'role': role.name, 'vars': {'role_version': role.installed_version}}
                for role in itertools.chain(*roles_to_run.values())
            ],
            'vars_files': str(tmpdir.path / "vars.yml")
        }]

        with open(tmpdir.path / "play.yml", "w") as f:
            content = datafiles.formats.RuamelYAML.serialize(playbook)
            f.write(content)

        # Execute the playbook, using private role vars switch to ensure
        # role_version variables are not overwriting each other
        args = ("--project-dir", str(tmpdir.path), "--play", "play.yml", "run", str(tmpdir.path))
        with local.env(ANSIBLE_PRIVATE_ROLE_VARS="True"):
            runner[(*role_path_args, *args)] & FG

    for collection, roles in roles_to_run.items():
        # Store the executed roles. Prefer None over empty dict to ensure
        #     roles:
        #       collection.name:
        # over
        #     roles:
        #       collection.name: {}
        config.channels[collection]["roles"] = {r.name: r.available_version for r in roles} or None
