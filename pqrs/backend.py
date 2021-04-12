"""
Implements backend-related functionality.
"""

import dataclasses
import json

import yaml

from pqrs import paths


@dataclasses.dataclass
class Role:
    name: str
    description: list[str]
    selected: bool = False

    @classmethod
    def from_path(cls, path):
        name = path.stem

        metadata = {}
        metadata_path = path / 'meta/pqrs.yml'

        if metadata_path.exists():
            with open(path / 'meta/pqrs.yml') as f:
                metadata = yaml.load(f)

        description = metadata.get('description', '')

        return cls(name, [line.strip() for line in description.splitlines()])


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
        collection: [Role.from_path(p) for p in path.glob('roles/*') if (p / 'meta/pqrs.yml').exists()]
        for collection, path in pqrs_collections.items()
    }
