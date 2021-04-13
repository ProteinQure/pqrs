"""
Implements interface for the PQRS configuration file.
"""
import logging
from typing import Optional
from dataclasses import dataclass

from datafiles import datafile

from pqrs import paths

# Supress info messages from datafiles
logging.getLogger('datafiles').setLevel(logging.CRITICAL)


@dataclass
class ChannelInfo:
    url: str
    roles: dict[str, str]

@datafile(str(paths.PQRS_LOCATION / "pqrs.yml"))
class Config:
    channels: dict[str, ChannelInfo] = None
    variables: Optional[dict[str, str]] = None


config = Config.objects.get_or_create()
