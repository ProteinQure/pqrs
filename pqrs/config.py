"""
Implements interface for the PQRS configuration file.
"""
import logging

from datafiles import datafile

from pqrs import paths

# Supress info messages from datafiles
logging.getLogger('datafiles').setLevel(logging.CRITICAL)


@datafile(str(paths.PQRS_LOCATION / "pqrs.yml"))
class Config:
    channels: dict[str, str] = None
    roles: dict[str, list[str]] = None


config = Config.objects.get_or_create()
