from fmg.curve import Curve

class ProductDistribution:

    _product_code_list = ["nu", "pa", "sc", "de"]
    _species_code_list = ["AUF",
                          "BOG",
                          "CHN",
                          "ERO",
                          "FRE",
                          "FRN",
                          "HEG",
                          "OSV",
                          "TIL",
                          "BOJ",
                          "BOP",
                          "ERS",
                          "PEB",
                          "PEH",
                          "PET",
                          "PEU",
                          "PIB",
                          "PIR",
                          "EPB",
                          "EPN",
                          "EPO",
                          "EPR",
                          "MEZ",
                          "PIG",
                          "SAB",
                          "PRU",
                          "THO",
                          "SEP",
                          "AUT"]

    _default_curve_list = []

    #_nu = Curve("product.distrib.nu")
    #_default_curve_nu.add_point(0, 0)
    #_default_curve_pa = Curve("product.distrib.pa")
    #_default_curve_pa.add_point(0, 0.33)
    #_default_curve_sc = Curve("product.distrib.sc")
    #_default_curve_sc.add_point(0, 0.33)
    #_default_curve_de = Curve("product.distrib.de")
    #_default_curve_de.add_point(0, 0.33)

    def __init__(self,
                 id=""):
        self._id = id
        self._curve_dict = {}
        for s in self._species_code_list:
            for p in self._product_code_list:
                self._curve_dict[s + p] = None
        
    def set_curve(self, species_code, product_code, curve):
        self._curve_dict[species_code + product_code] = curve

    def curve(self, species_code, product_code):
        #if not self._curve_dict[species_code + product_code]:
        #    for key in self._curve_dict: 
        #        c = self._curve_dict[key]
        #        if not c:
        #            print key, c
        return self._curve_dict[species_code + product_code]

    def species_code_list(self):
        return self._species_code_list

    def product_code_list(self):
        return self._product_code_list

    def curve_id_list(self):
        return self._curve_dict.keys()
    
    def id(self):
        return self._id
