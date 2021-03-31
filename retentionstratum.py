class RetentionStratum:
    """ForestModel retention stratum data.
    """

    _id_default = ""
    _description_default = ""

    def __init__(self, id, retention=None, description=_description_default):
        self._id = id
        self._retention = retention
        self._description = description

    def set_retention(self, retention):
        self._retention = retention

    def retention(self):
        return self._retention

    def id(self):
        return self._id

    def description(self):
        return self._description

    def dump_xml(self):
        lines = []
        lines.append("""<retention factor="%s" />""" % self._retention)
        return lines
    
