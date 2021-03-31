class ProductStratum:
    """ForestModel product stratum data.

    Fragments in product stratum have common set of product attributes.
    """

    _id_default = ""
    _description_default = ""
    _treatment_stratum_id_default = ""
    _feature_stratum_id_default = ""
    _current_treatment_id_default = ""

    def __init__(self,
                 id=_id_default,
                 treatment_stratum_id=_treatment_stratum_id_default,
                 feature_stratum_id=_feature_stratum_id_default,
                 current_treatment_id=_current_treatment_id_default,
                 description=_description_default):
        self._id = id
        self._treatment_stratum_id=treatment_stratum_id
        self._feature_stratum_id=feature_stratum_id
        self._current_treatment_id=current_treatment_id
        self._description = description
        self._attribute_dict = {}
        self._has_volume_attribute = False

    def set_current_treatment_id(self, current_treatment_id):
        self._current_treatment_id = current_treatment_id

    def current_treatment_id(self):
        return self._current_treatment_id

    def set_treatment_stratum_id(self, treatment_stratum_id):
        self._treatment_stratum_id = treatment_stratum_id

    def treatment_stratum_id(self):
        return self._treatment_stratum_id

    def set_feature_stratum_id(self, feature_stratum_id):
        self._feature_stratum_id = feature_stratum_id

    def feature_stratum_id(self):
        return self._feature_stratum_id

    def has_volume_attribute(self):
        return self._has_volume_attribute

    def has_attribute(self, attribute):
        key = attribute
        if not isinstance(key, basestring):
            key = attribute.key()
        return key in self._attribute_dict.keys()

    def add_attribute(self, attribute, key_prefix=""):
        key = key_prefix+attribute.key()
        if key not in self._attribute_dict.keys():
            self._attribute_dict[key] = attribute
            if attribute.is_volume():
                self._has_volume_attribute = True

    def attribute_key_list(self):
        keys = self._attribute_dict.keys()
        keys.sort()
        return keys

    def id(self):
        return self._id

    def description(self):
        return self._description

    def attribute(self, key):
        result = None
        if key in self._attribute_dict:
            result = self._attribute_dict[key]
        return result
        

if __name__ == "__main__":
    # test code for ProductStratum class

    from fmg.attribute import Attribute
    from fmg.attributes import Attributes
    #reload(fmg.product)

    a = Attribute("attribute.label")
    aa = Attributes("attributes.label")
    
    ps = ProductStratum("productstratum.id")
    ps.add_attribute(a)
    ps.add_attribute(aa)

    for a in ps.attribute_list():
        print "\n".join(a.dump_xml())
