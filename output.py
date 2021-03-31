class Output:
    """
    ForestModel output element data
    """

    _curves_default = "curves.csv"
    _blocks_default = "blocks.csv"
    _features_default = "features.csv"
    _products_default = "products.csv"
    _treatments_default = "treatments.csv"
    _tracknames_default = "tracknames.csv"
    _messages_default = "messages.csv"
    _members_default = "members.csv"
    _protoaccounts_default = "protoaccounts.csv"

    _curves = _curves_default
    _blocks = _blocks_default
    _features = _features_default
    _products = _products_default
    _treatments = _treatments_default
    _tracknames = _tracknames_default
    _messages = _messages_default
    _members = _members_default
    _protoaccounts = _protoaccounts_default

    def curves(self):
        return self._curves

    def blocks(self):
        return self._blocks

    def features(self):
        return self._features

    def products(self):
        return self._products

    def treatments(self):
        return self._treatments

    def tracknames(self):
        return self._tracknames

    def messages(self):
        return self._messages

    def members(self):
        return self._members

    def protoaccounts(self):
        return self._protoaccounts

    def set_curves(self, filename):
        self._curves = filename

    def set_blocks(self, filename):
        self._blocks = filename

    def features(self, filename):
        self._features = filename

    def products(self, filename):
        self._products = filename

    def treatments(self, filename):
        self._treatments = filename

    def tracknames(self, filename):
        self._tracknames = filename

    def messages(self, filename):
        self._messages = filename

    def members(self, filename):
        self._members = filename

    def protoaccounts(self, filename):
        self._protoaccounts = filename

    def dump_xml(self):
        lines = []
        tmp = "<output "
        if self._curves != self._curves_default:
            tmp += """curves="%s" """ % self._curves
        if self._blocks != self._blocks_default:
            tmp += """blocks="%s" """ % self._blocks
        if self._features != self._features_default:
            tmp += """features="%s" """ % self._features
        if self._products != self._products_default:
            tmp += """products="%s" """ % self._products
        if self._treatments != self._treatments_default:
            tmp += """treatments="%s" """ % self._treatments
        if self._tracknames != self._tracknames_default:
            tmp += """tracknames="%s" """ % self._tracknames
        if self._messages != self._messages_default:
            tmp += """messages="%s" """ % self._messages
        if self._members != self._members_default:
            tmp += """members="%s" """ % self._members
        if self._protoaccounts != self._protoaccounts_default:
            tmp += """protoaccounts="%s" """ % self._protoaccounts
        tmp += " />"
        lines.append(tmp)
        return lines
