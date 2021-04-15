"""
Implements interface for the PQRS configuration file.
"""
import logging
from typing import Optional
from dataclasses import dataclass

import datafiles

from pqrs import paths

# Supress info messages from datafiles
logging.getLogger('datafiles').setLevel(logging.CRITICAL)

# The INDENT_YAML_BLOCKS option unfortunately causes
# formatting problems for lists of dicts
datafiles.settings.INDENT_YAML_BLOCKS = False


@dataclass
class ChannelInfo:
    url: str
    roles: dict[str, str]

@datafiles.datafile(str(paths.PQRS_LOCATION / "pqrs.yml"))
class Config:
    channels: dict[str, ChannelInfo] = None
    variables: Optional[dict[str, str]] = None


config = Config.objects.get_or_create()
