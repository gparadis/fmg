# -*- coding: iso-8859-15 -*-

from math import pi
from sir import Sir

class Sirf:
    """
    Encapsulate SIRF (strate d'inventaire regroupée fusionnée) data
    """
    
    _default_null_qual_value = "X"
    _species_group_dict = {}
    _group_species_dict = {}
    _invasion_factor_default = 1.0
    _invasion_type_default = "R"

    def __init__(self,
                 id="",
                 final_harvest_cost_expression_id="",
                 partial_harvest_cost_expression_id="",
                 final_harvest_value_expression_id="",
                 partial_harvest_value_expression_id="",
                 invasion_factor=_invasion_factor_default,
                 invasion_type=_invasion_type_default,
                 mean_inventory_age=0,
                 force_meanage_lookup=False):
        self._force_meanage_lookup=force_meanage_lookup
        self._id = id
        self._mean_age = 0.0
        self._area = 0.0
        self._stock_threshold = 0.0
        self._curve_factor_precision = 0.001 # constant (round factor to 3 decimal places)
        self._sir_dict = {}
        self._curve_dict = {}
        self._stock_dict = {}
        self._stand_dict = {}
        self._curve_factor_dict = {}
        self._curve_xoffset_dict = {}
        self._curve_age_dict = {}
        self._null_qual_value = self._default_null_qual_value
        self._product_distribution_id = ""
        self._x = "x"
        self._final_harvest_cost_expression_id=final_harvest_cost_expression_id
        self._partial_harvest_cost_expression_id=partial_harvest_cost_expression_id
        self._final_harvest_value_expression_id=final_harvest_value_expression_id
        self._partial_harvest_value_expression_id=partial_harvest_value_expression_id
        self._invasion_factor=invasion_factor
        self._invasion_type=invasion_type
        self._invasion_species_factor_dict = {}
        self._regen_id = ""
        self._mean_inventory_age = mean_inventory_age

    def max_curve_factor(self):
        return max(self._curve_factor_dict.values())

    def mean_inventory_age(self):
        return self._mean_inventory_age()

    def set_regen_id(self, regen_id):
        self._regen_id = regen_id

    def regen_id(self):
        return self._regen_id

    def set_invasion_species_factor(self, species_code, factor):
        self._invasion_species_factor_dict[species_code] = factor

    def invasion_species_factor(self, species_code):
        result = 0.0
        if species_code in self._invasion_species_factor_dict:
            result = self._invasion_species_factor_dict[species_code]
        return result

    def invasion_species_list(self):
        return self._invasion_species_factor_dict.keys()

    def set_invasion(self, factor, invasion_type="A"): # incoherent (see self._invasion_type_default)
        self._invasion_factor=factor
        self._invasion_type=invasion_type

    def invasion_factor(self):
        return self._invasion_factor

    def invasion_type(self):
        return self._invasion_type

    def set_final_harvest_cost_expression_id(self, id):
        self._final_harvest_cost_expression_id = id

    def final_harvest_cost_expression_id(self):
        return self._final_harvest_cost_expression_id

    def set_partial_harvest_cost_expression_id(self, id):
        self._partial_harvest_cost_expression_id = id

    def partial_harvest_cost_expression_id(self):
        return self._partial_harvest_cost_expression_id

    def set_final_harvest_value_expression_id(self, id):
        self._final_harvest_value_expression_id = id

    def final_harvest_value_expression_id(self):
        return self._final_harvest_value_expression_id

    def set_partial_harvest_value_expression_id(self, id):
        self._partial_harvest_value_expression_id = id

    def partial_harvest_value_expression_id(self):
        return self._partial_harvest_value_expression_id

    def set_product_distribution_id(self, pdid):
        self._product_distribution_id = pdid

    def product_distribution_id(self):
        return self._product_distribution_id

    def curve_factor_precision(self):
        return self._curve_factor_precision

    def set_curve_factor_precision(self, val):
        self._curve_factor_precision = val

    def assign_species_group(self, species, group):
        self._species_group_dict[species] = group
        if group not in self._group_species_dict:
            self._group_species_dict[group] = set()
        self._group_species_dict[group].add(species)

    def species_group(self, species):
        tmp = None
        if species in self._species_group_dict:
            tmp = self._species_group_dict[species]
        return tmp

    def group_species_list(self, group):
        # note: returns set object (not list)... cast to list if problem 
        tmp = None
        if group in self._group_species_dict:
            tmp = self._group_species_dict[group]
        return tmp  
    
    def id(self):
        return self._id

    def add_sir(self, sir):
        self._sir_dict[sir.id()] = sir

    def update(self):
        self._calc_area()
        self._calc_stand_stock()
        self._calc_species_age()
        self._assign_curves()
        self._calc_mean_age()
        self._calc_curve_factors()

    def sir_id_list(self):
        keys = self._sir_dict.keys()
        keys.sort()
        return keys

    def sir(self, id):
        tmp = None
        if id in self._sir_dict:
            tmp = self._sir_dict[id]
        return tmp

    def _calc_species_age(self):
        self._mean_age = 0.0
        tmp_area_dict = {}
        for species in self.species_list():
            for sirid in self._sir_dict:
                sir = self._sir_dict[sirid]
                if not sir.curve(species): continue # skip if null curve
                if species not in self._curve_age_dict:
                    self._curve_age_dict[species] = 0.0
                if species not in tmp_area_dict:
                    tmp_area_dict[species] = 0.0
                #print self._curve_age_dict[species], sir.age(species), sir.area() # debug 
                self._curve_age_dict[species] += float(sir.age(species)) * sir.area()
                tmp_area_dict[species] += sir.area()
            if species in self._curve_age_dict:
                self._curve_age_dict[species] /= tmp_area_dict[species]

    def _calc_mean_age(self):
        sum_volume = 0.0
        self._mean_age = 0.0
        for species in self.species_list():
            if species not in self._curve_age_dict or not self.curve(species): continue
            volume = self.curve(species).value(self.age(species))
            sum_volume += volume
            self._mean_age += self.age(species) * volume
        if sum_volume:            
            self._mean_age /= sum_volume

    def curve_xoffset(self, species):
        xoffset = 0.0
        if species in self._curve_dict:
            xoffset = self.age() - self.age(species)
        return int(xoffset)

    def age(self, species=""):
        tmp = 0.0
        if not species:
            tmp = self._mean_age
        elif species in self._curve_age_dict:
            tmp = self._curve_age_dict[species]
        return tmp
    
    def _calc_area(self):
        self._area = 0.0
        for sir in self._sir_dict:
            self._area += self._sir_dict[sir].area()

    def area(self):
        return self._area

    def curve_factor(self, species):
        tmp = 0.0
        if species in self._curve_factor_dict:
            tmp = self._curve_factor_dict[species]
        return tmp

    def _calc_curve_factors(self):
        cfp = self.curve_factor_precision()
        for species in self.species_list():
            if not self.curve(species): continue
            sv = self.stock(species)
            #import pprint
            #print "_calc_curve_factors", self.curve(species).point_dict() # debug
            age = self.age(species)
            if self._force_meanage_lookup:
                age = self._mean_age
                if __debug__:
                    print "Sirf._calc_curve_factors: forcing mean age lookup", self._id, age
            cv = self.curve(species).value(age)
            #if __debug__:
            #    print cv
            #    print
            self._curve_factor_dict[species] = round((sv / cv) / cfp) * cfp


    def _assign_curves(self):
        """
        Automatically assign reference volume curve id (from tgs.dbf)
        to each sirf/species combination.
        
        Curve id selected from list of proposed sir curves.
        Curve majority determined by volume representation (i.e. for each curve id, greatest
        sum of [sir_area * sir_ess_volha]).
        """
        tmp_dict1 = {}
        tmp_dict2 = {}
        curveid_suffix = ""
        
        for sirid in self._sir_dict:
            sir = self._sir_dict[sirid]
            for species in sir.species_list():
                if not sir.curve(species): continue
                if species not in tmp_dict1:
                    tmp_dict1[species] = {}
                    tmp_dict2[species] = {}
                tmp_vol = 0
                if sir.curve(species).id() not in tmp_dict1[species]:
                    tmp_dict1[species][sir.curve(species).id()] = sir.curve(species)
                    tmp_dict2[species][sir.curve(species).id()] = sir.stock(species) * sir.area() 
                else:
                    tmp_dict2[species][sir.curve(species).id()] += sir.stock(species) * sir.area()
        for species in tmp_dict1:
            tmp_vol = 0
            for curveid in tmp_dict1[species]:
                if tmp_vol < tmp_dict2[species][curveid]:
                    curve = tmp_dict1[species][curveid]
                    curve.set_id(curve.id() + curveid_suffix)
                    self._curve_dict[species] = curve
                    tmp_vol = tmp_dict2[species][curveid]


    def curve(self, species):
        tmp = None
        if species in self._curve_dict:
            tmp = self._curve_dict[species]
        return tmp


    def _calc_stock(self):
        """
        Calculated area-weighted stock table from constituent Sir list.
        """
        sum_area = 0
        for sirid in self._sir_dict:
            sir = self._sir_dict[sirid]
            for species in sir.species_list():
                if species not in self._stock_dict:
                    self._stock_dict[species] = {}
                for diam in sir.diam_list(species):
                    if diam not in self._stock_dict[species]:
                        self._stock_dict[species][diam] = 0
                    self._stock_dict[species][diam] += sir.stock(species, diam) * sir.area()
            sum_area += sir.area()
        del_list = []
        for species in self._stock_dict:
            for diam in self._stock_dict[species]:
                if not self._stock_dict[species][diam]:
                    del_list.append((species, diam))
                else:
                    self._stock_dict[species][diam] /= sum_area
        for i in del_list:
            species = i[0]
            diam = i[1]
            del self._stock_dict[species][diam]


    def _calc_stand_stock(self):
        """
        Calculated area-weighted stand and stock tables from constituent Sir list.
        """
        sum_area = 0
        
        self._stand_dict.clear()
        self._stock_dict.clear()

        debug = False
        if debug:
            print "SIRF_ID,SIR_ID,SPECIES,DIAM,QUAL,STEMSHA,AREA"

        for sirid in self._sir_dict:
            sir = self._sir_dict[sirid]
            for species in sir.species_list():
                if species not in self._stock_dict:
                    self._stock_dict[species] = {}
                if species not in self._stand_dict:
                    self._stand_dict[species] = {}
                for diam in sir.diam_list(species):
                    if diam not in self._stock_dict[species]:
                        self._stock_dict[species][diam] = 0.0
                    if diam not in self._stand_dict[species]:
                        self._stand_dict[species][diam] = {"":0.0}
                    self._stock_dict[species][diam] += float(sir.stock(species, diam) * sir.area())
                    if sir.qual_list(species, diam) == ['']:
                        continue
                    for qual in sir.qual_list(species, diam):
                        if qual not in self._stand_dict[species][diam]:
                            self._stand_dict[species][diam][qual] = 0.0
                        self._stand_dict[species][diam][qual] += sir.stand(species, diam, qual) * sir.area()
            sum_area += sir.area()
        for species in self.species_list():
            for diam in self.diam_list(species):
                self._stock_dict[species][diam] /= float(sum_area)
                for qual in self.qual_list(species, diam):
                    self._stand_dict[species][diam][qual] /= float(sum_area)


    def _basal_area(self, diam):
        #print "_basal_area", diam, pow((diam * 0.005), 2) * pi # debug
        return pow((diam * 0.005), 2) * pi


    def stand(self, species="", diam=0, qual="", as_ba=False):
        tmp = 0.0
        if species and species in self._stand_dict:
            if diam and diam in self._stand_dict[species]:
                if qual and qual in self._stand_dict[species][diam]:
                    tmp = self._stand_dict[species][diam][qual]
                elif not qual:
                    # qual not specified, return total for diam
                    tmp = 0.0
                    for q in self._stand_dict[species][diam]:
                        if as_ba:
                            #print "as_ba", species, diam, qual
                            tmp += self._stand_dict[species][diam][q] * self._basal_area(diam)
                        else:
                            tmp += self._stand_dict[species][diam][q]
            elif not diam:
                # diam not specified, return total for species
                tmp = 0.0
                for d in self._stand_dict[species]:
                    tmp += self.stand(species, d)
        elif not species:
            # species not specified, return total
            tmp = 0.0
            for s in self._stand_dict:
                tmp += self.stand(s)
        return tmp

        
    def stock(self, species="", diam=0, group=""):
        tmp = 0.0
        if group and group in self._group_species_dict:
            tmp = 0.0
            for gs in self.group_species_list(group):
                tmp += self.stock(gs)
            return tmp            
        if not species:
            tmp = 0.0
            for s in self._stock_dict:
                tmp += self.stock(s)
        elif species in self._stock_dict:
            if diam and diam in self._stock_dict[species]:
                tmp = self._stock_dict[species][diam]
            elif not diam:
                # assume diam not specified, return total for species
                tmp = 0.0
                for d in self._stock_dict[species]:
                    tmp += self._stock_dict[species][d]
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
        keys = None
        if species in self._stand_dict and diam in self._stand_dict[species]: 
            keys = self._stand_dict[species][diam].keys()
            if '' in keys:
                keys.remove('')
            keys.sort()
        return keys


    def set_stock_threshold(self, val):
        self._stock_threshold = val


    def stock_threshold(self):
        return self._stock_threshold


    def set_stock(self, species, diam, volha):
        self._stock_dict[species][diam] = float(volha)


    def clean(self):
        """
        Remove species that have no curve assignment.
        Remove species that have very small volumes,
        and reassign stock table volume to remaining species
        in group (only if species groups defined).
        """
        gaules = [2, 4, 6, 8]
        #gaules = [] # debug
        
        tmp4 = self.stock()
        
        tmp_species_dict = {}
        for species in self.species_list():
            if not self.curve(species):
                pass # is this 
                #self._remove_species(species)
            elif len(self._species_group_dict) and \
                     (self.stock(species) / self.stock()) < self.stock_threshold():
                group = self.species_group(species)
                if group not in tmp_species_dict:
                    tmp_species_dict[group] = []
                tmp_species_dict[group].append(species)

        tmp3 = 0.0
        for group in tmp_species_dict:
            if self.group_species_list(group) and len(self.group_species_list(group))==1: continue
            for species in tmp_species_dict[group]:
                if self.stock(species=species) == self.stock(group=group): continue
                tmp5 = 0.0
                species_stock = self.stock(species)
                self._reset_stock(species)
                gtotvol = self.stock(group=self.species_group(species)) # - self.stock(species=species)
                #print self.group_species_list(self.species_group(species)) # debug
                for s in self.group_species_list(self.species_group(species)):
                    if self.stock(s) and gtotvol:
                        svol = species_stock * self.stock(s) / gtotvol
                        tmp5 += svol
                        tmp3 += species_stock
                        for d in self.diam_list(s):
                            if d in gaules: continue
                            # evenly distribute volume across diameter classes
                            tmp1 = self.stock(s) # debug
                            tmp2 = self.stock(s, d) # debug
                            self.set_stock(s,d, self.stock(s,d) + (svol / len(self.diam_list(s))))
                self._remove_species(species)


    def _reset_stock(self, species):
        """
        Reset stock to 0 for species.
        """
        for d in self.diam_list(species):
            self.set_stock(species, d, 0.0)
                
    def _remove_species(self, species):
        """
        Remove species from curve list and stock table
        """
        if species in self._curve_dict:
            del self._curve_dict[species]
        if species in self._stock_dict:
            del self._stock_dict[species]
#         group = self.species_group(species)
#         if group:
#             if species in self._group_species_dict[group]:
#                 self._group_species_dict[group].remove(species)
#         if species in self._species_group_dict:
#             del self._species_group_dict[species]
        

if __name__ == "__main__":
    print "Testing Sirf class"

    test_num = 3

    if test_num == 1:
        sirf1 = Sirf("sirf1")

        sir1 = Sir("sir1")
        sir1.set_area(100)
        sir1.set_age(10, "aaa")
        sir1.set_age(20, "bbb")
        sir1.set_age(30, "ccc")
        sir1.set_stock("aaa", 1, 1)
        sir1.set_stock("bbb", 2, 10)
        sir1.set_stock("ccc", 3, 100)
        sir1.set_stock("ddd", 1, 0) # this one should get filtered out
        sir1.set_stand("aaa", 1, "A", 1)
        sir1.set_stand("bbb", 1, "B", 1)
        sir1.set_stand("ccc", 1, "C", 1)

        sir2 = Sir("sir2")
        sir2.set_area(200)
        sir2.set_age(10, "aaa")
        sir2.set_age(20, "bbb")
        sir2.set_age(30, "ccc")
        sir2.set_stock("aaa", 1, 2)
        sir2.set_stock("bbb", 2, 20)
        sir2.set_stock("ccc", 3, 200)
        sir2.set_stand("aaa", 1, "A", 1)
        sir2.set_stand("bbb", 1, "B", 1)
        sir2.set_stand("ccc", 1, "C", 1)

        sir3 = Sir("sir3")
        sir3.set_area(300)
        sir3.set_age(10, "aaa")
        sir3.set_age(20, "bbb")
        sir3.set_age(30, "ccc")
        sir3.set_stock("aaa", 1, 3)
        sir3.set_stock("bbb", 2, 30)
        sir3.set_stock("ccc", 3, 300)
        sir3.set_stand("aaa", 1, "A", 1)
        sir3.set_stand("bbb", 1, "B", 1)
        sir3.set_stand("ccc", 1, "C", 1)

        sirf1.add_sir(sir1)
        sirf1.add_sir(sir2)
        sirf1.add_sir(sir3)

        for sirid in sirf1.sir_id_list():
            sir = sirf1.sir(sirid)
            print sir.id(), sir.area()

        for s in sirf1.species_list():
            for d in sirf1.diam_list(s):
                print "stock"
                print sirf1.id(), s, d, sirf1.stock(s, d)
                print sirf1.id(), sir1.id(), sir1.stock(s, d)
                print sirf1.id(), sir2.id(), sir2.stock(s, d)
                print sirf1.id(), sir3.id(), sir3.stock(s, d)
                for q in sirf1.qual_list(s, d):
                    print "stand"
                    print sirf1.qual_list(s, d)
                    print sir1.qual_list(s, d)
                    print sir2.qual_list(s, d)
                    print sir3.qual_list(s, d)
                    print sirf1.id(), s, d, q, sirf1.stock(s, d, q)
                    print sirf1.id(), sir1.id(), sir1.stand(s, d, q)
                    print sirf1.id(), sir2.id(), sir2.stand(s, d, q)
                    print sirf1.id(), sir3.id(), sir3.stand(s, d, q)
    elif test_num == 2:
        sirf1 = Sirf("sirf1")

        sir1 = Sir("sir1")
        sir2 = Sir("sir2")
        sir3 = Sir("sir3")
        sir1.set_area(100)
        sir2.set_area(100)
        sir3.set_area(100)

        sir1.set_stand("a", 1, "A", 10)
        sir2.set_stand("a", 1, "A", 10)
        sir3.set_stand("a", 1, "A", 10)
        
        sirf1.add_sir(sir1)
        sirf1.add_sir(sir2)
        sirf1.add_sir(sir3)
        
        print sirf1._stand_dict
        print sir1._stand_dict
        print sir2._stand_dict
        print sir3._stand_dict
        print
        print sirf1.stand()
        print sir1.stand()
        print sir2.stand()
        print sir3.stand()

    elif test_num == 3:
        sirf1 = Sirf("sirf1")

        sir1 = Sir("sir1")
        sir1.set_area(1)
        sir1.set_age(10, "aaa")
        sir1.set_stand("aaa", 100, "A", 1)

        sirf1.add_sir(sir1)
        sirf1.update()

        print sir1.stand()
        print sirf1.stand(), sirf1.stand(as_ba=True)
        print sirf1.species_list()
        print "sirf1.diam_list('aaa')", sirf1.diam_list('aaa')
        print "sirf1.qual_list('aaa', 'A')", sirf1.qual_list('aaa', 100)
        print sirf1._stand_dict
