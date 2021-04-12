"""
Implements interface for the PQRS configuration file.
"""

from datafiles import datafile

from pqrs import paths


@datafile(str(paths.PQRS_LOCATION / "pqrs.yml"))
class Config:
    channels: dict[str, str] = None
    roles: dict[str, list[str]] = None


config = Config.objects.get_or_create()
