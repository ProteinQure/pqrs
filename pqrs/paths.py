"""
Provides common paths.
"""

import pathlib


COLLECTIONS = pathlib.Path('~/.ansible/collections/ansible_collections/').expanduser()
PQRS_LOCATION = pathlib.Path('~/.pqrs').expanduser()
