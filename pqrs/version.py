import semantic_version


class Version(semantic_version.Version):
    """
    Extension of the semantic_version.Version that can be processed by
    rumael.yaml.
    """

    def to_yaml(self):
        return str(self)
