class SuccessionStratum:
    """ForestModel succession stratum data.
    """

    _id_default = ""
    _description_default = ""

    def __init__(self, id=_id_default, succession=None, description=_description_default):
        self._id = id
        self._succession = succession
        self._description = description

    def set_succession(self, succession):
        self._succession = succession

    def succession(self):
        return self._succession

    def id(self):
        return self._id

    def description(self):
        return self._description
    
