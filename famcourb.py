class FamCourb:
    """
    Sylva II curve family (famille de courbes) data
    """
    _id_fam_courb_default = ""
    _code_default = ""
    _descr_default = ""
    _age_explo_default = 0
    _age_bris_default = 0
    _factor_default = 1.0

    
    def __init__(self,
                 id_fam_courb=_id_fam_courb_default,
                 code=_code_default,
                 descr=_descr_default,
                 age_explo=_age_explo_default,
                 age_bris=_age_bris_default,
                 factor=_factor_default):
        self._volume_curve = None
        self._repar_vol_essen_curve_map = {}
        self._id_fam_courb = id_fam_courb
        self._code = code
        self._descr = descr
        self._age_explo = age_explo
        self._age_bris = age_bris
        self._factor = factor

    def set_factor(self, val):
        self._factor = val

    def factor(self):
        return self._factor

    def id_fam_courb(self):
        return self._id_fam_courb

    def code(self):
        return self._code

    def descr(self):
        return self._descr

    def age_explo(self):
        return self._age_explo

    def age_bris(self):
        return self._age_bris

    def volume_curve(self):
        return self._volume_curve

    def species_list(self):
        return self._repar_vol_essen_curve_map.keys()

    def repar_vol_essen_curve(self, species):
        if species in self._repar_vol_essen_curve_map:
            return self._repar_vol_essen_curve_map[species]

    def set_id_fam_courb(self, id_fam_courb):
        self._id_fam_courb = id_fam_courb

    def set_code(self, code):
        self._code = code

    def set_descr(self, descr):
        self._descr = descr

    def set_age_explo(self, age_explo):
        self._age_explo = age_explo

    def set_age_bris(self, age_bris):
        self._age_bris = age_bris

    def set_volume_curve(self, curve):
        self._volume_curve = curve
    
    def add_repar_vol_essen_curve(self, species, curve):
        self._repar_vol_essen_curve_map[species] = curve

    
if __name__ == "__main__":
    fc = FamCourb()
    fc.add_repar_vol_essen_curve("foo", Curve())
    print fc.repar_vol_essen_curve("foo")
