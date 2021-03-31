from fmg.productdistribution import ProductDistribution
from fmg.curve import Curve

class FeatureStratum:
    """
    ForestModel feature stratum data.

    Fragments in feature stratum have common set of feature attributes.
    """

    _max_age = 500
    _id_default = ''
    _description_default = ''
    _is_pc_default = False
    _is_ct_default = False
    _is_sc_default = False
    _invasion_factor_default = 1.0
    _invasion_type_default = 'R'
    _invaded_default = False
    _invasion_enabled_default = False
    _regime_default = 'R'
    __debug = False

    #_id = _id_default
    #_description = _description_default

    def __init__(self,
                 id,
                 description=_description_default,
                 is_pc=_is_pc_default,
                 is_ct=_is_ct_default,
                 is_sc=_is_sc_default,
                 invasion_factor=_invasion_factor_default,
                 invasion_type=_invasion_type_default,
                 invaded=_invaded_default,
                 final_harvest_cost_expression_id='',
                 partial_harvest_cost_expression_id='',
                 final_harvest_value_expression_id='',
                 partial_harvest_value_expression_id='',
                 previous_feature_stratum_id='',
                 previous_treatment_id='',
                 invasion_enabled=_invasion_enabled_default,
                 treatment_stratum_id='',
                 treatment_stratum_id_list=[],
                 regime=_regime_default):
        self._id = id
        self._description = description
        self._is_pc = is_pc
        self._is_ct = is_ct
        self._is_sc = is_sc
        self._regime = regime
        
        self._attribute_id_list = []
        #self._species_list = []
        self._volume_attribute_dict = {}
        self._attribute_dict = {}

        self._total_volume_curve = None
        self._product_distribution_id = None
        self._invasion_factor=invasion_factor
        self._invasion_type=invasion_type
        self._invaded=invaded
        self._invasion_species_factor_dict = {}
        self._invasion_enabled = invasion_enabled
        self._final_harvest_cost_expression_id = final_harvest_cost_expression_id
        self._partial_harvest_cost_expression_id = partial_harvest_cost_expression_id
        self._final_harvest_value_expression_id = final_harvest_value_expression_id
        self._partial_harvest_value_expression_id = partial_harvest_value_expression_id
        if previous_feature_stratum_id:
            self._previous_feature_stratum_id=previous_feature_stratum_id
        else:
            self._previous_feature_stratum_id=self._id
        self._previous_treatment_id = previous_treatment_id
        self._treatment_stratum_id = treatment_stratum_id
        self._treatment_stratum_id_list = treatment_stratum_id_list

    def set_regime(self, val):
        self._regime = val

    def is_regime_regular(self):
        return self.regime() == 'R'

    def is_regime_irregular(self):
        return self.regime() == 'I'

    def regime(self):
        return self._regime

    def set_treatment_stratum_id(self, val):
        self._treatment_stratum_id = val

    def treatment_stratum_id(self):
        return self._treatment_stratum_id

    def set_treatment_stratum_id_list(self, val):
        self._treatment_stratum_id_list = val

    def treatment_stratum_id_list(self):
        if self._treatment_stratum_id_list:
            return self._treatment_stratum_id_list
        elif self._treatment_stratum_id:
            return [self._treatment_stratum_id]
        else:
            return []

    def previous_treatment_id(self):
        return self._previous_treatment_id

    def enable_invasion(self):
        self._invasion_enabled = True

    def invasion_enabled(self):
        return self._invasion_enabled

    def set_previous_feature_stratum_id(self, val):
        self._previous_feature_stratum_id = val

    def previous_feature_stratum_id(self):
        return self._previous_feature_stratum_id

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

    def base_curve(self, species):
        if species in self._volume_attribute_dict:
            return self._volume_attribute_dict[species].base_curve()

    def volume_attribute(self, species):
        if species in self._volume_attribute_dict:
            return self._volume_attribute_dict[species]

    def has_invasion_species_factors(self):
        return len(self._invasion_species_factor_dict)

    def set_invasion_species_factor(self, species_code, factor):
        self._invasion_species_factor_dict[species_code] = factor

    def invasion_species_factor(self, species_code):
        result = 0.0
        if species_code in self._invasion_species_factor_dict:
            result = self._invasion_species_factor_dict[species_code]
        return result

    def invasion_species_list(self):
        return self._invasion_species_factor_dict.keys()

    def species_list(self):
        return self._volume_attribute_dict.keys()

    def set_invasion_params(self, factor, invasion_type='A'): # incoherent (see self._invasion_type_default)
        self._invasion_factor=factor
        self._invasion_type=invasion_type

    def invasion_factor(self):
        return self._invasion_factor

    def invasion_type(self):
        return self._invasion_type

    def set_invaded(self, invaded):
        self._invaded = invaded

    def invaded(self):
        return self._invaded

    def set_invasion_transition(self, feature_stratum_id):
        self._invasion_transition = feature_stratum_id

    def invasion_transition(self):
        return self._invasion_transition

    def set_product_distribution_id(self, pdid):
        self._product_distribution_id = pdid

    def product_distribution_id(self):
        return self._product_distribution_id

    def set_is_pc(self, val):
        self._is_pc = bool(val)

    def set_is_ct(self, val):
        self._is_ct = bool(val)

    def set_is_sc(self, val):
        self._is_sc = bool(val)

    def is_pc(self):
        return self._is_pc

    def is_ct(self):
        return self._is_ct

    def is_sc(self):
        return self._is_sc 

    def set_total_volume_curve(self, total_volume_curve):
        self._total_volume_curve = total_volume_curve

    def total_volume_curve(self):
        return self._total_volume_curve

    def add_volume_attribute(self, attribute, curve):
        self.add_attribute(attribute)
        self._volume_attribute_dict[attribute.species_code()] = attribute
        #self.update_total_volume_curve(curve)
        
    def add_attribute(self, attribute):
        self._attribute_dict[attribute.key()] = attribute
        self._attribute_id_list.append(attribute.key())

    def remove_total_volume_curve(self):
        self._total_volume_curve = None

    def update_total_volume_curve(self, curve):
        import copy
        tvc = self._total_volume_curve
        if not tvc:
            tvc = Curve(id='%s.tvc' % self._id)
        self._total_volume_curve = Curve()
        c = curve
        al1 = c.age_list()
        al2 = tvc.age_list()
        min_age = al1[0]
        if al2:
            min_age = min(min_age, al2[0])
        al1.reverse()
        al2.reverse()
        max_age = al1[0]
        #print 'xxx', min_age, max_age
        if al2:
            max_age = max(max_age, al2[0])
        for x in range(min_age, max_age+1, 5):
            y = tvc.value(x) + c.value(x)
            #print x, y
            self._total_volume_curve.add_point(x, y)
        #print 'xxx'
        #print '\n'.join(self._total_volume_curve.dump_xml())

        if self.__debug:
            print '\n'.join(curve.dump_xml())
            print '%s.tvc' % self._id
            print '\n'.join(self._total_volume_curve.dump_xml())
                
    def attribute(self, id):
        result = None
        if id in self._attribute_dict:
            result = self._attribute_dict[id]
        return result

    def attribute_list(self):
        # old code
        ##import copy
        ##return copy.copy(self._attribute_dict.values())
        
        # new code
        # build attribute list (same order as added)
        result = []
        for key in self._attribute_id_list:
            result.append(self._attribute_dict[key])
        return result

    def volume_attribute_list(self):
        #print self._attribute_list
        return [a for a in self._attribute_dict.values() if a.is_volume()]

    def remove_volume_attributes(self):
        self._attribute_id_list = filter((lambda key: not self._attribute_dict[key].is_volume()),
                                         self._attribute_id_list)
        self._attribute_dict = dict(filter((lambda item: not item[1].is_volume()),
                                           self._attribute_dict.items()))
        self._volume_attribute_dict.clear()
        self._total_volume_curve = None

    def set_id(self, val):
        self._id = val

    def id(self):
        return self._id

    def description(self):
        return self._description
        

if __name__ == '__main__':
    # test code for FeatureStratum class

    from fmg.attribute import Attribute
    #from fmg.attributes import Attributes
    #reload(fmg.feature)
    c1 = Curve()
    c1.add_point(0, 0)
    c1.add_point(10, 100)
    c1.add_point(20, 200)
    c1.add_point(30, 100)
    c2 = Curve()
    c2.add_point(10, 100)
    c2.add_point(20, 200)
    c2.add_point(30, 100)
    c2.add_point(40, 0)
    a1 = Attribute('volume1', is_volume=True, species_code='xxx', future=88, curve=c1)
    a2 = Attribute('volume2', is_volume=True, species_code='yyy', future=88, curve=c2)
    a3 = Attribute('notvolume', is_volume=False, future=99)
    ##aa = Attributes('attributes.label')
    
    fs = FeatureStratum('featurestratum.id')
    fs.add_attribute(a1, c1)
    fs.add_attribute(a2, c2)
    fs.add_attribute(a3, Curve())

    print 'total volume curve'
    print '\n'.join(fs.total_volume_curve().dump_xml())
    print
    print 'before rremove_volume_attributes()'
    print 'attribute id list\t%s' %fs._attribute_id_list
    print 'attribute dict\t\t%s' % fs._attribute_dict
    print 'species list\t\t%s' % fs.species_list()
    for key in fs._attribute_id_list:
        print '\n'.join(fs._attribute_dict[key].dump_xml())
    #for a in fs.attribute_list():
    #    print '\n'.join(a.dump_xml())

    fs.remove_volume_attributes()

    print
    print 'after rremove_volume_attributes()'
    print 'attribute id list\t%s' %fs._attribute_id_list
    print 'attribute dict\t\t%s' % fs._attribute_dict
    print 'species list\t\t%s' % fs.species_list()
    for a in fs.attribute_list():
        print '\n'.join(a.dump_xml())

    #print
    #print '\n'.join(fs.total_volume_curve().dump_xml())
