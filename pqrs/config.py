"""
Implements interface for the PQRS configuration file.
"""

from datafiles import datafile


PQRS_LOCATION = local.env.home / '.pqrss'


@datafile(str(PQRS_LOCATION / "pqrs.yml"))
class Config:
    channels: dict[str, str] = None
    roles: dict[str, list[str]] = None
