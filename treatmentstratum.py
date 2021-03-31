from fmg.treatment import Treatment

class TreatmentStratum:
    """ForestModel treatment stratum data.

    Fragments in treatment stratum have common set of treatments.
    """

    _id_default = ""
    _description_default = ""

    #_id = _id_default
    #_description = _description_default

    def __init__(self, id, description=_description_default):
        self._id = id
        self._description = description
        self._treatment_map = {}

    def add_treatment(self, treatment):
        self._treatment_map[treatment.label()] = treatment

    def treatment_label_list(self):
        return self._treatment_map.keys()
    
    def treatment_id_list(self):
        result = []
        for t in self._treatment_map.values():
            result.append(t.id())
        return result

    def treatment(self, label):
        tmp = None
        if label in self._treatment_map:
            tmp = self._treatment_map[label]
        return tmp

    def treatment_list(self):
        return self._treatment_map.values()

    def set_id(self, id):
        self._id = id

    def id(self):
        return self._id

    def description(self):
        return self._description
        

if __name__ == "__main__":
    # test code for TreatmentStratum class

    from fmg.treatment import Treatment
    #reload(fmg.treatment)

    t = Treatment("treatment.label")
    ts = TreatmentStratum("treatmentstratum.id")
    ts.add_treatment(t)

    for label in ts.treatment_label_list():
        print "\n".join(ts.treatment(label).dump_xml())
