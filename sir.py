# -*- coding: iso-8859-15 -*-

#from sets import Set

from tgscurve import TgsCurve

class Sir:
    """
    Encapsulate SIR (strate d'inventaire regroupée) data
    """
    
    _bogus_curve = TgsCurve("")
    _default_null_qual_value = "X"
    
    def __init__(self, id):
        self._id = id
        self._area = 0.0
        self._species_curve_dict = {}
        self._species_age_dict = {}
        self._stock_dict = {}
        self._stand_dict = {}
        self._null_qual_value = self._default_null_qual_value

    def id(self):
        return self._id

    def set_area(self, area):
        self._area = area

    def area(self):
        return float(self._area)

    def add_species(self, species):
        self._stock_dict[species] = {}
        self._stand_dict[species] = {}

    def set_sirf(self, sirfid):
        self._sirfid = sirfid

    def sirf(self):
        return self._sirfid

    def set_curve(self, species, curve):
        #if species not in self._stock_dict:
        #    self.add_species(species)
        self._species_curve_dict[species] = curve

    def curve(self, species):
        tmp = None
        if species in self._species_curve_dict:
            tmp = self._species_curve_dict[species]
        return tmp

    def set_age(self, species, age):
        self._species_age_dict[species] = age

    def age(self, species):
        tmp = None
        if species in self._species_age_dict:
            tmp = self._species_age_dict[species]
        return tmp
            
    def set_stock(self, species, diam, volha):
        if not volha: return
        if species not in self._stock_dict:
            self.add_species(species)
        self._stock_dict[species][diam] = volha

    def set_stand(self, species, diam, qual, stemsha):
        if not stemsha: return
        if not qual:
            qual = self._null_qual_value
        if species not in self._stand_dict:
            self.add_species(species)
        if diam not in self._stand_dict[species]:
            self._stand_dict[species][diam] = {}
        self._stand_dict[species][diam][qual] = float(stemsha)

    def stock(self, species, diam=0):
        tmp = 0.0
        if species in self._stock_dict:
            if diam and diam in self._stock_dict[species]:
                tmp = self._stock_dict[species][diam]
            elif not diam:
                # diam not specified, return total for species
                tmp = 0
                for d in self._stock_dict[species]:
                    tmp += self._stock_dict[species][d]
        return float(tmp)

    def stand(self, species="", diam=0, qual=""):
        tmp = 0.0
        if species and species in self._stand_dict:
            if diam and diam in self._stand_dict[species]:
                if qual and qual in self._stand_dict[species][diam]:
                    tmp = self._stand_dict[species][diam][qual]
                elif not qual:
                    # qual not specified, return total for diam
                    for q in self._stand_dict[species][diam]:
                        tmp += self._stand_dict[species][diam][q]
            elif not diam:
                # diam not specified, return total for species
                for d in self._stand_dict[species]:
                    tmp += self.stand(species, d)
        elif not species:
            # species not specified, return total
            tmp = 0.0
            for s in self._stand_dict:
                tmp += self.stand(s)
        return tmp

    def species_list(self):
        s = set()
        s.update(self._stand_dict.keys())
        s.update(self._stock_dict.keys())
        return list(s)

    def diam_list(self, species):
        s = set()
        if species in self._stock_dict:
            s.update(self._stock_dict[species].keys())
        if species in self._stand_dict:
            s.update(self._stand_dict[species].keys())
        return list(s)

    def qual_list(self, species, diam):
        keys = []
        if species in self._stand_dict and diam in self._stand_dict[species]: 
            keys = self._stand_dict[species][diam].keys()
            if '' in keys:
                keys.remove('')
            keys.sort()
        return keys


if __name__ == "__main__":
    print "Testing Sir class"

    sir = Sir("sirid")
    sir.set_stand("a", 1, "A", 1)
    sir.set_stand("a", 1, "B", 1)
    sir.set_stand("a", 2, "A", 1)
    sir.set_stand("a", 2, "B", 1)
    sir.set_stand("a", 3, "", 1)
    sir.set_stand("b", 1, "", 1)

    sir.set_stock("a", 4, 1)

    print sir.stand("a", 1, "A")
    print sir.stand("a", 1)
    print sir.stand("a")
    print sir.stand("b")

    print sir.species_list()
    print sir.diam_list("a")
    

    
