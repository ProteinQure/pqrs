from semantic_version import Version
from ruamel import yaml


def VersionRepresenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(data))

yaml.representer.RoundTripRepresenter.add_representer(
    Version, VersionRepresenter
)

