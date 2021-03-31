
from fmg.output import Output
from fmg.treatment import Treatment
from fmg.select import Select
from fmg.retention import Retention
from fmg.assign import Assign
from fmg.featurestratum import FeatureStratum
from fmg.productstratum import ProductStratum
from fmg.attribute import Attribute
from fmg.attributes import Attributes
from fmg.expression import Expression
from fmg.curve import Curve
from fmg.productdistribution import ProductDistribution
from fmg.define import Define
from collections import deque

import copy
import re
import sys

class ForestModel:
    """
    ForestModel element data class
    
    Treatment type codes:
    PC : pre-commercial
    CT : commercial thinning
    SC : species commercial
    FC : final cut
    """ 
    #_treatment_type_sequence = ["PL", "PCT", "CT", "SC", "FC"]

    _max_age = 400
    _description_default = ""
    _match_default = "multi"
    _fuzzage_default = 5
    _fuzzpct_default = 1000
    _maxsuccession_default = 10
    _maxrotation_default = 3    
    _fu_fieldname_default = Treatment._fu_fieldname_default
    _invasion_default = False
    _periodlength_default = 5
    _woodstock_max_lifespan = 1000
    
    def __init__(self,
                 horizon,
                 year,
                 description=_description_default,
                 match=_match_default,
                 fuzzage=_fuzzage_default,
                 fuzzpct=_fuzzpct_default,
                 maxsuccession=_maxsuccession_default,
                 maxrotation=_maxrotation_default,
                 output = Output(),
                 fu_fieldname=_fu_fieldname_default,
                 invasion=_invasion_default,
                 periodlength=_periodlength_default):
        self._horizon = horizon
        self._year = year
        self._periodlength = periodlength
        self._input_element = None
        self._description = description
        self._match = match
        self._fuzzage = fuzzage
        self._fuzzpct = fuzzpct
        self._maxsuccession = maxsuccession
        self._maxrotation = maxrotation
        self._output_element = output
        self._fu_fieldname = fu_fieldname
        self._invasion = invasion
        self._define_dict = {}
        self._curve_dict = {}
        self._expression_dict = {}
        self._attribute_dict = {}
        #self._attribute_list = []
        self._attributes_dict = {}
        self._attributes_list = []
        self._treatment_dict = {}
        self._retention_stratum_dict = {}
        self._succession_stratum_dict = {}
        self._feature_stratum_dict = {}
        self._treatment_stratum_dict = {}
        self._product_stratum_dict = {}
        self._feature_stratum_transition_dict = {}
        self._product_attribute_dict = {}
        self._select_dict = {}
        self._xml_lines = []
        self._default_product_distribution_id = "default"
        self._product_distribution_dict = {"default":ProductDistribution("default")}
        self._feature_stratum_id_filter_list = []
        unitycurve = Curve(id="unity")
        unitycurve.add_point(0, 1)
        self.add_curve(unitycurve)
        self._species_group_dict = {}
        self._species_code_list = []
        self._hack_list = []
        self._retention_select_deque = deque()
        self._succession_select_deque = deque()
        self._feature_select_deque = deque()
        self._track_select_deque = deque()
        self._track_select_dict = {}
        self._product_select_deque = deque()
        self._general_select_deque = deque()
        self._processed_track_set = set()
        self._base_curve_dict = {}
        self._skip_null_curves = False
        self._track_filter_set = set()
        
        # new Woodstock stuff...
        self._woodstock_constants_dict = {}
        self._woodstock_landscape_list = []
        self._woodstock_landscape_dict = {}
        self._woodstock_landscape_aggregate_dict = {}
        self._woodstock_action_aggregate_dict = {}

    def has_commercialthinning(self):
        for t in self._treatment_dict.values():
            if t.is_commercialthinning(): return True
        return False

    def set_periodlength(self, val):
        self._periodlength = val

    def periodlength(self):
        return self._periodlength

    def add_track_filter(self, treatment_stratum_id, feature_stratum_id):
        self._track_filter_set.add((treatment_stratum_id, feature_stratum_id))

    def set_skip_null_curves(self, val):
        self._skip_null_curves = val

    def skip_null_curves(self, val):
        return self._skip_null_curves

    def set_base_curve(self, species_code, curve):
        self._base_curve_dict[species_code] = curve
        self.add_curve(curve)

    def base_curve(self, species_code):
        return self._base_curve_dict[species_code]

    def set_invasion(self, invasion):
        self._invasion = invasion

    def invasion(self):
        return self._invasion

    def add_retention_select(self, select, front=False):
        if not front:
            self._retention_select_deque.append(select)
        else:
            self._retention_select_deque.appendleft(select)
        
    def add_succession_select(self, select, front=False):
        if not front:
            self._succession_select_deque.append(select)
        else:
            self._succession_select_deque.appendleft(select)
        
    def add_feature_select(self, select, front=False):
        if not front:
            self._feature_select_deque.append(select)
        else:
            self._feature_select_deque.appendleft(select)
        
    def add_track_select(self, select, front=False):
        if not front:
            self._track_select_deque.append(select)
        else:
            self._track_select_deque.appendleft(select)
        self._track_select_dict[select.statement()] = select
        
    def add_product_select(self, select, front=False):
        if not front:
            self._product_select_deque.append(select)
        else:
            self._product_select_deque.appendleft(select)
        
    def add_general_select(self, select, front=False):
        if not front:
            self._general_select_deque.append(select)
        else:
            self._general_select_deque.appendleft(select)

    def add_hack(self, hack):
        self._hack_list.append(hack)

    def has_hack(self, hack):
        #print self._hack_list
        if hack in self._hack_list:
            return True
        else:
            return False

    def add_product_attribute(self,
                              feature_stratum_id=None,
                              treatment_stratum_id=None,
                              treatment_id=None,
                              attribute=None):
        #if __debug__:
        #    if attribute.expression().id() == "harvestcost.irreg":
        #        print feature_stratum_id, treatment_stratum_id, treatment_id
        key = (feature_stratum_id, treatment_stratum_id, treatment_id)
        if key not in self._product_attribute_dict:
                self._product_attribute_dict[key] = []
        if attribute.force_local():
            self._product_attribute_dict[key].append(attribute)
        else:
            self.add_attribute(attribute)
            self._product_attribute_dict[key].append(Attribute(label=attribute.label(),
                                                                   id=attribute.id(),
                                                                   is_ref=True))

    def set_species_group(self, species_group, species_code, group_code):
        if species_group not in self._species_group_dict:
            self._species_group_dict[species_group] = {}
        self._species_group_dict[species_group][species_code] = group_code
        if species_code not in self._species_code_list:
            self._species_code_list.append(species_code)
            self._species_code_list.sort()

    def species_group_list(self):
        keys = self._species_group_dict.keys()
        keys.sort()
        return keys

    def species_code_list(self):
        return self._species_code_list

    def species_group(self, species_group, species_code):
        return self._species_group_dict[species_group][species_code]
        
    def group_species_list(self, species_group, group_code):
        l = []
        for s in self._species_group_dict[species_group]:
            if self._species_group_dict[species_group][s] == group_code: 
                l.append(s)
        return l
        
    def has_attribute(self, a):
        return a.id() in self.attribute_id_list()
        
    def has_expression(self, e):
        return e.id() in self.expression_id_list()
        
    def has_curve(self, c):
        return c.id() in self.curve_id_list()
         
    def has_curve_id(self, cid):
        return cid in self.curve_id_list()
         
    def add_select(self, select):
        self._select_dict[select.statement()] = select

    def select(self, statement):
        return self._select_dict[statement]

    def select_statement_list(self):
        return self._select_dict.keys()

    def max_age(self):
        return self._max_age

    #def update_total_volume_curve(self, featurestratum):
    #    featurestratum.remove_total_volume_curve()
    #    for a in featurestratum.volume_attribute_list():
    #        featurestratum.update_total_volume_curve(self.resolve_to_curve(a))

    def total_volume_curve(self, feature_stratum_id):
        c = Curve()
        c.add_point(0, 0.0)
        fs = self.feature_stratum(feature_stratum_id)
        for a in fs.volume_attribute_list():
            c += self.resolve_to_curve(a)
        return c

    def total_volume_curve2(self, featurestratum):
        # build list of volume attributes
        alist1 = [] # volume attribute objects
        for a in featurestratum.attribute_list():
            
            if a.is_volume():
                #print "zzz", a.id(), a.label(), a.is_volume()
                if a.is_group():
                    afactor = a.factor()
                    while a.is_ref():
                        a = self.attributes(a.id())
                        afactor *= a.factor()
                    for aa in a.attribute_list():
                        aafactor = aa.factor()
                        while aa.is_ref():
                            aa = self.attribute(aa.id())
                            aafactor *= aa.factor()
                        aa = copy.deepcopy(aa)
                        aa.set_factor(afactor * aafactor)
                        alist1.append(aa)
                else:
                    afactor = a.factor()
                    #if __debug__:
                    #    foo = self.attribute(a.id())
                    #    print "tvc", a.id(), a.is_ref(), a.dump_xml()
                    #    print "tvc", foo.id(), foo.is_ref(), foo.curve(), foo.curve().id(),
                    #    print "foo.curve().dump_xml()", foo.curve().dump_xml()
                        
                        
                    while a.is_ref():
                        #if __debug__:
                        #    print "tvc", a.id(), a.is_volume(), a.is_ref()
                        #    print self._attribute_dict[a.id()].dump_xml()
                        #    print self.attribute(a.id()).dump_xml()
                        a = self.attribute(a.id())
                        afactor *= a.factor()
                    #print "yyy", a.id(), a.label(), a.is_volume()
                    aa = copy.deepcopy(a)
                    alist1.append(aa)
        if not alist1:
            return None
        c = Curve(id="tvc-%s" % featurestratum.id()) # total volume curve
        clist = [] # list of volume curve objects
        alist2 = [] # list of attribute objects that use expressions (instead of curves)
        for a in alist1:
            factor = a.factor()
            if a.curve():
                cc = a.curve()
                while cc.is_ref():
                    cc = self.curve(cc.id())
                cc = copy.deepcopy(cc)
                cc.set_factor(a.factor())
                clist.append(cc)
            else:
                # assume expression instead of curve
                alist2.append(a)
        for x in range(1, self._max_age, 1):
            y = 0.0
            for cc in clist:
                y += float(cc.value(x)) * cc.factor()
            for a in alist2:
                #if __debug__: # and a.expression().id() == "harvestcost.irreg":
                #    print "tvc1", featurestratum.id(), a.id(), a.label(), a.is_volume()
                #    for foo in alist1:
                #        print "alist1", foo.id(), foo.label(), foo.is_volume()
                #    for foo in alist2:
                #        print "alist2", foo.id(), foo.label(), foo.is_volume()
                y += float(self.eval_expression(a.expression().statement(), x)) * a.factor()
            c.add_point(x, y)
        # remove repeated values from left of curve
        last_x = -1
        last_y = c.value(last_x)
        for x in range(0, self.max_age(), 1):
            y = c.value(x)
            if y == last_y:
                c.remove_point(last_x)
                last_x = x
                last_y = y
            else:
                break
        # remove repeated values from right of curve
        last_x = self.max_age()
        last_y = c.value(last_x)
        for x in range(self.max_age(), 0, -1):
            y = c.value(x)
            if y == last_y:
                c.remove_point(last_x)
                last_x = x
                last_y = y
            else:
                break
        c.update_ages()

        #if __debug__:
        #    if c:
        #        print "\n".join(c.dump_xml())
        #if __debug__:
        #    print "done tvc"

        return c

    def add_treatment(self, treatment):
        self._treatment_dict[treatment.id()] = treatment

    def add_treatment_species_code(self, treatment_id, species_code):
        self.treatment(treatment_id).add_species_code(species_code)
        #print "adding species:", treatment_id, species_code, self.treatment(treatment_id).species_code_list() # debug

    def treatment_species_code_list(self, treatment_id):
        return self.treatment(treatment_id).species_code_list()

    def treatment_id_list(self):
        return self._treatment_dict.keys()

    def treatment(self, treatment_id):
        tmp = None
        if treatment_id in self._treatment_dict:
            tmp = self._treatment_dict[treatment_id]
        return tmp

    def add_retention_stratum(self, retention_stratum):
        self._retention_stratum_dict[retention_stratum.id()] = retention_stratum

    def retention_stratum_id_list(self):
        return self._retention_stratum_dict.keys()

    def retention_stratum(self, id):
        tmp = None
        if id in self._retention_stratum:
            tmp = self._retention_stratum_dict[id]
        return tmp

    def add_succession_stratum(self, succession_stratum):
        self._succession_stratum_dict[succession_stratum.id()] = succession_stratum

    def succession_stratum_id_list(self):
        return self._succession_stratum_dict.keys()

    def succession_stratum(self, id):
        tmp = None
        if id in self._succession_stratum:
            tmp = self._succession_stratum_dict[id]
        return tmp

    def add_feature_stratum_id_filter(self, id):
        self._feature_stratum_id_filter_list.append(id)

    def add_feature_stratum(self, feature_stratum):
        if self._feature_stratum_id_filter_list and feature_stratum.id() not in self._feature_stratum_id_filter_list: return
        self._feature_stratum_dict[feature_stratum.id()] = feature_stratum

    def feature_stratum_id_list(self):
        return self._feature_stratum_dict.keys()

    def feature_stratum(self, id):
        tmp = None
        if id in self._feature_stratum_dict:
            tmp = self._feature_stratum_dict[id]
        return tmp

    def add_treatment_stratum(self, treatment_stratum):
        self._treatment_stratum_dict[treatment_stratum.id()] = treatment_stratum

    def treatment_stratum_id_list(self):
        return self._treatment_stratum_dict.keys()

    def add_feature_stratum_transition(self,
                                       treatment_id,
                                       from_feature_stratum_id,
                                       to_feature_stratum_id):
        
        self._feature_stratum_transition_dict[(treatment_id, from_feature_stratum_id)] = to_feature_stratum_id

    def feature_stratum_transition(self, treatment_id, from_feature_stratum_id):
        result = None
        key = (treatment_id, from_feature_stratum_id)
        if key in self._feature_stratum_transition_dict:
            result = self._feature_stratum_transition_dict[key]
        return result

    def treatment_stratum(self, id):
        tmp = None
        if id in self._treatment_stratum_dict:
            tmp = self._treatment_stratum_dict[id]
        return tmp
    
    def add_product_stratum(self, product_stratum):
        self._product_stratum_dict[product_stratum.id()] = product_stratum

    def product_stratum_id_list(self):
        return self._product_stratum_dict.keys()

    def product_stratum(self, id):
        tmp = None
        if id in self._product_stratum_dict:
            tmp = self._product_stratum_dict[id]
        return tmp

    def add_define(self, define):
        self._define_dict[define.field()] = define

    def set_input_element(self, input):
        self._input_element = input

    def input_element(self):
        return self._input_element

    def output_element(self):
        return self._output_element
    
    def set_description(self, description):
        self._description = str(description)
        
    def set_match(self, match):
        if str(match) in ["multi", "solo"]:
            self._match = str(match)

    def match(self):
        return self._match
        
    def set_fuzzage(self, fuzzage):
        self._fuzzage = int(fuzzage)

    def fuzzage(self):
        return self._fuzzage
        
    def set_fuzzpct(self, fuzzpct):
        self._fuzzpct = int(fuzzpct)

    def fuzzpct(self):
        return self._fuzzpct
        
    def set_maxsuccession(self, maxsuccession):
        self._maxsuccession = int(maxsuccession)

    def maxsuccession(self):
        return self._maxsuccession
        
    def set_maxrotation(self, maxrotation):
        self._maxrotation = int(maxrotation)

    def maxrotation(self):
        return self._maxrotation
        
    def add_curve(self, curve):
        
        if __debug__ and not curve.id():
            print "ForestModel.add_curve() failed for curve:"
            print "\n".join(curve.dump_xml())
            
        assert curve.id() # reference curve must have id
        self._curve_dict[curve.id()] = curve
        
    def curve_id_list(self):
        return self._curve_dict.keys()

    def add_expression(self, expression):
        assert expression.id() # reference expression must have id
        #if __debug__:
        #    print expression.id()
        #    print expression.dump_xml()
        self._expression_dict[expression.id()] = expression
        
    def expression_id_list(self):
        return self._expression_dict.keys()

    def expression(self, id):
        tmp = None
        if id in self._expression_dict:
            tmp = self._expression_dict[id]
        return tmp

    def add_product_distribution(self, pd):
        self._product_distribution_dict[pd.id()] = pd
        for sc in pd.species_code_list():
            for pc in pd.product_code_list():
                self.add_curve(pd.curve(sc, pc))

    def product_distribution_id_list(self):
        return self._product_distribution_dict.keys()

    def product_distribution(self, id):
        if id in self._product_distribution_dict:
            return self._product_distribution_dict[id]
        else:
            return self._product_distribution_dict[self._default_product_distribution_id]

    def curve_dict(self):
        return self._curve_dict

    def curve(self, id):
        tmp = None
        if id in self._curve_dict:
            tmp = self._curve_dict[id]
        return tmp

    def attribute_id_list(self):
        return self._attribute_dict.keys()

    def add_volume_attribute(self, feature_stratum_id, attribute):
        fs = self.feature_stratum(feature_stratum_id)
        curve = self.resolve_to_curve(attribute)
        fs.add_volume_attribute(attribute, curve)
        
    def add_attribute(self, attribute):
        assert attribute.id() # reference attribute must have id
        #index = len(self._attribute_dict)
        #self._attribute_list.append(attribute)
        #self._attribute_dict[attribute.id()] = index
        self._attribute_dict[attribute.id()] = attribute

    def attribute(self, id):
        tmp = None
        if id in self._attribute_dict:
            tmp = self._attribute_dict[id]
            #tmp = self._attribute_list[self._attribute_dict[id]]
        return tmp

    def attributes_id_list(self):
        return self._attributes_dict.keys()    
                
    def add_attributes(self, attributes):
        assert attributes.id() # reference attributes must have id
        index = len(self._attributes_dict)
        self._attributes_list.append(attributes)
        self._attributes_dict[attributes.id()] = index

    def attributes(self, id):
        tmp = None
        if id in self._attributes_dict:
            tmp = self._attributes_list[self._attributes_dict[id]]
        return tmp

    def set_name(self, name):
        self._name = name

    def name(self):
        return self._name

    def set_path(self, path):
        self._path = path

    def path(self):
        return self._path

    def write(self, lines, suffix):
        if suffix:
            ofname = "%(path)s/%(name)s-%(suffix)s.xml" \
            % {"path":self._path,
               "name":self._name,
               "suffix":suffix}
        else:
            ofname = "%(path)s/%(name)s.xml" \
            % {"path":self._path,
               "name":self._name}            
        of = open(ofname, "w")
        of.writelines(lines)
        of.close()

    def dump_xml(self):
        # todo: move XML comments here
        self._xml_lines = []
        head_lines = self._dump_xml_head()
        input_lines = self._dump_xml_input()
        output_lines = self._dump_xml_output()
        define_lines = self._dump_xml_define()
        retention_lines = self._dump_xml_retention()
        succession_lines = self._dump_xml_succession()
        track_lines = self._dump_xml_track()#(self._treatment_stratum_dict, self._feature_stratum_dict)
        #print "self._features_stratum_dict", self._features_stratum_dict
        feature_lines = self._dump_xml_feature()
        # process attribute and attributes sections after tracks (new CT reference attributes)
        attribute_lines = self._dump_xml_attribute()
        attributes_lines = self._dump_xml_attributes()
        product_lines = self._dump_xml_product()
        select_lines = self._dump_xml_select()
        curve_lines = self._dump_xml_curve()
        tail_lines = self._dump_xml_tail()

        self._xml_lines.extend(head_lines)
        head_lines = None
        self._xml_lines.extend(input_lines)
        input_lines = None
        self._xml_lines.extend(output_lines)
        output_lines = None
        self._xml_lines.extend(define_lines)
        define_lines = None
        self._xml_lines.extend(curve_lines)
        curve_lines = None
        self._xml_lines.extend(attribute_lines)
        attribute_lines = None
        self._xml_lines.extend(attributes_lines)
        attributes_lines = None
        self._xml_lines.extend(retention_lines)
        retention_lines = None
        self._xml_lines.extend(succession_lines)
        succession_lines = None
        self._xml_lines.extend(feature_lines)
        feature_lines = None
        self._xml_lines.append("<!-- dump track 'select' elements -->")
        self._xml_lines.extend(track_lines)
        track_lines = None
        self._xml_lines.extend(product_lines)
        product_lines = None
        self._xml_lines.extend(select_lines)
        select_lines = None        
        self._xml_lines.extend(tail_lines)
        tail_lines = None

        return self._xml_lines


    def dump_xml2(self):
        lines = []
        # todo: move XML comments here
        #self._xml_lines = []
        lines.append("""<?xml version="1.0" encoding="ISO-8859-1"?>""")

        entitydecl = "<!ENTITY curves SYSTEM %(name)s-curves.xml>"\
                     "<!ENTITY attributes SYSTEM %(name)s-attributes.xml>"\
                     % {"name":self.name()}
        #doctype = """<!DOCTYPE ForestModel PUBLIC "ForestModel" "http://www.spatial.ca/ForestModel.dtd" [%s]>""" \
        #                % entitydecl
        doctype = """<!DOCTYPE ForestModel PUBLIC "ForestModel" "http://www.spatial.ca/ForestModel.dtd">"""
        lines.append(doctype)

        head_lines = self._dump_xml_head()
        input_lines = self._dump_xml_input()
        output_lines = self._dump_xml_output()
        define_lines = self._dump_xml_define()
        retention_lines = self._dump_xml_retention()
        succession_lines = self._dump_xml_succession()
        track_lines = self._dump_xml_track2()#(self._treatment_stratum_dict, self._feature_stratum_dict)
        #print "track_lines", len(track_lines)
        feature_lines = self._dump_xml_feature()
        # process attribute and attributes sections after tracks (new CT reference attributes)
        attribute_lines = self._dump_xml_attribute()
        attributes_lines = self._dump_xml_attributes()
        product_lines = self._dump_xml_product()
        select_lines = self._dump_xml_select()
        curve_lines = self._dump_xml_curve()
        tail_lines = self._dump_xml_tail()

        self._xml_lines.extend(head_lines)
        head_lines = None
        self._xml_lines.extend(input_lines)
        input_lines = None
        self._xml_lines.extend(output_lines)
        output_lines = None
        self._xml_lines.extend(define_lines)
        define_lines = None
        self._xml_lines.extend(curve_lines)
        curve_lines = None
        self._xml_lines.extend(attribute_lines)
        attribute_lines = None
        self._xml_lines.extend(attributes_lines)
        attributes_lines = None
        self._xml_lines.extend(retention_lines)
        retention_lines = None
        self._xml_lines.extend(succession_lines)
        succession_lines = None
        self._xml_lines.extend(feature_lines)
        feature_lines = None
        self._xml_lines.append("<!-- dump track 'select' elements -->")
        self._xml_lines.extend(track_lines)
        track_lines = None
        self._xml_lines.extend(product_lines)
        product_lines = None
        self._xml_lines.extend(select_lines)
        select_lines = None        
        self._xml_lines.extend(tail_lines)
        tail_lines = None

        return self._xml_lines

    def _dump_xml_head(self):
        lines = []
        lines.append("""<?xml version="1.0" encoding="ISO-8859-1"?>""")
        lines.append("""<!DOCTYPE ForestModel PUBLIC "ForestModel" "http://www.spatial.ca/ForestModel.dtd">""")
        tmp = """<ForestModel horizon="%(horizon)s" year="%(year)s" """ \
              % {"horizon":self._horizon, "year":self._year}
        if self._description:
            tmp += """description="%s" """ % self._description
        if self._match != self._match_default:
            tmp += """match="%s" """ % self._match
        if self._fuzzage != self._fuzzage_default:
            tmp += """fuzzage="%s" """ % self._fuzzage
        if self._fuzzpct != self._fuzzpct_default:
            tmp += """fuzzpct="%s" """ % self._fuzzpct
        if self._maxsuccession != self._maxsuccession_default:
            tmp += """maxsuccession="%s" """ % self._maxsuccession
        if self._maxrotation != self._maxrotation_default:
            tmp += """maxrotatio="%s" """ % self._maxrotation
        tmp += ">"
        lines.append(tmp)
        return lines
        
    def _dump_xml_input(self):
        lines = []
        lines.extend(self._input_element.dump_xml())
        return lines
                
    def _dump_xml_output(self):
        lines = []
        lines.extend(self._output_element.dump_xml())
        return lines
        
    def _dump_xml_define(self):
        lines = []        
        tid_list = ["none"]
        tintensity_list = ["0.0"]
        tfuture_list = ["0.0"]
        for tid in self.treatment_id_list():
            tid_list.append(tid)
            tintensity_list.append(str(self.treatment(tid).intensity()))
            tfuture_list.append(str(self.treatment(tid).future()))
            if self.treatment(tid).is_finalcut():
                tid_list.append(tid+"-ext")
                tintensity_list.append(str(self.treatment(tid).intensity()))
                tfuture_list.append(str(self.treatment(tid).future()))
        tid_string = ",".join(tid_list)
        tid_string = "'%s'" % tid_string
        self.add_define(Define("treatment_id_list", tid_string, is_constant=True))
        tintensity_string = ",".join(tintensity_list)
        tintensity_string = "'%s'" % tintensity_string
        self.add_define(Define("treatment_intensity_list", tintensity_string, is_constant=True))
        tfuture_string = ",".join(tfuture_list)
        tfuture_string = "'%s'" % tfuture_string
        self.add_define(Define("treatment_future_list", tfuture_string, is_constant=True))
        lines.append("<!-- dump 'define' elements -->")
        for key in self._define_dict.keys():
            define = self._define_dict[key]
            lines.extend(define.dump_xml())
        return lines

    def _dump_xml_curve(self):
        lines = []
        if self._curve_dict:
            lines.append("<!-- dump reference 'curve' elements -->")
            keys = self._curve_dict.keys()
            keys.sort()
            for key in keys:
                #if __debug__:
                #    print key
                #    #print "\n".join(tvc.dump_xml())
                c = self.curve(key)
                if self._skip_null_curves and c.is_null(): continue
                lines.extend(c.dump_xml())
        return lines

    def _dump_xml_attribute(self):
        lines = []
        if self._attribute_dict:
            lines.append("<!-- dump reference 'attribute' elements -->")
            #for attribute in self._attribute_list:
            for attribute in self._attribute_dict.values():
                lines.extend(attribute.dump_xml())
        return lines

    def _dump_xml_attributes(self):
        lines = []
        if self._attributes_dict:
            lines.append("<!-- dump reference 'attributes' elements -->")
            for attributes in self._attributes_list:
                lines.extend(attributes.dump_xml())
        return lines

    def _dump_xml_retention(self):
        lines = []
        lines.append("<!-- dump retention 'select' elements -->")
        for rsid in self._retention_stratum_dict:
            rs = self._retention_stratum_dict[rsid]
            statement ="retention_stratum_id eq '%s'" % rsid 
            s = Select(statement)
            #print rs.retention()
            s.set_retention(rs.retention())
            #s.set_retention(rs)
            lines.extend(s.dump_xml())
        return lines

    def _dump_xml_succession(self):
        lines = []
        lines.append("<!-- dump succession 'select' elements -->")
        for ssid in self._succession_stratum_dict:
            ss = self._succession_stratum_dict[ssid]
            statement = ""
            if ss.id():
                statement ="succession_stratum_id eq '%s'" % ss.id()
            s = Select(statement)
            s.set_succession(ss.succession())
            lines.extend(s.dump_xml())
        return lines

    def _dump_xml_feature(self):
        lines = []
        lines.append("<!-- dump feature 'select' elements -->")
        for fsid in self._feature_stratum_dict:
            
            #if __debug__:
            #    print "dumping fsid", fsid

            fs = self._feature_stratum_dict[fsid]
            statement ="feature_stratum_id eq '%s'" % fs.id()
            s = Select(statement)
            for a in fs.attribute_list():
                s.add_feature_attribute(a)
            lines.extend(s.dump_xml())
        return lines

    def resolve_to_curve(self, a):
        assert a.is_volume()
        factor = a.factor()
        c = None
        while a.is_ref():
            a = self.attribute(a.id())
        if a.curve():
            c = a.curve()
            while c.is_ref():
                c = self.curve(c.id())
            c = copy.deepcopy(c)
            #if __debug__:
            #    print "yyy", c.dump_xml()
            c.set_factor(c.factor() * a.factor())
        elif a.expression():
            # assume expression
            c = Curve()
            for x in range(0, self._max_age, 5):
                y = float(self.eval_expression(a.expression().statement(), x)) * a.factor()
                c.add_point(x, y)
                
        if not c:
            print "ForestModel.resolve_to_curve() failed for attribute:"
            print "\n".join(a.dump_xml())

        return c

#     def _dump_xml_track(self):#, ts_dict, fs_dict):
#         lines = []
#         for tsid in self._treatment_stratum_dict:
#             ts = self._treatment_stratum_dict[tsid]
#             for fsid in self._feature_stratum_dict:
#                 ############################################################
#                 # todo:
#                 #     add fu_fieldname to statement
#                 #     (conditional on fu dependency defined for treatment)
#                 ############################################################
#                 fs1 = self._feature_stratum_dict[fsid]
#                 statement_base = "status in managed and treatment_stratum_id eq '%(tsid)s' " \
#                                  "and feature_stratum_id eq '%(fsid)s'" \
#                                  % {"tsid":tsid, "fsid":fsid}
#                 tmp3 = [] # list of Select objects

#                 mrt_list = []
#                 s = Select(statement_base)
#                 ss = None
#                 for tl in ts.treatment_label_list():
#                     t = ts.treatment(tl)
#                     if t.is_finalcut():
#                         s.add_treatment(copy.deepcopy(t))
#                         if t.force_extensive() and len(ts.treatment_label_list()) > 1:
#                             t_ext = copy.deepcopy(t)
#                             t_ext.set_extensive(True)
#                             t_ext.set_label(t.label() + "-ext")
#                             t_ext.set_id(t.id() + "-ext")
#                             if t.init_extensive():
#                                 # extensive treatment only available if first treatment in horizon
#                                 ss = copy.deepcopy(s)
#                                 s.set_statement("%s and previous_treatment_id eq 'init'" % statement_base)
#                             s.add_treatment(t_ext)
#                     elif t.is_commercialthinning() or t.is_speciescut() or t.is_precommercial():
#                         mrt_list.append(t)
#                     else:
#                         s.add_treatment(copy.deepcopy(t))
#                 tmp3.append(s)
#                 if ss:
#                     tmp3.append(ss)
#                 # process list of select objects
#                 for s in tmp3:
#                     # process treatments in this track
#                     l1 = [] # list of finalcut type treatments
#                     l2 = [] # list of other treatments
#                     for t in s.treatment_list():
#                         if not fs1.total_volume_curve():
#                             #tvc = self.total_volume_curve(fs1)
#                             #fs1.set_total_volume_curve(tvc)
#                             fs1.set_total_volume_curve(self.total_volume_curve(fs1))
#                         tvc = fs1.total_volume_curve()
#                         if not tvc: continue
#                         if tvc.id() not in self.curve_id_list():
#                             self.add_curve(tvc)
#                             #if __debug__:
#                             #    print "\n".join(self.curve(tvc.id()).dump_xml())
#                             #    print self._curve_dict.keys()
#                             #    assert tvc.id() in self.curve_id_list()
#                         if not t.is_special():
#                             for mrt in mrt_list:
#                                 if t.is_extensive() and not mrt.force_extensive(): continue
#                                 t.add_midrotation_treatment(mrt)
#                                 if mrt.is_precommercial():
#                                     t.set_label(t.label()+"_"+mrt.label())         
#                                 else:
#                                     t.set_label(mrt.label()+"_"+t.label())
#                                     mrt.update_operability_limits(tvc)
#                         t.update_operability_limits(tvc)
#                         psid = "%(tsid)s.%(fsid)s.%(tid)s" % {"tsid":tsid, "fsid":fsid, "tid":t.id()}
#                         if not self.product_stratum(psid):
#                             self.add_product_stratum(ProductStratum(id=psid,
#                                                                     treatment_stratum_id=tsid,
#                                                                     feature_stratum_id=fsid,
#                                                                     current_treatment_id=t.id()))
#                         ps = self.product_stratum(psid)
#                         t.add_produce_assign(Assign("product_stratum_id", psid))
#                         #t.add_produce_assign(Assign("treatment_stratum_id", tsid))
#                         #t.add_produce_assign(Assign("feature_stratum_id", fsid))
#                         t.add_produce_assign(Assign("current_treatment_id", t.id()))
#                         if t.midrotation_harvest_treatment():
#                             mrtid = t.midrotation_harvest_treatment().id()
#                         else:
#                             mrtid = "none"
#                         t.add_produce_assign(Assign("midrotation_harvest_treatment_id", mrtid))
#                         t.add_transition_assign(Assign("previous_treatment_id", t.id()))
#                         self._update_product_attribute_list(t, fs1, ts, ps)

#                         # only assign feature stratum transition if not set yet (otherwise assume set at treatment level)
#                         # ??? maybe condition should be the other way around (ForestModel transition overrides Treatment transition) ??? 
#                         if not t.feature_stratum_transition() and (t.id(),fsid) in self._feature_stratum_transition_dict:
#                             t.set_feature_stratum_transition(self._feature_stratum_transition_dict[(t.id(),fsid)])

#                         if t.type_code() == "SC":
#                             # generate product stratum for final cut following species-specific partial cut (type SC)
#                             # (suppress product volumes for species targeted during partial cut)
#                             for t_scfc in s.treatment_list():
#                                 if t_scfc.type_code() != "FC": continue
#                                 psid_scfc = "%(fsid)s.%(tid)s_%(tscfcid)s" % {"fsid":fsid, "tid":t.id(), "tscfcid":t_scfc.id()}
#                                 if not self.product_stratum(psid_scfc):
#                                     self.add_product_stratum(ProductStratum(psid_scfc))
#                                 else:
#                                     continue
#                                 ps_scfc = self.product_stratum(psid_scfc)
#                                 for va in self._generate_product_volume_attribute_list(t_scfc, fs1, ps_scfc):
#                                     if va.species_code() not in t.species_code_list():
#                                         ps_scfc.add_attribute(va)
#                         elif t.type_code() == "CT":
#                             # special processing for commercial thinning treatuements (type CT)                            
#                             # append _CT to old id to create new id
#                             fs2 = FeatureStratum("%s_CT" % fs1.id(),
#                                                  description="%s post-CT" % fs1.id(),
#                                                  is_ct=True)
#                             for a in fs1.attribute_list():
#                                 if not a.is_volume():
#                                     # add non-volume attributes unchanged
#                                     fs2.add_attribute(a)
#                                 else:
#                                     # Subtract constant v from volume attributes.
#                                     # Define v as volume removed during CT when 
#                                     # treatment scheduled exactly in
#                                     # middle of operability window.
#                                     age = t.minage() + ((t.maxage() - t.minage()) * 0.5)
#                                     tmp101 = []
#                                     if a.is_group():
#                                         for aa in self.attributes(a.id()).attribute_list():
#                                             tmp101.append(aa)
#                                     else:
#                                         tmp101.append(a)
#                                     for aa in tmp101:
#                                         tmp102 = aa
#                                         while tmp102.is_ref(): tmp102 = self.attribute(tmp102.id())
#                                         tmp103 = 0 # value of expression or curve at age
#                                         if tmp102.expression():
#                                             tmp103 = self.eval_expression(tmp102.expression().statement(), age)
#                                         else:
#                                             # assume curve
#                                             tmp103 = self.curve(tmp102.curve().id()).value(age)
#                                         v = tmp103 * aa.factor() * t.intensity()
#                                         tmpid = aa.id().strip()+"_CT"
#                                         if not self.attribute(tmpid):
#                                             aaa = Attribute(label=aa.label(),
#                                                             id=tmpid,
#                                                             expression=Expression("attributeid('%(aaid)s') - %(v)s"
#                                                                                   % {"aaid":aa.id(), "v":v}),
#                                                             is_volume=True)
#                                             self.add_attribute(aaa)
#                                         aaa = Attribute(label=aa.label(),
#                                                         id=tmpid,
#                                                         is_volume=True,
#                                                         is_ref=True)
#                                         fs2.add_attribute(aaa)
                                    
#                             # add feature stratum transitions for FC treatments in fs2
#                             for tt in s.treatment_list():
#                                 if tt.type_code() == "FC":
#                                     self.add_feature_stratum_transition(tt.id(),
#                                                                         fs2.id(),
#                                                                         self.feature_stratum_transition(tt.id(), fs1.id()))
                            
#                             # build feature attribute select for new feature stratum
#                             statement = "feature_stratum_id='%s'" % fs2.id()
#                             ss = Select(statement)
#                             for aa in fs2.attribute_list():
#                                 ss.add_feature_attribute(aa)
#                             lines.extend(ss.dump_xml())
                            
#                             tsid2 = tsid
#                             if t.treatment_stratum_transition():
#                                 tsid2 = t.treatment_stratum_transition()
#                             ts2 = self.treatment_stratum(tsid2)
                            
#                             lines.extend(self._dump_xml_track({ts2.id():ts2},{fs2.id():fs2}))
                            
#                             # generate new product stratum
#                             for label in ts.treatment_label_list():
#                                 tt = self.treatment(ts.treatment(label).id())
#                                 if tt.type_code() == tt.finalcut_type_code():
#                                     # assume only FC after CT
#                                     psid2 = "%(fsid)s.%(tid)s" % {"fsid":fs2.id(), "tid":tt.id()}
#                                     psid3 = "%(fsid)s.%(tid)s" % {"fsid":fsid, "tid":tt.id()}
#                                     ps2 = self.product_stratum(psid2)
#                                     ps3 = self.product_stratum(psid3)
#                                     for psa in ps3.attribute_list():
#                                         if not psa.is_volume():
#                                             # only add non-volume attributes (volume attributes added elsewhere)
#                                             ps2.add_attribute(psa)
#                                             self.add_product_stratum(ps2)
#                             t.set_feature_stratum_transition(fs2.id())
#                     lines.extend(s.dump_xml())
#         return lines
    

    def _dump_xml_track2(self, show_progress=True):#, ts_dict, fs_dict):
        lines = []
        tsid_list = copy.copy(self._treatment_stratum_dict.keys())
        fsid_list = copy.copy(self._feature_stratum_dict.keys())
        if __debug__ and show_progress:
            import progressbar
            print "Processing tracks (pass 1 of 2)"
            p = progressbar.ProgressBar(maxval=len(fsid_list)).start()
            i = 0
        for fsid in fsid_list:
            if __debug__ and show_progress:
                p.update(i)
                i += 1
            fs = self.feature_stratum(fsid)
            if not fs.treatment_stratum_id():
                for tsid in tsid_list:
                    self.process_track(tsid, fsid)
            else:
                #print "fs.treatment_stratum_id()", fs.treatment_stratum_id()
                # special case (1:1 feature stratum to treatment stratum ratio)
                #self.process_track(fs.treatment_stratum_id(), fsid)
                for tsid in fs.treatment_stratum_id_list():
                    self.process_track(tsid, fsid)
        if __debug__ and show_progress:
            p.finish()
        tsid_list = copy.copy(self._treatment_stratum_dict.keys())
        fsid_list = copy.copy(self._feature_stratum_dict.keys())
        if __debug__ and show_progress:
            import progressbar
            print "Processing tracks (pass 2 of 2)"
            p = progressbar.ProgressBar(maxval=len(self._feature_stratum_dict)).start()
            i = 0
        for fsid in self._feature_stratum_dict:
            if __debug__ and show_progress:
                p.update(i)
                i += 1
            for tsid in self._treatment_stratum_dict:
                if not self.is_processed_track(tsid, fsid):
                    self.process_track(tsid, fsid)
        if __debug__ and show_progress:
            p.finish()
        for s in self._track_select_deque:
            lines.extend(s.dump_xml())
        return lines

    def is_processed_track(self, tsid, fsid):
        return (tsid, fsid) in self._processed_track_set

    def is_invasive(self, species_code):
        return self.species_group("invasion", species_code) in ["INV"]

    def generate_volume_attribute(self,
                                  feature_stratum,
                                  species,
                                  factor=1.0,
                                  base_curve=None):
        import re
        if base_curve:
            curve = Curve(id=base_curve.id(), is_ref=True)
            self.add_curve(base_curve)
        else:
            curve = None
        aid = "volume-%(fsid)s-%(species)s" % {"fsid":feature_stratum.id(), "species":species}   
        alabel = "%%f.volume.%%m.%s" % species
        # final harvest cost expression
        hce1 = copy.deepcopy(self.expression(feature_stratum.final_harvest_cost_expression_id()))
        hce1.set_statement(hce1.statement().replace("speciescode", species))
        hce1.set_id("%(eid)s.%(s)s" % {"eid":hce1.id(), "s":species})
        if not self.has_expression(hce1):
            self.add_expression(hce1)
        # partial harvest cost expression
        hce2 = copy.deepcopy(self.expression(feature_stratum.partial_harvest_cost_expression_id()))
        hce2.set_statement(hce2.statement().replace("speciescode", species))
        hce2.set_id("%(eid)s.%(s)s" % {"eid":hce2.id(), "s":species})
        if not self.has_expression(hce2):
            self.add_expression(hce2)
        if feature_stratum.invaded():
            # check for species in same species group
            sgl = []
            has_species_group = False
            for s in self.feature_stratum(feature_stratum.previous_feature_stratum_id()).species_list():
                if self.species_group("account", species) == self.species_group("account", s):
                    has_species_group = True
        # final harvest value expression
        hve1 = copy.deepcopy(self.expression(feature_stratum.final_harvest_value_expression_id()))
        hve1.set_statement(hve1.statement().replace("speciescode", species))
        hve1.set_statement(hve1.statement().replace("speciesgroup-account", self.species_group("account", species)))
        hve1.set_id("%(eid)s.%(s)s" % {"eid":hve1.id(), "s":species})
        # partial harvest value expression
        hve2 = copy.deepcopy(self.expression(feature_stratum.partial_harvest_value_expression_id()))
        hve2.set_statement(hve2.statement().replace("speciescode", species))
        hve2.set_statement(hve2.statement().replace("speciesgroup-account", self.species_group("account", species)))
        hve2.set_id("%(eid)s.%(s)s" % {"eid":hve2.id(), "s":species})
        if feature_stratum.invaded() and not has_species_group:
            hve1.set_statement(hve1.statement().replace("feature_stratum_id.unitvalue", "unitvalue"))
            hve1.set_id("%s-invasion" % hve1.id())
            hve2.set_statement(hve2.statement().replace("feature_stratum_id.unitvalue", "unitvalue"))
            hve2.set_id("%s-invasion" % hve2.id())
        if not self.has_expression(hve1):
            self.add_expression(hve1)
        if not self.has_expression(hve2):
            self.add_expression(hve2)
        a = Attribute(id=aid,
                      label=alabel,
                      factor=factor,
                      is_volume=True,
                      species_code=species,
                      curve=curve,
                      final_harvest_cost_expression_id=hce1.id(),
                      partial_harvest_cost_expression_id=hce2.id(),
                      final_harvest_value_expression_id=hve1.id(),
                      partial_harvest_value_expression_id=hve2.id(),
                      base_curve=base_curve)
        return a


    def add_invasion_state(self, feature_stratum_id):
        import copy
        fs1 = self.feature_stratum(feature_stratum_id)
        if not fs1.invasion_enabled() or fs1.invaded(): return
        fs2id = "%s-invasion" % fs1.id()
        if fs2id in self._feature_stratum_dict: return
        fs2 = copy.deepcopy(fs1)
        fs2.set_id(fs2id)
        fs2.set_invaded(True)
        fs2.set_previous_feature_stratum_id(fs1.id())
        
        fs1.set_invasion_transition(fs2.id())
        self.add_feature_stratum(fs2)
        if fs2.has_invasion_species_factors():
            # pre-compiled post-invasion curve factors by species code
            fs2.remove_volume_attributes()
            for s in fs2.invasion_species_list():
                if s in fs1.species_list():
                    base_curve = fs1.base_curve(s)
                else: # use default curve
                    base_curve = self.base_curve(s)
                a = self.generate_volume_attribute(fs2, s, fs2.invasion_species_factor(s), base_curve)
                self.add_attribute(a)
                self.add_volume_attribute(fs2.id(), a.as_ref())
        else:
            tvc = self.total_volume_curve(fs2.id())
            age = tvc.max_mai_age()
            v = 0
            v1 = 0
            v2 = 0
            for a in fs2.volume_attribute_list():
                if not self.is_invasive(a.species_code()): continue
                c = self.resolve_to_curve(a)
                v += c.value(age)
            pv = v / tvc.value(age)
            f1 = fs2.invasion_factor() / pv                       # absolute intol 
            f2 = fs2.invasion_factor()                            # relative intol
            f3 = fs2.invasion_factor() / (1-pv)                   # absolute tol
            f4 = ((1-pv) - pv*(fs2.invasion_factor()-1)) / (1-pv) # relative tol
            for a in fs2.volume_attribute_list():    
                if self.is_invasive(a.species_code()):
                    if fs2.invasion_type() == "A":
                        a.set_factor(a.factor() * f1)
                    else: # assume invasion type "R"
                        a.set_factor(a.factor() * f2)
                else:
                    if fs2.invasion_type() == "A":
                        a.set_factor(a.factor() * f3)
                    else: # assume invasion type "R"
                        a.set_factor(a.factor() * f4)
        return fs2


    def product_stratum_id(self, treatment_stratum_id, feature_stratum_id, treatment_id):
        return "%s.%s.%s" % (treatment_stratum_id, feature_stratum_id, treatment_id)


    def process_track(self, treatment_stratum_id, feature_stratum_id):
        fs = self._feature_stratum_dict[feature_stratum_id]
        ts = self._treatment_stratum_dict[treatment_stratum_id]
        
        if self._track_filter_set:
            if fs.treatment_stratum_id_list():
                if (treatment_stratum_id, feature_stratum_id) not in self._track_filter_set: return
            else:
                if self._track_filter_set and (ts.id(), fs.previous_feature_stratum_id()) not in self._track_filter_set: return
        if not fs.volume_attribute_list():
            self._processed_track_set.add((treatment_stratum_id, feature_stratum_id))
            return
        statement_base = "status in managed and treatment_stratum_id eq '%s' " \
                         "and feature_stratum_id eq '%s'" \
                         % (treatment_stratum_id, feature_stratum_id)
        mrt_list = []
        s1 = Select(statement_base)
        s2 = None
        s3 = None
        for tl in ts.treatment_label_list():
            t = ts.treatment(tl)
            if t.is_finalcut():
                s1.add_treatment(copy.deepcopy(t))
                fs_invaded = None
                if ((t.force_extensive() or len(ts.treatment_label_list()) == 1)) and self.invasion():
                    fs_invaded = self.add_invasion_state(feature_stratum_id)
                    if fs_invaded:
                        has_precom = False
                        for tl_tmp in ts.treatment_label_list(): 
                            # scan for precommercial treatments
                            t_tmp = ts.treatment(tl_tmp)
                            if t_tmp.is_precommercial(): has_precom = True
                        if not has_precom:
                            # only transition to invasion state if finalcut not coupled with any precom treatments
                            self.add_feature_stratum_transition(t.id(), feature_stratum_id, fs_invaded.id())
                            if self._track_filter_set:
                                self.add_track_filter(treatment_stratum_id, fs_invaded.id())

                if t.force_extensive() and len(ts.treatment_label_list()) > 1:
                    t_ext = copy.deepcopy(t)
                    t_ext.set_extensive(True)
                    t_ext.set_label(t.label() + "-ext")
                    t_ext.set_id(t.id() + "-ext")

                    #########################################################
                    # start new code (test)
                    # problem this code is trying to fix:
                    #   model not transitioning towards invaded state after (forced) extensive final cut treatment
                    if fs_invaded and self.invasion():
                        self.add_feature_stratum_transition(t_ext.id(), feature_stratum_id, fs_invaded.id())
                    # end new code (test)
                    #########################################################

                    if t.init_extensive() and not fs.invaded():
                        # extensive treatment only available if first treatment in horizon
                        s2 = copy.deepcopy(s1)
                        s1.set_statement("%s and previous_treatment_id eq 'init'" % statement_base)
                    s1.add_treatment(t_ext)
            elif t.is_commercialthinning() or t.is_speciescut() or t.is_precommercial():
                mrt_list.append(t)
                if t.is_precommercial():
                    if not s3: 
                        s3 = copy.deepcopy(s1)
                        s3.set_statement("%s and previous_treatment_id eq 'init'" % statement_base)
                    t_init = copy.deepcopy(t)
                    t_init.set_extensive(True)
                    s3.add_treatment(t_init)
            else:
                s1.add_treatment(copy.deepcopy(t))
        for s in [s1, s2, s3]:
            if not s: continue 
            # process treatments in this track
            l1 = [] # list of finalcut type treatments
            l2 = [] # list of other treatments
            for t in s.treatment_list():
                if not t.is_special():
                    for mrt in mrt_list:
                        if t.is_extensive() and not mrt.force_extensive(): continue
                        t.add_midrotation_treatment(mrt)
                        if mrt.is_precommercial():
                            t.set_label(t.label()+"_"+mrt.label())         
                        else:
                            t.set_label(mrt.label()+"_"+t.label())
                t.update_operability_limits(self.total_volume_curve(feature_stratum_id))#, debug=True)
                psid = self.product_stratum_id(treatment_stratum_id, feature_stratum_id, t.id())
                if not self.product_stratum(psid):
                    self.add_product_stratum(ProductStratum(id=psid,
                                                            treatment_stratum_id=treatment_stratum_id,
                                                            feature_stratum_id=feature_stratum_id,
                                                            current_treatment_id=t.id()))
                ps = self.product_stratum(psid)
                t.add_produce_assign(Assign("product_stratum_id", psid))
                t.add_produce_assign(Assign("current_treatment_id", t.id()))
                if t.midrotation_harvest_treatment():
                    mrtid = t.midrotation_harvest_treatment().id()
                else:
                    mrtid = "none"
                t.add_produce_assign(Assign("midrotation_harvest_treatment_id", mrtid))
                t.add_transition_assign(Assign("previous_treatment_id", t.id()))
                self._update_product_attribute_list(t, fs, ts, ps)
                
                # only assign feature stratum transition if not set yet (otherwise assume set at treatment level)
                # ??? maybe condition should be the other way around (ForestModel transition overrides Treatment transition) ??? 
                if not t.feature_stratum_transition() and self.feature_stratum_transition(t.id(), fs.id()):
                    #if t.is_finalcut(): print t.id(), t.label(), self.feature_stratum_transition(t.id(), fs.id())
                    t.set_feature_stratum_transition(self.feature_stratum_transition(t.id(), fs.id()))

                # Uses fs.treatment_stratum_id() and fs.treatment_stratum_id_list()
                # to detect (and skip) irreg strata... yuck!!!
                if self._track_filter_set and t.feature_stratum_transition() and not (fs.treatment_stratum_id() or fs.treatment_stratum_id_list()):
                    self.add_track_filter(ts.id(), t.feature_stratum_transition())

            self.add_track_select(s)
        self._processed_track_set.add((ts.id(), fs.id()))
        
    def process_track_woodstock(self, treatment_stratum_id, feature_stratum_id):
        #print 'process_track_woodstock', treatment_stratum_id, feature_stratum_id #debug
        fs = self._feature_stratum_dict[feature_stratum_id]
        ts = self._treatment_stratum_dict[treatment_stratum_id]        
        if self._track_filter_set:
            if fs.treatment_stratum_id_list():
                if (treatment_stratum_id, feature_stratum_id) not in self._track_filter_set: return
            else:
                if self._track_filter_set and (ts.id(), fs.previous_feature_stratum_id()) not in self._track_filter_set: return
        if not fs.volume_attribute_list():
            self._processed_track_set.add((treatment_stratum_id, feature_stratum_id))
            return
        # build mask
        fs_ti = self.woodstock_landscape_theme_index('feature_stratum')
        ts_ti = self.woodstock_landscape_theme_index('treatment_stratum')
        mask = ''
        for ti in range(0, len(self._woodstock_landscape_list)):
            if ti == fs_ti: mask += feature_stratum_id+' ' 
            elif ti == ts_ti: mask += treatment_stratum_id+' ' 
            else:
                mask += '? '
        statement_base = mask
        mrt_list = []
        s = Select(statement_base)
        for tl in ts.treatment_label_list():
            t = ts.treatment(tl)
            if t.is_finalcut():
                s.add_treatment(copy.deepcopy(t))
                fs_invaded = None
                if self.invasion():
                    fs_invaded = self.add_invasion_state(feature_stratum_id)
                    if fs_invaded:
                        self.add_woodstock_landscape_theme('feature_stratum', [fs_invaded.id()])
                        self.add_feature_stratum_transition(t.id(), feature_stratum_id, fs_invaded.id())
                        #print " feature stratum transition" , t.id(), feature_stratum_id, self.feature_stratum_transition(t.id(), feature_stratum_id)
                        if self._track_filter_set:
                            self.add_track_filter(treatment_stratum_id, fs_invaded.id())
            else:
                s.add_treatment(copy.deepcopy(t))
        l1 = [] # list of finalcut type treatments
        l2 = [] # list of other treatments
        for t in s.treatment_list():
            
            # do we need this or not?
            #t.update_operability_limits(self.total_volume_curve(feature_stratum_id))#, debug=True)

            #psid = self.product_stratum_id(treatment_stratum_id, feature_stratum_id, t.id())
            #self.add_product_stratum(ProductStratum(id=psid,
            #                                        treatment_stratum_id=treatment_stratum_id,
            #                                        feature_stratum_id=feature_stratum_id,
            #                                        current_treatment_id=t.id()))
            #ps = self.product_stratum(psid)
            #t.add_produce_assign(Assign("product_stratum_id", psid))
            #t.add_produce_assign(Assign("current_treatment_id", t.id()))
            #if t.midrotation_harvest_treatment():
            #    mrtid = t.midrotation_harvest_treatment().id()
            #else:
            #    mrtid = "none"
            #t.add_produce_assign(Assign("midrotation_harvest_treatment_id", mrtid))
            #t.add_transition_assign(Assign("previous_treatment_id", t.id()))
            #self._update_product_attribute_list(t, fs, ts, ps)                
            # only assign feature stratum transition if not set yet (otherwise assume set at treatment level)
            # ??? maybe condition should be the other way around (ForestModel transition overrides Treatment transition) ??? 
            if not t.feature_stratum_transition() and self.feature_stratum_transition(t.id(), fs.id()):
                t.set_feature_stratum_transition(self.feature_stratum_transition(t.id(), fs.id()))
            # Uses fs.treatment_stratum_id() and fs.treatment_stratum_id_list()
            # to detect (and skip) irreg strata... yuck!!!
            if self._track_filter_set and t.feature_stratum_transition() and not (fs.treatment_stratum_id() or fs.treatment_stratum_id_list()):
                self.add_track_filter(ts.id(), t.feature_stratum_transition())
        self.add_track_select(s)
        self._processed_track_set.add((ts.id(), fs.id()))
        
        

    def product_attribute_list(self, fsid, tsid, tid):
        key_list = [(fsid, tsid, tid),
                    (fsid, tsid, None),
                    (fsid, None, tid),
                    (fsid, None, None),
                    (None, tsid, tid),
                    (None, tsid, None),
                    (None, None, tid),
                    (None, None, None),
                    (fsid, tsid, ''),  # ugly hack!
                    (fsid, '', tid),   # ugly hack!
                    (fsid, '', ''),    # ugly hack! 
                    ('', tsid, tid),   # ugly hack!
                    ('', tsid, ''),    # ugly hack!
                    ('', '', tid),     # ugly hack!
                    ('', '', '')]      # ugly hack!

        result = []
        #if __debug__:
        #    for k in self._product_attribute_dict.keys():
        #        print k
        #    for k in key_list:
        #        print k
        for key in key_list:
            if key in self._product_attribute_dict:
                for a in self._product_attribute_dict[key]:
                    result.append(a)
                    #if __debug__:
                    #    print key, a.id()
        return result


    def _update_product_attribute_list(self, t, fs, ts, ps):
        vol_attribute_list = []
        nonvol_attribute_list = []
        # add area treated attribute
        a = Attribute(label="product.areatreated.%s" % t.id(),
                      expression=Expression("curveid('unity')"))
        a.set_key("product.areatreated.%s" % t.id())
        nonvol_attribute_list.append(a)
        # process general product attributes
        pal = self.product_attribute_list(fs.id(), ts.id(), t.id())
        for a in pal:
            nonvol_attribute_list.append(a)
        if t.is_finalcut():
            # add area disturbed attribute
            a = Attribute(label="product.areadisturbed.finalcut",
                          expression=Expression("curveid('unity')"))
            a.set_key("product.areadisturbed.finalcut")
            nonvol_attribute_list.append(a)
        for mrt in t.midrotation_treatment_list():
            # add area treated attribute
            a = Attribute(label="product.areatreated.%s" % mrt.id(),
                          expression=Expression("curveid('unity')"),
                          future=mrt.future())
            a.set_key("product.areatreated.%s" % mrt.id())
            nonvol_attribute_list.append(a)
            if mrt.is_commercialthinning() or t.is_speciescut():
                # add area dsturbed attribute
                a = Attribute(label="product.areadisturbed.partialcut",
                              expression=Expression("curveid('unity')"),
                              future=mrt.future())
                a.set_key("product.areadisturbed.partialcut")
                nonvol_attribute_list.append(a)
        pd = self.product_distribution(fs.product_distribution_id())
        if t.is_finalcut() and not fs.treatment_stratum_id():
            for a in fs.attribute_list():                                    
                 if a.is_volume():
                    tmp101 = []
                    if a.is_group():
                        for aa in self.attributes(a.id()).attribute_list():
                            tmp101.append(aa)
                    else:
                        tmp101.append(a)
                    for aa in tmp101:
                        for pc in pd.product_code_list():
                            if aa.species_code():
                                sc = aa.species_code()
                            elif aa.id():
                                sc = self.attribute(aa.id()).species_code()
                            assert sc
                            pdc = pd.curve(sc, pc)
                            if self._skip_null_curves and pdc.is_null(): continue
                            if aa.id():
                                aaa = self.attribute(aa.id())
                                statement = "attributeid('%(aid)s') * curveid('%(pdcid)s')" % {"aid":aaa.id(), "pdcid":pdc.id()}
                                aaaa = Attribute(label=aaa.label()+"."+pc,
                                                 expression=Expression(statement),
                                                 is_ref=False,
                                                 is_volume=True,
                                                 species_code=sc,
                                                 final_harvest_cost_expression_id=aaa.final_harvest_cost_expression_id(),
                                                 partial_harvest_cost_expression_id=aaa.partial_harvest_cost_expression_id(),
                                                 final_harvest_value_expression_id=aaa.final_harvest_value_expression_id(),
                                                 partial_harvest_value_expression_id=aaa.partial_harvest_value_expression_id())
                            else:
                                aaaa = Attribute(label=aa.label()+"."+pc,
                                                 species_code=sc,
                                                 final_harvest_cost_expression_id=aa.final_harvest_cost_expression_id(),
                                                 partial_harvest_cost_expression_id=aa.partial_harvest_cost_expression_id(),
                                                 final_harvest_value_expression_id=aa.final_harvest_value_expression_id(),
                                                 partial_harvest_value_expression_id=aa.partial_harvest_value_expression_id())
                                statement = ""
                                if aa.expression():
                                    statement = aa.expression.statement()+"*curveid('%s')" % pdc.id()
                                else:
                                    # assume curve reference instead of Expression: build statement from scratch
                                    statement = "attributeid('%(aid)s')*curveid('%(pdcid)s')" % {"aid":aa.id(), "pdcid":pdc.id()}
                                aaaa.set_expression(Expression(statement))
                            if aaaa.label() in ps.attribute_key_list(): continue
                            aaaa.set_factor(aa.factor() * t.intensity())
                            aaaa.set_key(aaaa.label())
                            vol_attribute_list.append(aaaa)
                            if t.midrotation_harvest_treatment():
                                mrt = t.midrotation_harvest_treatment()
                                mrt_a = copy.deepcopy(aaaa)
                                mrt_a.set_key(mrt_a.key() + "-" + mrt.id())
                                mrt_a.set_factor(mrt.intensity())
                                mrt_a.set_future(mrt.future())
                                vol_attribute_list.append(mrt_a)
        for hva in vol_attribute_list:
            ps.add_attribute(hva)
            if not hva.future():
                # generate harvest_cost attribute from harvested volume attribute
                fhca = Attribute(label="product.cost.harvest.finalcut.%s" % hva.species_code(),
                                 id="%(hceid)s.%(future)s" % {"hceid":hva.final_harvest_cost_expression_id(), "future":hva.future()},
                                 expression=copy.deepcopy(self.expression(hva.final_harvest_cost_expression_id())),
                                 is_ref=False)
                fhca.set_key(fhca.id())
                ps.add_attribute(fhca)
                
                ################################################################################
                # UGLY HACK ####################################################################
                if self.has_hack("final-harvest-cost-expression"):
                    tmplabel1 = "_.harvestvolume.final.%s" % hva.species_code()
                    if not ps.has_attribute(tmplabel1):
                        ps.add_attribute(Attribute(label=tmplabel1,
                                                   id=tmplabel1,
                                                   expression=Expression(statement=self.expression("harvestvolume.final").statement().replace("speciescode", hva.species_code())),
                                                   is_ref=False))
                    tmplabel2 = "_.harvestcost.final"
                    if not ps.has_attribute(tmplabel2):
                        ps.add_attribute(Attribute(label=tmplabel2,
                                                   id=tmplabel2,
                                                   expression=self.expression(hva.final_harvest_cost_expression_id()),
                                                   is_ref=False))
                    fhca = ps.attribute(fhca.id())
                    statement = "attribute('%(tmplabel1)s')*attribute('%(tmplabel2)s')" % {"tmplabel1":tmplabel1, "tmplabel2":tmplabel2}
                    fhca.set_expression(Expression(statement=statement))
                ################################################################################
                ################################################################################

                fhva = Attribute(label="product.value.%s" % hva.species_code(),
                                 id="%(hceid)s.%(future)s" % {"hceid":hva.final_harvest_value_expression_id(),
                                                              "future":hva.future()},
                                 expression=self.expression(hva.final_harvest_value_expression_id()),
                                 is_ref=False)
                fhva.set_key(fhva.id())
                ps.add_attribute(fhva)

                ################################################################################
                # UGLY HACK ####################################################################
                if self.has_hack("final-harvest-value-expression"):
                    tmplabel1 = "_.harvestvolume.final.%s" % hva.species_code()
                    if not ps.has_attribute(tmplabel1):
                        ps.add_attribute(Attribute(label=tmplabel1,
                                                   id=tmplabel1,
                                                   expression=Expression(statement=self.expression("harvestvolume.final").statement().replace("speciescode", hva.species_code())),
                                                   is_ref=False))                    
                    tmplabel2 = "_.harvestvalue.final.%s" % self.species_group("account",hva.species_code())
                    if not ps.has_attribute(tmplabel2):
                        ps.add_attribute(Attribute(label=tmplabel2,
                                                   id=tmplabel2,
                                                   expression=self.expression(hva.final_harvest_value_expression_id()),
                                                   #expression=Expression(statement=statement),
                                                   is_ref=False))
                    fhva = ps.attribute(fhva.id())
                    statement = "attribute('%(tmplabel1)s')*attribute('%(tmplabel2)s')" % {"tmplabel1":tmplabel1, "tmplabel2":tmplabel2}
                    fhva.set_expression(Expression(statement=statement))                    
                ################################################################################
                ################################################################################

            else:
                phca = Attribute(label="product.cost.harvest.partialcut.%s" % hva.species_code(),
                                 id="%(hceid)s.neg%(future)s" % {"hceid":hva.partial_harvest_cost_expression_id(), "future":abs(hva.future())},
                                 expression=self.expression(hva.partial_harvest_cost_expression_id()),
                                 is_ref=False,
                                 future=hva.future())
                phca.set_key(phca.id())
                ps.add_attribute(phca)

                ################################################################################
                # UGLY HACK ####################################################################
                if self.has_hack("partial-harvest-cost-expression"):
                    tmplabel1 = "_.harvestvolume.partial.%s" % hva.species_code()
                    if not ps.has_attribute(tmplabel1):
                        ps.add_attribute(Attribute(label=tmplabel1,
                                                   id=tmplabel1,
                                                   expression=Expression(statement=self.expression("harvestvolume.partial").statement().replace("speciescode", hva.species_code())),
                                                   is_ref=False))
                    tmplabel2 = "_.harvestcost.partialcut"
                    if not ps.has_attribute(tmplabel2):
                        ps.add_attribute(Attribute(label=tmplabel2,
                                                   id=tmplabel2,
                                                   expression=self.expression(hva.partial_harvest_cost_expression_id()),
                                                   is_ref=False))
                    phca = ps.attribute(phca.id())
                    statement = "attribute('%(tmplabel1)s')*attribute('%(tmplabel2)s')" % {"tmplabel1":tmplabel1, "tmplabel2":tmplabel2}
                    phca.set_expression(Expression(statement=statement))
                ################################################################################
                ################################################################################

                phva = Attribute(label="product.value.%s" % hva.species_code(),
                                 id="%(hceid)s.neg%(future)s" % {"hceid":hva.partial_harvest_value_expression_id(), "future":abs(hva.future())},
                                 expression=self.expression(hva.partial_harvest_value_expression_id()),
                                 is_ref=False,
                                 future=hva.future())
                phva.set_key(phva.id())
                ps.add_attribute(phva)
                
                ################################################################################
                # UGLY HACK ####################################################################
                if self.has_hack("partial-harvest-value-expression"):
                    tmplabel1 = "_.harvestvolume.partial.%s" % hva.species_code()
                    if not ps.has_attribute(tmplabel1):
                        ps.add_attribute(Attribute(label=tmplabel1,
                                                   id=tmplabel1,
                                                   expression=Expression(statement=self.expression("harvestvolume.partial").statement().replace("speciescode", hva.species_code())),
                                                   is_ref=False))                    
                    tmplabel2 = "_.harvestvalue.partial.%s" % self.species_group("account",hva.species_code())
                    if not ps.has_attribute(tmplabel2):
                        ps.add_attribute(Attribute(label=tmplabel2,
                                                   id=tmplabel2,
                                                   expression=self.expression(hva.partial_harvest_value_expression_id()),
                                                   #expression=Expression(statement=statement),
                                                   is_ref=False))
                    phva = ps.attribute(phva.id())
                    statement = "attribute('%(tmplabel1)s')*attribute('%(tmplabel2)s')" % {"tmplabel1":tmplabel1, "tmplabel2":tmplabel2}
                    phva.set_expression(Expression(statement=statement))
                ################################################################################
                ################################################################################

        for a in nonvol_attribute_list:
            ps.add_attribute(a)


    def _dump_xml_product(self):
        lines = []
        lines.append("<!-- dump product 'select' elements -->")
        for psid in self._product_stratum_dict:
            ps = self._product_stratum_dict[psid]
            statement = "product_stratum_id eq '%s'" % psid
            s = Select(statement)
            for key in ps.attribute_key_list():
                s.add_product_attribute(ps.attribute(key))
            if not s.is_empty():
                lines.extend(s.dump_xml())
        return lines

    def _dump_xml_select(self):
        lines = []
        lines.append("<!-- dump general 'select' elements -->")
        for statement in self.select_statement_list():
            lines.extend(self.select(statement).dump_xml())
        return lines
    
    def _dump_xml_tail(self):
        lines = []
        # add catch-all tracks statement
        lines.append("""<select statement="status in unmanaged">""")
        lines.append("<track />")
        lines.append("</select>")
        
        lines.append("</ForestModel>")
        return lines

    def eval_expression(self, expression, age):
        """
        Parse and evaluate expression at age
        """
        curveid_pattern = "curveid\(\'[a-zA-Z0-9_\-.]*\'\)"
        attributeid_pattern = "attributeid\(\'[a-zA-Z0-9_\-.]*\'\)"
        # compile list of unique curve references
        curve_ref_dict = {}
        ref_set = set()
        for ref in re.findall(curveid_pattern, expression):
            ref_set.add(ref)
        for ref in ref_set:
            # extract curve id from reference
            id = ref[9:(len(ref)-2)]
            curve_ref_dict[id] = str(self.curve(id).value(age))
        # compile list of unique attribute references
        attribute_ref_dict = {}
        ref_set = set()
        for ref in re.findall(attributeid_pattern, expression):
            ref_set.add(ref)
        for ref in ref_set:
            # extract attribute id from reference
            id = ref[13:(len(ref)-2)]
            a = self.attribute(id)
            if a.expression():
                attribute_ref_dict[id] = str(self.eval_expression(a.expression().statement(), age) * a.factor())
            else:
                attribute_ref_dict[id] = str(self.curve(a.curve().id()).value(age) * a.factor())
        e = expression
        for id in curve_ref_dict:
            e = re.sub("curveid\(\'%s\'\)"%id, curve_ref_dict[id], e)
        for id in attribute_ref_dict:
            e = re.sub("attributeid\(\'%s\'\)"%id, attribute_ref_dict[id], e)
        return eval(e)


    def add_woodstock_constant(self, idcode, textstring):
        self._woodstock_constants_dict[idcode] = textstring


    def add_woodstock_landscape_theme(self, theme, values=[], index=-1):
        if theme not in self._woodstock_landscape_list:
            if index < 0: # append to end of list
                index = len(self._woodstock_landscape_list)
            self._woodstock_landscape_list.insert(index, theme)
            self._woodstock_landscape_dict[theme] = set()
        self._woodstock_landscape_dict[theme].update(values)

    def woodstock_landscape_theme(self, theme):
        assert theme in self._woodstock_landscape_dict
        return self._woodstock_landscape_dict[theme]

    def add_woodstock_landscape_theme_aggregate(self, theme, aggregate, values):
        if theme not in self._woodstock_landscape_aggregate_dict:
            self._woodstock_landscape_aggregate_dict[theme] = []
        self._woodstock_landscape_aggregate_dict[theme].append((aggregate,values))
    
    def woodstock_landscape_theme_index(self, theme):
        return self._woodstock_landscape_list.index(theme)

    def add_woodstock_landscape_theme(self, theme, values=[], index=-1):
        if theme not in self._woodstock_landscape_list:
            if index < 0: # append to end of list
                index = len(self._woodstock_landscape_list)
            self._woodstock_landscape_list.insert(index, theme)
            self._woodstock_landscape_dict[theme] = set()
        self._woodstock_landscape_dict[theme].update(values)

    def add_woodstock_action_aggregate(self, aggregate, values):
        if aggregate not in self._woodstock_action_aggregate_dict:
            self._woodstock_action_aggregate_dict[aggregate] = []
        self._woodstock_action_aggregate_dict[aggregate].extend(values)

    def dump_woodstock_model(self, 
                             cull=False,
                             append_outputs='',
                             append_yields=''):
        lines = []

        woodstock_constants_section = self._dump_woodstock_constants_section()
        woodstock_lifespan_section = self._dump_woodstock_lifespan_section()
        woodstock_areas_section = self._dump_woodstock_areas_section()
        woodstock_actions_section = self._dump_woodstock_actions_section()
        woodstock_transitions_section = self._dump_woodstock_transitions_section()
        woodstock_yields_section = self._dump_woodstock_yields_section(cull)
        if append_yields: # append yields definitions from text file
            woodstock_yields_section.append('; YIELD definitions appended from external file (NOT automatically generated by fmg)')
            import os
            print os.getcwd()
            for tmpline in open(append_yields, 'r').readlines():
                woodstock_yields_section.append(tmpline.rstrip('\n'))
        woodstock_landscape_section = self._dump_woodstock_landscape_section()
        woodstock_outputs_section = self._dump_woodstock_outputs_section()
        if append_outputs: # append outputs definitions from text file
            woodstock_outputs_section.append('; OUTPUT definitions appended from external file (NOT automatically generated by fmg)')
            for tmpline in open(append_outputs, 'r').readlines():
                woodstock_outputs_section.append(tmpline.rstrip('\n'))
        woodstock_reports_section = self._dump_woodstock_reports_section()
        woodstock_graphics_section = self._dump_woodstock_graphics_section()
        woodstock_optimize_section = self._dump_woodstock_optimize_section()
        woodstock_lpschedule_section = self._dump_woodstock_lpschedule_section()
        woodstock_schedule_section = self._dump_woodstock_schedule_section()
        woodstock_queue_section = self._dump_woodstock_queue_section()
        woodstock_control_section = self._dump_woodstock_control_section()

        lines.extend(woodstock_constants_section)
        lines.extend(woodstock_landscape_section)
        lines.extend(woodstock_lifespan_section)
        lines.extend(woodstock_areas_section)
        lines.extend(woodstock_yields_section)
        lines.extend(woodstock_actions_section)
        lines.extend(woodstock_transitions_section)
        lines.extend(woodstock_outputs_section)
        lines.extend(woodstock_reports_section)
        lines.extend(woodstock_graphics_section)
        lines.extend(woodstock_optimize_section)
        lines.extend(woodstock_lpschedule_section)
        lines.extend(woodstock_schedule_section)
        lines.extend(woodstock_queue_section)
        lines.extend(woodstock_control_section) 

        return lines

    
    def _dump_woodstock_constants_section(self):
        lines = []
        for key in self._define_dict.keys():
            define = self._define_dict[key]
            if define.is_constant():
                self.add_woodstock_constant(define.field(), str(define.value()))
        if self._woodstock_constants_dict: # only proceed if constants dict not empty
            lines.append('')
            lines.append('CONSTANTS')
            keys = self._woodstock_constants_dict.keys()
            keys.sort()
            for key in keys:
                lines.append('%s %s'%(str(key), str(self._woodstock_constants_dict[key])))
            lines.append('')
        return lines
         
    def _dump_woodstock_landscape_section(self):
        lines = ['', 'LANDSCAPE']
        self.add_woodstock_landscape_theme('succession_stratum', sorted(self._succession_stratum_dict.keys()))
        self.add_woodstock_landscape_theme('treatment_stratum', sorted(self._treatment_stratum_dict.keys()))
        fs_list = self._feature_stratum_dict.keys()
        #if self.has_commercialthinning:
        #    for fsid in self._feature_stratum_dict.keys():
        #        fs_list.append(fsid+'_CT')
        fs_list.sort()
        self.add_woodstock_landscape_theme('feature_stratum', fs_list)
        self.add_woodstock_landscape_theme('default_feature_stratum', sorted(self._feature_stratum_dict.keys()))
        for theme in self._woodstock_landscape_list:
            lines.append('*THEME %s' % str(theme))
            for value in sorted(self._woodstock_landscape_dict[theme]):
                lines.append('  %s' % str(value))
            if theme in self._woodstock_landscape_aggregate_dict:
                for item in self._woodstock_landscape_aggregate_dict[theme]:
                    lines.append('*AGGREGATE %s' % item[0])
                    for value in item[1]:
                        lines.append('  %s' % str(value))
        return lines

    def _dump_woodstock_lifespan_section(self):
        lines = ['', 'LIFESPAN']
        theme_index = self.woodstock_landscape_theme_index('succession_stratum')
        for ssid in self._succession_stratum_dict.keys():
            line = ''
            for t in range(0, len(self._woodstock_landscape_list)):
                if t <> theme_index: 
                    line += '? '
                else:
                    line += str(ssid)+' '
            line += str(int(min(self._woodstock_max_lifespan, 
                                self.period(self._succession_stratum_dict[ssid].succession().breakup()))))
            lines.append(line)
        return lines

    def _dump_woodstock_areas_section(self, skip=True):

        # TO DO: implement *EXCLUDE (use status field)

        #lines = ['', 'AREAS']
        lines = []
        # default is skip (let Spatial Woodstock generate this section)
        if not skip:
            pass # TO DO: stuff here
        return lines

    def _split_woodstock_line(self, line, maxchar=255, indent=2):
        if len(line) <= maxchar: return line
        result = ''
        ll = 0
        for token in line.split(' '):
            if ll+len(token)+1+indent <= maxchar:
                result += ' '+token
                ll += len(token)+1
            else:
                result += '\n'+' '*indent
                ll = 0
        return result.strip()

    def _dump_woodstock_yields_section(self, cull=False, tol=0.5, show_progress=True, debug=False, harvestcost=True):
        #print self._product_stratum_dict.keys()
        #print self._product_stratum_dict
        #assert False
        culled_curve_count = 0
        lines = ['', 'YIELDS']
        theme_index = self.woodstock_landscape_theme_index('feature_stratum')
        keys = self._feature_stratum_dict.keys()
        keys.sort()
        if show_progress:
            import progressbar
            if cull: tmp = 'enabled'
            else:    tmp = 'disabled'
            print 'Generating Woodstock YIELDS section (curve culling %s)' % tmp
            p = progressbar.ProgressBar(maxval=len(keys)).start()
            i = 0
        for fsid in keys:
            fs = self._feature_stratum_dict[fsid]
            
            # declare age-dependent yield and generate feature_stratum mask
            mask = ''
            for t in range(0, len(self._woodstock_landscape_list)):
                if t <> theme_index: mask += '? '
                else: mask += str(fsid)+' '
            lines.append('*Y %s' % mask)

            # build volume yield curve dict
            age_set = set()
            curves = {}
            curves2 = {}
            bac = None
            if fs.is_regime_regular():
                tmpset = set(self._species_group_dict['account'].values())  # build list of species groups
                tmpdict = dict(zip(tmpset, [self.group_species_list('account', sg) for sg in tmpset]))
                pd = self.product_distribution(fs.product_distribution_id())
                #print tmpdict
                #assert False
                for sg in tmpdict:
                    c = Curve()
                    c.add_point(0, 0.0)
                    for sc in tmpdict[sg]:
                        a = fs.volume_attribute(sc)
    
                        #print fs._volume_attribute_dict
                        #assert False
                        if not a: continue # species not present in this stratum
                        c += self.resolve_to_curve(a)
                    age_set.update(c.age_list())
                    c_sd = c * (pd.curve(sc, 'de') + pd.curve(sc, 'sc')) # de + sc = sd
                    if not c_sd.is_null(): curves[(sg,'sd')] = c_sd
                    c_pa = c * pd.curve(sc, 'pa')
                    if not c_sd.is_null(): curves[(sg,'pa')] = c_pa
            elif fs.is_regime_irregular():
                # fetch ba curve
                #for a in fs.attribute_list(): print a.id(), a.descriptor()
                a = [a for a in fs.attribute_list() 
                     if a.has_descriptor() and a.descriptor().is_basalarea() and a.descriptor().is_total()][-1:][0] # find total BA attribute
                bac = a.curve()
                #if bac.is_null():
                #    print fs.id()
                #    print '\n'.join(bac.dump_xml())
                assert not bac.is_null() # all irregular feature strata should have non-null total BA curve
                
                # compile volume curves (growing stock)
                for a in fs.volume_attribute_list():
                    if a.species_code() == None: continue
                    c = self.resolve_to_curve(a)
                    #if c.is_null() and cull: continue # skip null (all zeros) volume curves (avoid Woodstock interpreter warning)
                    curves[(a.species_code(),a.product_code())] = c
                    #print a.species_code(),a.product_code()
                    #c.dump_csv()
                    age_set.update(c.age_list())
                #print [t.id() for t in self._treatment_dict.values() if t.is_irregular()]
                #assert False
                for t in [t for t in self._treatment_dict.values() if t.is_irregular()]:
                    if t.id() not in curves2: curves2[t.id()] = {}
                    #print fs.id(), fs.treatment_stratum_id_list()
                    #print self.product_stratum_id(fs.treatment_stratum_id_list()[0], fs.id(), t.id())
                    #print self._product_stratum_dict.keys()
                    ps = self.product_stratum(self.product_stratum_id(fs.treatment_stratum_id_list()[0], fs.id(), t.id()))
                    if not ps: 
                        print self.product_stratum_id(fs.treatment_stratum_id_list()[0], fs.id(), t.id())
                        continue # invalid combination
                    # iterate over volume attributes
                    for a in [ps.attribute(key) for key in ps.attribute_key_list() if ps.attribute(key).is_volume()]:
                        if a.species_code() == None: continue
                        c = self.resolve_to_curve(a)
                        #if cull and c.is_null(): continue # skip null (all zeros) volume curves (avoid Woodstock interpreter warning)
                        curves2[t.id()][(a.species_code(),a.product_code())] = c
                        print fsid, t.id(), a.species_code()
                        #age_set.update(c.age_list())

            else:
                assert False # something is wrong

#             # output volume curves as table (growing stock)
#             colwidths = {}
#             keys = curves.keys()
#             keys.sort()
#             line = '_AGE '
#             for key in keys:
#                 tmp = 'yvol_%s_%s' % (key[0].lower(), key[1].lower())
#                 colwidths[key] = len(tmp) + 1
#                 line += tmp.ljust(colwidths[key])
#             lines.append(line)
#             age_list = list(age_set)
#             age_list.sort()
#             for age in range(self.periodlength(), age_list[-1:][0], self.periodlength()):
#                 line = str(self.period(age)).rjust(4)
#                 for key in keys:
#                     line += ('%5.1f' % curves[key].value(age)).rjust(colwidths[key])
#                 lines.append(line)
#             if bac:
#                 lines.append('yba_total 1 %s' % '\n            '.join([('%4.1f' % bac.value(age)) for age in age_list]))

            
            # output volume curves (growing stock)
            #keys = curves.keys()
            #keys.sort()
            if debug:
                print 'outputting volume curves for feature stratum', fsid
            lines.append('; volume yield components (growing stock)')
            for key in sorted(curves.keys()):
                c = curves[key]
                if cull and c.is_null():
                    if debug:
                        print 'null curve', key[0], key[1]
                        c.dump_csv()
                    culled_curve_count += 1
                    continue
                if c.is_flat():
                    #print 'flat curve',  key[0], key[1]
                    startage = max(self.periodlength(), c.min_age())
                    if cull and c.value(startage) < tol:
                        if debug:
                            print 'near-zero flat curve', key[0], key[1]
                            c.dump_csv()
                        culled_curve_count += 1
                        continue
                    line = self._split_woodstock_line('yvol_%s_%s %s %s ' % (key[0].lower(), 
                                                                             key[1].lower(),
                                                                             self.period(startage),
                                                                             c.value(startage)))
                    lines.append(line)
                    #culled_curve_count += 1
                    continue
                # build list of ages
                tmpages = [age for age in range(max(self.periodlength(), c.min_age()), c.max_age()+self.periodlength(), self.periodlength())]
                if cull:
                    tmpages = [age for age in range(max(self.periodlength(), c.min_age()), c.max_age()+self.periodlength(), self.periodlength())
                               if not c.is_flat_from(age-self.periodlength(), tol=tol)]
                    if not tmpages: 
                        if debug:
                            print 'non-null curve pruned down to nothing (from back)',  key[0], key[1]
                            c.dump_csv()
                        culled_curve_count += 1
                        continue
                    # prune ages from front of list where correponding values are near-zero 
                    tmpages.reverse()
                    firstage = tmpages.pop()
                    while tmpages and c.value(firstage) < tol:
                        firstage = tmpages.pop()
                    tmpages.append(firstage)
                    tmpages.reverse()
                    if len(tmpages)==1 and c.value(tmpages[0]) < tol: 
                        if debug:
                            print 'non-null curve pruned down to nothing (from front)',  key[0], key[1]
                            c.dump_csv()
                        culled_curve_count += 1
                        continue
                line = self._split_woodstock_line('yvol_%s_%s %s %s ' % (key[0].lower(), 
                                                                         key[1].lower(), 
                                                                         self.period(tmpages[0]),
                                                                         ' '.join([('%5.1f' % c.value(age)).strip() 
                                                                                   for age in tmpages])))
                lines.append(line)
            if fs.is_regime_irregular():
                tmpages = [age for age in range(max(self.periodlength(), bac.min_age()), 
                                                bac.max_age()+self.periodlength(), 
                                                self.periodlength())]
                line = self._split_woodstock_line('yba_total %s %s' % (self.period(tmpages[0]), 
                                                                       ' '.join([('%4.1f' % bac.value(age)).strip() 
                                                                                 for age in tmpages])))
                lines.append(line)
                # output volume curves as table (harvest volume by treatment, regime I)
                for t in [t for t in self._treatment_dict.values() if t.is_irregular()]:
                    lines.append('; havest volume yield components for treatment: %s' % t.id())
                    for key in sorted(curves2[t.id()].keys()):
                        c = curves2[t.id()][key]
                        if cull and c.is_null(): 
                            culled_curve_count += 1
                            continue
                        if c.is_flat():
                            startage = max(self.periodlength(), c.min_age())
                            if cull and c.value(startage) < tol:
                                if debug:
                                    print 'near-zero flat curve', key[0], key[1]
                                    c.dump_csv()
                                culled_curve_count += 1
                                continue
                            line = self._split_woodstock_line('yvol_%s_%s_%s %s %s ' % (key[0].lower(), 
                                                                                         key[1].lower(),
                                                                                         t.id().lower(),
                                                                                         self.period(startage),
                                                                                         c.value(startage)))
                            #print fsid, t.id()
                            #print line

                            lines.append(line)
                        # build list of ages
                        tmpages = [age for age in range(max(self.periodlength(), c.min_age()), 
                                                        c.max_age()+self.periodlength(), 
                                                        self.periodlength())]
                        if cull:
                            tmpages = [age for age in range(max(self.periodlength(), c.min_age()), 
                                                            c.max_age()+self.periodlength(), 
                                                            self.periodlength())
                                       if not c.is_flat_from(age-self.periodlength(), tol=tol)]
                            if not tmpages: 
                                if debug:
                                    print 'non-null curve pruned down to nothing (from back)',  key[0], key[1]
                                    c.dump_csv()
                                culled_curve_count += 1
                                continue
                            # prune ages from front of list where correponding values are near-zero 
                            tmpages.reverse()
                            firstage = tmpages.pop()
                            while tmpages and c.value(firstage) < tol:
                                firstage = tmpages.pop()
                            tmpages.append(firstage)
                            tmpages.reverse()
                            if len(tmpages)==1 and c.value(tmpages[0]) < tol: 
                                if debug:
                                    print 'non-null curve pruned down to nothing (from front)',  key[0], key[1]
                                    c.dump_csv()
                                culled_curve_count += 1
                                continue
                        line = self._split_woodstock_line('yvol_%s_%s_%s %s %s ' % (key[0].lower(), 
                                                                                    key[1].lower(), 
                                                                                    t.id().lower(),
                                                                                    self.period(tmpages[0]),
                                                                                    ' '.join([('%5.1f' % c.value(age)).strip() 
                                                                                              for age in tmpages])))
                        lines.append(line)

            if show_progress:
                #print i, len(keys)
                p.update(i)
                i += 1
        # for fsid in keys... (end of block)
        ################################################################################
        if show_progress:
            p.finish()
                            

                        
            #assert not culled_curve_count

#             tables = {'pa':[], 'sd':[]}
#             if fs.is_regime_irregular():
#                 # output volume curves as table (harvest volume by treatment, regime I)
#                 for t in [t for t in self._treatment_dict.values() if t.is_irregular()]:
#                     colwidths = {'pa':{}, 'sd':{}}
#                     keys = curves2[t.id()].keys()
#                     keys.sort()
#                     tmplines = {'pa':'_AGE ', 'sd':'_AGE '}
#                     for key in keys:
#                         tmp = 'yvol_%s_%s_%s' % (key[0].lower(), key[1].lower(), t.id().lower())
#                         colwidths[key[1]][key] = len(tmp) + 1
#                         tmplines[] += tmp.ljust(colwidths[key[1]][key])
#                     tables[key[1]].append(line)
#                     age_list = list(age_set)
#                     age_list.sort()
#                     for age in range(self.periodlength(), age_list[-1:][0], self.periodlength()):
#                         line = str(self.period(age)).rjust(4)
#                         for key in keys:
#                             line += ('%7.3f' % curves2[t.id()][key].value(age)).rjust(colwidths[key[1]][key])
#                         tables[key[1]].append(line)
#                     #if bac:
#                     #    lines.append('yba_total_%s 1 %s' % (t.id().lower(), '\n            '.join([('%4.1f' % bac.value(age)) for age in age_list])))
#                 for key in tables: lines.extend(tables[key])

        # global complex yield components
        lines.append('*YC %s' % self.empty_woodstock_mask())
        sg_list = list(set(self._species_group_dict['account'].values()))  # build list of species groups
        pc_list = ['pa', 'sd']
        for pc in pc_list:
            lines.append('yvol_pc-%s _SUM(%s)' % (pc, ',\n                '.join(['yvol_%s_%s' % (sg, pc) for sg in sg_list])))
        lines.append('yvol_total _SUM(%s)' % ', '.join(['yvol_pc-%s'%pc for pc in pc_list])) 
        #lines.append('yvol_total _SUM(%s)' % ',\n                '.join(['yvol_%s_%s' % (sg, pc) 
        #                                                                 for sg in list(set(self._species_group_dict['account'].values())) 
        #                                                                 for pc in ['pa', 'sd']]))
        lines.append('ymai_vol_total _MAI(yvol_total, %s)' % self.periodlength())
        lines.append('yytpmai_vol_total _YTP(ymai_vol_total)')

        if cull:
            print 'culled %s curves' % culled_curve_count

        return lines


#     def _dump_woodstock_yields_section(self):
#         lines = ['', 'YIELDS']
#         theme_index = self.woodstock_landscape_theme_index('feature_stratum')
#         keys = self._feature_stratum_dict.keys()
#         keys.sort()
#         for fsid in keys:
#             fs = self._feature_stratum_dict[fsid]
            
#             # declare age-dependent yield and generate feature_stratum mask
#             line = '*Y '
#             for t in range(0, len(self._woodstock_landscape_list)):
#                 if t <> theme_index: 
#                     line += '? '
#                 else:
#                     line += str(fsid)+' '
#             lines.append(line)

#             # build volume yield curve dict
#             age_set = set()
#             curves = {}
#             for a in fs.volume_attribute_list():
#                 if fs.regime() == 'I' and a.species_code() == None: continue # a.set_species_code('TOT')
#                 #print a.id(), a.is_volume(), a.species_code()
#                 c = self.resolve_to_curve(a)
#                 if c.is_null(): continue # skip null (all zeros) volume curves (avoid Woodstock interpreter warning)
#                 curves[(a.species_code(),a.product_code())] = c
#                 age_set.update(c.age_list())
#             #if fs.regime() == 'R': curves['TOT'] = fs.total_volume_curve()

#             # output volume curve dict as table
#             colwidths = {}
#             keys = curves.keys()
#             keys.sort()
#             line = '_AGE  '
#             for key in keys:
#                 #if species == 'TOT': continue
#                 tmp = 'yvol_%s' % key[0].lower()
#                 if key[1]: tmp += '_%s' % key[1].lower()
#                 colwidth[key] = len(tmp) + 1
#                 line += tmp.ljust(colwidth[key])
                
#             #line += 'yvol_tot'
#             lines.append(line)
#             age_list = list(age_set)
#             age_list.sort()
#             for age in range(self.periodlength(), age_list[-1:][0], self.periodlength()):
#                 #f age < 0: continue
#                 tmpage = round(age / 5)
#                 line = (str(int(age/self.periodlength())).rjust(4)).ljust(5)
#                 tv = 0.0
#                 for key in keys:
#                     line += ('%7.3f' % curves[key].value(age)).rjust(colwidth[key])
#                     #if fs.regime() == 'R' and species == 'TOT': continue # feature-stratum total volume curves broken
#                     #tv += curves[species].value(age)
#                 #if fs.regime() == 'R': line += ('%7.3f' % tv).rjust(11)
#                 lines.append(line)

# #             # build non-volume yield curve dict
# #             age_set = set()
# #             curves = {}
# #             for a in fs.attribute_list():
# #                 if a.is_volume(): continue 
# #                 if fs.regime() == 'I': a.set_species_code('TOT')
# #                 #print a.id(), a.is_volume(), a.species_code()
# #                 c = self.resolve_to_curve(a)
# #                 curves[a.species_code()] = c
# #                 age_set.update(c.age_list())
# #             #if fs.regime() == 'R': curves['TOT'] = fs.total_volume_curve()


#         return lines

    def _dump_woodstock_actions_section(self, show_progress=True, ytpbroken=False):
        lines = ['', 'ACTIONS']
        
        tsid_list = copy.copy(self._treatment_stratum_dict.keys())
        fsid_list = copy.copy(self._feature_stratum_dict.keys())

        for tid in self.treatment_id_list():
            t = self.treatment(tid)
            dar = 'Y' # default age reset
            if t.adjust() == 'R' or t.is_irregular(): dar = 'N'
            lines.append('*ACTION %s %s %s' % (t.id().lower(), dar, t.description()))        

        if __debug__ and show_progress:
            import progressbar
            print "Processing tracks (pass 1 of 2)"
            p = progressbar.ProgressBar(maxval=len(fsid_list)).start()
            i = 0
        for fsid in fsid_list:
            if __debug__ and show_progress:
                p.update(i)
                i += 1
            fs = self.feature_stratum(fsid)
            if not fs.treatment_stratum_id_list():
                for tsid in tsid_list:
                    self.process_track_woodstock(tsid, fsid)
            else:
                # special case (1:1 feature stratum to treatment stratum ratio)
                #self.process_track(fs.treatment_stratum_id(), fsid)
                for tsid in fs.treatment_stratum_id_list():
                    #print fs.treatment_stratum_id_list()
                    self.process_track_woodstock(tsid, fsid)
        if __debug__ and show_progress:
            p.finish()
        tsid_list = copy.copy(self._treatment_stratum_dict.keys())
        fsid_list = copy.copy(self._feature_stratum_dict.keys())
        if __debug__ and show_progress:
            import progressbar
            print "Processing tracks (pass 2 of 2)"
            p = progressbar.ProgressBar(maxval=len(self._feature_stratum_dict)).start()
            i = 0
        for fsid in self._feature_stratum_dict:
            if __debug__ and show_progress:
                p.update(i)
                i += 1
            for tsid in self._treatment_stratum_dict:
                if not self.is_processed_track(tsid, fsid):
                    self.process_track_woodstock(tsid, fsid)
        if __debug__ and show_progress:
            p.finish()
        
        fs_ti = self.woodstock_landscape_theme_index('feature_stratum')
        ts_ti = self.woodstock_landscape_theme_index('treatment_stratum')
        lines2 = []
        for tid in self.treatment_id_list():
            #print self.treatment_id_list()
            print 'processing treatment operability: ', tid
            lines.append('*OPERABLE %s' % tid.lower())
            t = copy.deepcopy(self.treatment(tid))
            if t.is_irregular(): 
                for tsid, fsid in self._processed_track_set:
                    ts = self.treatment_stratum(tsid)
                    if tid not in ts.treatment_id_list(): continue
                    fs = self.feature_stratum(fsid)
                    t = ts.treatment(t.label())
                    line = '  '
                    for ti in range(0, len(self._woodstock_landscape_list)):
                        if ti == fs_ti: line += fsid+' ' 
                        elif ti == ts_ti: line += tsid+' ' 
                        else: line += '? '
                    #print t.oplmintype(), t.oplmaxtype()
                    assert t.oplmintype() == t.oplmaxtype() == 'BA' # only BA-based operability supported for now
                    line += 'yba_total >= %s' % t.oplmin()
                    if t.irreg_oplmax(): line += ' AND yba_total <= %s' % t.oplmax()
                    lines.append(line)
            else: # regular treatment
                # determine min operability
                assert t.oplmintype() != 'RMV' # not implemented yet
                if t.oplmintype() == 'AGE':
                    oplmin = '_AGE >= %s' % self.period(t.minage())
                elif t.oplmintype() == 'VOL':
                    oplmin = 'yvol_total >= %s' % t.oplmin()
                elif t.oplmintype() == 'RMM': 
                    if ytpbroken:
                        # debug hack
                        oplmin = '_AGE >= %s' % self.period(t.minage())
                    else:
                        oplmin = 'yytpmai_vol_total <= %s' % t.oplmin()
                else:
                    #print t.oplmintype(), t._type_code, t.is_irregular()
                    assert False # bad value
                # determine max operability
                assert t.oplmaxtype() != 'RMV' # not implemented yet
                if t.oplmaxtype() == 'AGE':
                    oplmax = '_AGE <= %s' % self.period(t.maxage())
                elif t.oplmaxtype() == 'VOL':
                    oplmax = 'yvol_total >= %s' % t.oplmax()
                elif t.oplmaxtype() == 'RMM':
                    if ytpbroken:
                        # debug hack
                        oplmax = '_AGE <= %s' % self.period(t.maxage())
                    else:
                        oplmax = 'yytpmai_vol_total >= %s' % t.oplmax()
                else:
                    assert False # bad value
                tsid_set = set()
                for tsid, fsid in self._processed_track_set:
                    ts = self.treatment_stratum(tsid)
                    fs = self.feature_stratum(fsid)
                    if tsid in tsid_set or tid not in ts.treatment_id_list(): continue
                    tsid_set.add(tsid)
                    # build mask
                    mask = ''
                    for ti in range(0, len(self._woodstock_landscape_list)):
                        if ti == ts_ti: mask += tsid+' ' 
                        else: mask += '? '
                    if oplmin and oplmax: operator = 'AND'
                    lines.append('  %s%s %s %s' % (mask, oplmin, operator, oplmax))
                if t.is_commercialthinning():
                    # output *PARTIAL statement
                    sg_list = list(set(self._species_group_dict['account'].values()))  # build list of species groups
                    pc_list = ['pa', 'sd']
                    
                    lines.append('*PARTIAL %s\n  yvol_total %s' % (t.id(),' '.join(['yvol_%s_%s' % (sg.lower(),pc) for sg in sg_list for pc in pc_list])))

        # generate aggregate actions based on treatment type
        tmplist_finalcut = []
        tmplist_commercialthinning = []
        tmplist_precommercial = []
        tmplist_irregular = []
        for tid in self.treatment_id_list():
            t = self.treatment(tid)
            if t.is_finalcut():
                tmplist_finalcut.append(tid.lower())
            elif t.is_commercialthinning():
                pass # implement later...
            elif t.is_precommercial():
                tmplist_precommercial.append(tid.lower())
            elif t.is_irregular():
                tmplist_irregular.append(tid.lower())
        if tmplist_finalcut:
            comment = 'Treatment type: final cut'
            lines.append('*AGGREGATE tt-fc %s' % comment)
            lines.append('  %s' % ' '.join(tmplist_finalcut))
        if tmplist_commercialthinning:
            comment = 'Treatment type: commecial thinning'
            lines.append('*AGGREGATE tt-ct %s' % comment)
            lines.append('  %s' % ' '.join(tmplist_commercialthinning))
        if tmplist_precommercial:
            comment = 'Treatment type: pre-commercial'
            lines.append('*AGGREGATE tt-pc %s' % comment)
            lines.append('  %s' % ' '.join(tmplist_precommercial))
        if tmplist_irregular:
            comment = 'Treatment type: irregular'
            lines.append('*AGGREGATE tt-ir %s' % comment)
            lines.append('  %s' % ' '.join(tmplist_irregular))
        #if self._woodtock_action_aggregate_dict:
        for aggregate in self._woodstock_action_aggregate_dict:
            lines.append('*AGGREGATE %s' % aggregate)
            lines.append('  %s' % ' '.join(self._woodstock_action_aggregate_dict[aggregate]))
            

        return lines

# # and t.oplmaxtype() == 'AGE':
#                 lines.append('%s _AGE %s _AGE %s' % (self.empty_woodstock_mask(), 
#                                                      self.period(t.minage()), 
#                                                      self.period(t.maxage())))
#             elif :
                
# #                 for tsid, fsid in self._processed_track_set:
# #                     ts = self.treatment_stratum(tsid)
# #                     fs = self.feature_stratum(fsid)
# #                     if tid not in ts.treatment_id_list(): continue
# #                     if t.is_irregular(): t = ts.treatment(t.label())
# #                     # build mask
# #                     line = '  '
# #                     for ti in range(0, len(self._woodstock_landscape_list)):
# #                         if ti == fs_ti: line += fsid+' ' 
# #                         elif ti == ts_ti: line += tsid+' ' 
# #                         else: line += '? '
# #                     # calculate lower operability limit
# #                     if not t.is_irregular():
# #                         t.update_operability_limits(self.total_volume_curve(fsid))
# #                     line += '_AGE %s _AGE %s' % (self.period(t.minage()), 
# #                                                  self.period(t.maxage()))
# #                     lines.append(line)
#             if t.is_commercialthinning():
#                 lines2.append('*PARTIAL %s' % tid)
#                 line = ' '
#                 for species_code in self.species_code_list():
#                     line += 'yvol_%s ' % species_code
#                 #line += 'vol_tot_i'
#                 lines2.append(line)
        

    def _dump_woodstock_transitions_section(self):
        lines = ['', 'TRANSITIONS']

        lines.append('*CASE _DEATH')
        theme_index = self.woodstock_landscape_theme_index('succession_stratum')
        for ssid in self._succession_stratum_dict.keys():
            mask = ''
            for t in range(0, len(self._woodstock_landscape_list)):
                if t == theme_index: mask += str(ssid)+' '
                else: mask += '? '
            lines.append('  *SOURCE %s' % mask)
            lines.append('    *TARGET %s 100 _AGE %s' % (mask, self.period(self._succession_stratum_dict[ssid].succession().renew())))
        for tid in self.treatment_id_list():
            sourcemask_set = set()
            skip = False
            lines.append('*CASE %s' % tid.lower())
            print 'processing transitions for case: ', tid
            tmplines = []
            for tsid, fsid in self._processed_track_set:
                #if skip:
                #    print tid, fsid, fsid
                #    continue
                ts = self.treatment_stratum(tsid)
                fs = self.feature_stratum(fsid)
                if tid not in ts.treatment_id_list(): continue
                # build mask
                fs_ti = self.woodstock_landscape_theme_index('feature_stratum')
                ts_ti = self.woodstock_landscape_theme_index('treatment_stratum')
                mask1 = ''
                for ti in range(0, len(self._woodstock_landscape_list)):
                    if ti == fs_ti: mask1 += fsid+' ' 
                    elif ti == ts_ti: mask1 += tsid+' ' 
                    else: mask1 += '? '
                t = self._track_select_dict[mask1].treatment(tid)
                if not t.has_treatment_stratum_transition():
                    mask1 = ''
                    for ti in range(0, len(self._woodstock_landscape_list)):
                        if ti == fs_ti: mask1 += fsid+' ' 
                        else: mask1 += '? '
                tfsid = fsid
                ttsid = tsid
                #print "xxx", t.id(), fsid, self.feature_stratum_transition(t.id(), fsid)
                if t.feature_stratum_transition() or self.feature_stratum_transition(t.id(), fsid):
                    tfsid = t.feature_stratum_transition()
                if t.treatment_stratum_transition():
                    ttsid = t.treatment_stratum_transition()
                mask2 = ''
                for ti in range(0, len(self._woodstock_landscape_list)):
                    if ti == fs_ti and tfsid != fsid: mask2 += tfsid+' ' 
                    elif ti == ts_ti and ttsid != tsid: mask2 += ttsid+' ' 
                    else: mask2 += '? '
                #print "  mask2", mask2
                if t.offset_curve():
                    lines.append('  ; define transitions for mask: %s' % mask1)
                    oc = t.offset_curve()
                    targetage = None
                    targetstratum = None
                    age1 = None
                    age2 = None
                    if not t.age_dependent_transitions(): # assume forced dominant transition
                        for age in oc.age_list():
                            if targetage:
                                if targetage == oc.value(age):
                                    age2 = age
                                else:
                                    lines.append('  *SOURCE %s@AGE(%s..%s)' % (mask1, self.period(age1), self.period(age2)))
                                    line = '    *TARGET %s100 _AGE %s' % (mask2, self.period(targetage))
                                    if t.retain(): line += ' _LOCK %i' % self.period(t.retain())
                                    lines.append(line)
                                    targetage = oc.value(age)
                                    age1 = age
                                    age2 = age
                            else:
                                targetage = oc.value(age)
                                age1 = age
                                age2 = age
                        lines.append('  *SOURCE %s' % mask1) # applies to treatment ages not covered by @AGE
                        line = '    *TARGET %s100 _AGE %s' % (mask2, self.period(targetage))
                        if t.retain(): line += ' _LOCK %i' % self.period(t.retain())
                        lines.append(line)
                    else: # age dependent transitions
                        for age in oc.age_list():
                            if targetage:
                                if targetage == oc.value(age) and targetstratum == t.feature_stratum_transition(age):
                                    age2 = age
                                else:
                                    lines.append('  *SOURCE %s@AGE(%s..%s)' % (mask1, self.period(age1), self.period(age2)))
                                    line = '    *TARGET %s100 _AGE %s' % (mask2, self.period(targetage))
                                    if t.retain(): line += ' _LOCK %i' % self.period(t.retain())
                                    lines.append(line)
                                    targetage = oc.value(age)
                                    targetstratum = t.feature_stratum_transition(age)
                                    age1 = age
                                    age2 = age
                                    tfsid = t.feature_stratum_transition(age)
                                    ttsid = t.treatment_stratum_transition(age)
                                    mask2 = ''
                                    for ti in range(0, len(self._woodstock_landscape_list)):
                                        if ti == fs_ti: mask2 += tfsid+' ' 
                                        elif ti == ts_ti and ttsid != tsid: mask2 += ttsid+' ' 
                                        else: mask2 += '? '
                            else:
                                targetage = oc.value(age)
                                targetstratum = t.feature_stratum_transition(age)
                                age1 = age
                                age2 = age
                                tfsid = t.feature_stratum_transition(age)
                                ttsid = t.treatment_stratum_transition(age)
                                mask2 = ''
                                for ti in range(0, len(self._woodstock_landscape_list)):
                                    if ti == fs_ti: mask2 += tfsid+' ' 
                                    elif ti == ts_ti and ttsid != tsid: mask2 += ttsid+' ' 
                                    else: mask2 += '? '
                        lines.append('  *SOURCE %s' % mask1) # applies to treatment ages not covered by @AGE
                        line = '    *TARGET %s100 _AGE %s' % (mask2, self.period(targetage))
                        if t.retain(): line += ' _LOCK %i' % self.period(t.retain())
                        lines.append(line)
                else: # offset mask not defined
                    mask_fs = t.has_feature_stratum_transition() or self.feature_stratum_transition(t.id(), fsid)
                    mask_ts = t.has_treatment_stratum_transition()
                    mask = ''
                    #print self._woodstock_landscape_list
                    if self.treatment(t.id()).has_feature_stratum_transition():
                        #print t.id(), t.feature_stratum_transition()
                        mask = self.empty_woodstock_mask()
                    else:
                        for ti in range(0, len(self._woodstock_landscape_list)):
                            if ti == fs_ti and mask_fs: mask += fsid+' ' 
                            #elif ti == ts_ti and mask_ts: mask += tsid+' ' 
                            else: mask += '? '
                    #print mask
                    #assert False
                    #if not (mask_fs or mask_ts): 
                    #    pass
                    #    #skip = True
                    #    #mask = self.empty_woodstock_mask()
                    #else:
                    #    lines.append('  ; define transitions for mask: %s' % mask)
                    #    #print t.feature_stratum_transition(), t.treatment_stratum_transition()
                    if mask in sourcemask_set: continue
                    if mask.find(self.empty_woodstock_mask()) == 0: # source mask is empty, append to end of list
                        tmplines.append('  *SOURCE %s' % mask)
                    else:
                        lines.append('  *SOURCE %s' % mask)
                    sourcemask_set.add(mask)
                    adjust = ''
                    assert not (t.is_relative_adjust() and t.offset()) # not sure how to deal with this case in Woodstock...
                    if t.is_absolute_adjust() and t.offset(): 
                        adjust = ' _AGE %s' % self.period(t.offset())
                    line = '    *TARGET %s100%s' % (mask2, adjust)
                    if t.retain(): 
                        line += ' _LOCK %i' % self.period(t.retain())
                    if t.is_commercialthinning():
                        fsti = self.woodstock_landscape_theme_index('feature_stratum')
                        tsti = self.woodstock_landscape_theme_index('treatment_stratum')
                        line += ' _APPEND(_TH%i, _CT) _APPEND(_TH%i, _CT)' % (fsti+1, tsti+1)
                    if mask.find(self.empty_woodstock_mask()) == 0: # source mask is empty, append to end of list
                        tmplines.append(line)
                    else:
                        lines.append(line)
            lines.extend(tmplines) # add empty source mask transition to end of CASE   
        return lines
        

    def period(self, age):
        return int(round(age/self.periodlength()))
                                                

    def _dump_woodstock_outputs_section(self):
        lines = ['', 'OUTPUTS']
        sg_list = list(set(self._species_group_dict['account'].values()))  # build list of species groups
        pc_list = ['pa', 'sd']
        # output harvest volumes and treated areas
        finalcut_volume_outputs = {}
        commercialthinning_volume_outputs = {}
        
        irregular_volume_outputs = {'tr':{}, 
                                    'sgpc':dict(zip([x+y for x in sg_list for y in pc_list], 
                                                    [[] for xy in [x+y for x in sg_list for y in pc_list]]))}
        regular_volume_outputs = dict(zip([x+y for x in sg_list for y in pc_list], 
                                          [[] for xy in [x+y for x in sg_list for y in pc_list]]))
        tmplist_finalcut = []
        tmplist_commercialthinning = []
        tmplist_precommercial = []
        tmplist_irregular = []

        for tid in self.treatment_id_list():
            t = self.treatment(tid)
            if t.is_finalcut():
                # area treated
                comment = 'Area treated (treatment: %s)' % tid.lower()
                outputname = 'otreatedarea_tr-%s' % tid.lower()
                tmplist_finalcut.append(outputname)
                lines.append('*OUTPUT %s %s' % (outputname, comment))
                lines.append('  *SOURCE %s _AREA' % tid.lower())
                # volume harvested
                finalcut_volume_outputs[tid] = []
                for sg in sg_list:
                    for pc in pc_list:
                        comment = 'Volume harvested (species group: %s, product class: %s, treatemnt: %s)' %  (sg.lower(), pc, tid.lower())
                        outputname = 'ohvol_sg-%s_pc-%s_tr-%s' % (sg.lower(), pc, tid.lower())
                        finalcut_volume_outputs[tid].append(outputname)
                        regular_volume_outputs[sg+pc].append(outputname)
                        lines.append('*OUTPUT %s %s' % (outputname, comment))
                        lines.append('  *SOURCE %s %s' % (tid.lower(), 'yvol_%s_%s' % (sg.lower(), pc)))
            elif t.is_commercialthinning():
                # area treated
                comment = 'Area treated (treatment: %s)' % tid.lower()
                outputname = 'otreatedarea_tr-%s' % tid.lower()
                tmplist_commercialthinning.append(outputname)
                lines.append('*OUTPUT %s %s' % (outputname, comment))
                lines.append('  *SOURCE %s _AREA' % tid.lower())
                # volume harvested
                commercialthinning_volume_outputs[tid] = []
                for sg in sg_list:
                    for pc in pc_list:
                        comment = 'Volume harvested (species group: %s, product class: %s, treatemnt: %s)' %  (sg.lower(), pc, tid.lower())
                        outputname = 'ohvol_sg-%s_pc-%s_tr-%s' % (sg.lower(), pc, tid.lower())
                        commercialthinning_volume_outputs[tid].append(outputname)
                        regular_volume_outputs[sg+pc].append(outputname)
                        lines.append('*OUTPUT %s %s' % (outputname, comment))
                        lines.append('  *SOURCE %s %s' % (tid.lower(), 'yvol_%s_%s' % (sg.lower(), pc)))
            elif t.is_precommercial():
                # area treated
                comment = 'Area treated (treatment: %s)' % tid.lower()
                outputname = 'otreatedarea_tr-%s' % tid.lower()
                tmplist_precommercial.append(outputname)
                lines.append('*OUTPUT %s %s' % (outputname, comment))
                lines.append('  *SOURCE %s _AREA' % tid.lower())
            elif t.is_irregular():
                # area treated
                comment = 'Area treated (treatment: %s)' % tid.lower()
                outputname = 'otreatedarea_tr-%s' % tid.lower()
                tmplist_irregular.append(outputname)
                lines.append('*OUTPUT %s %s' % (outputname, comment))
                lines.append('  *SOURCE %s _AREA' % tid.lower())
                # volume harvested
                irregular_volume_outputs['tr'][tid] = []
                #irregular_volume_outputs['species'][tid] = []
                for sg in sg_list:
                    for pc in pc_list:
                        comment = 'Volume harvested (species group: %s, product class: %s, treatemnt: %s)' %  (sg.lower(), pc, tid.lower())
                        outputname = 'ohvol_sg-%s_pc-%s_tr-%s' % (sg.lower(), pc, tid.lower())
                        irregular_volume_outputs['tr'][tid].append(outputname)
                        if tid not in irregular_volume_outputs['sgpc']: 
                            irregular_volume_outputs['sgpc'][tid] = []
                        irregular_volume_outputs['sgpc'][sg+pc].append(outputname)
                        lines.append('*OUTPUT %s %s' % (outputname, comment))
                        lines.append('  *SOURCE %s %s' % (tid.lower(), 'yvol_%s_%s_%s' % (sg.lower(), pc, t.id().lower()))) 
        if tmplist_finalcut:
            comment = 'Area treated (treatment type: final cut)'
            lines.append('*OUTPUT otreatedarea_tt-fc %s' % comment)
            lines.append('  *SOURCE %s' % ' +\n          '.join(tmplist_finalcut))
        if tmplist_commercialthinning:
            comment = 'Area treated (treatment type: commecial thinning)'
            lines.append('*OUTPUT otreatedarea_tt-ct %s' % comment)
            lines.append('  *SOURCE %s' % ' +\n          '.join(tmplist_commercialthinning))
        if tmplist_precommercial:
            comment = 'Area treated (treatment type: pre-commercial)'
            lines.append('*OUTPUT otreatedarea_tt-pc %s' % comment)
            lines.append('  *SOURCE %s' % ' +\n          '.join(tmplist_precommercial))
        if tmplist_irregular:
            comment = 'Area treated (treatment type: irregular)'
            lines.append('*OUTPUT otreatedarea_tt-ir %s' % comment)
            lines.append('  *SOURCE %s' % ' +\n          '.join(tmplist_irregular))
        if finalcut_volume_outputs:
            tmplist = []
            for tid in finalcut_volume_outputs.keys():
                comment = 'Volume harvested (treatemnt: %s)' %  tid.lower()
                outputname = 'ohvol_tr-%s' % tid.lower()
                tmplist.append(outputname)
                lines.append('*OUTPUT %s %s' % (outputname, comment))
                lines.append('  *SOURCE %s' % ' +\n          '.join(finalcut_volume_outputs[tid]))
            comment = 'Volume harvested (treatemnt type: final cut)'
            lines.append('*OUTPUT ohvol_tt-fc %s' % comment)
            lines.append('  *SOURCE %s' % ' +\n          '.join(tmplist))
        if commercialthinning_volume_outputs:
            tmplist = []
            for tid in commercialthinning_volume_outputs.keys():
                comment = 'Volume harvested (treatemnt: %s)' %  tid.lower()
                outputname = 'ohvol_tr-%s' % tid.lower()
                tmplist.append(outputname)
                lines.append('*OUTPUT %s %s' % (outputname, comment))
                lines.append('  *SOURCE %s' % ' +\n          '.join(commercialthinning_volume_outputs[tid]))
            comment = 'Volume harvested (treatemnt type: final cut)'
            lines.append('*OUTPUT ohvol_tt-ct %s' % comment)
            lines.append('  *SOURCE %s' % ' +\n          '.join(tmplist))
        if irregular_volume_outputs['tr']:
            assert False
            tmplist = []
            for tid in irregular_volume_outputs['tr'].keys():
                comment = 'Volume harvested (treatment: %s)' % tid.lower()
                outputname = 'ohvol_tr-%s' % tid.lower()
                tmplist.append(outputname)
                lines.append('*OUTPUT %s %s' % (outputname, comment))
                lines.append('  *SOURCE %s' % ' +\n          '.join(irregular_volume_outputs['tr'][tid]))
            comment = 'Volume harvested (treatemnt type: irregular)'
            lines.append('*OUTPUT ohvol_tt-ir %s' % comment)
            print lines[len(lines)-1] # debug
            lines.append('  *SOURCE %s' % ' +\n          '.join(tmplist))
            for sg in sg_list:
                tmplist = []
                for pc in pc_list:
                    comment = 'Volume harvested (regime: irregular, species group: %s, product class: %s)' %  (sg.lower(), pc)
                    outputname = 'ohvol_rg-i_sg-%s_pc-%s' % (sg.lower(), pc)
                    tmplist.append(outputname)
                    lines.append('*OUTPUT %s %s' % (outputname, comment))
                    lines.append('  *SOURCE %s' % ' +\n          '.join(irregular_volume_outputs['sgpc'][sg+pc]))
                comment = 'Volume harvested (regime: irregular, species group: %s)' %  sg.lower()
                outputname = 'ohvol_rg-i_sg-%s' % sg.lower()
                lines.append('*OUTPUT %s %s' % (outputname, comment))
                lines.append('  *SOURCE %s' % ' +\n          '.join(tmplist))
            #for sg in sg_list:
            #    for pc in pc_list:
            #        outputname = 'ohvol_rg-i_sg-%s' % sg.lower()
            #        lines.append('*OUTPUT %s' % outputname)
            #       lines.append('  *SOURCE %s' % ' +\n        '.join(irregular_volume_outputs['sgpc'][sg+pc]))
        if regular_volume_outputs:
            #tmpdict = dict(zip(sg_list, [[] for sg in sg_list])) # initialize dict to hold outputs
            for sg in sg_list:
                tmplist = []
                for pc in pc_list:
                    comment = 'Volume harvested (regime: regular, species group: %s, product class: %s)' %  (sg.lower(), pc)
                    outputname = 'ohvol_rg-r_sg-%s_pc-%s' % (sg.lower(), pc)
                    tmplist.append(outputname)
                    lines.append('*OUTPUT %s %s' % (outputname, comment))
                    lines.append('  *SOURCE %s' % ' +\n          '.join(regular_volume_outputs[sg+pc]))
                comment = 'Volume harvested (regime: irregular, species group: %s)' %  sg.lower()
                outputname = 'ohvol_rg-r_sg-%s' % sg.lower()
                lines.append('*OUTPUT %s %s' % (outputname, comment))
                lines.append('  *SOURCE %s' % ' +\n          '.join(tmplist))

        tmplist = []
        for sg in sg_list:
            outputname = 'ohvol_sg-%s' % sg.lower()
            tmplist.append(outputname)
            lines.append('*OUTPUT %s' % outputname)
            if irregular_volume_outputs['tr']:
                lines.append('  *SOURCE ohvol_rg-r_sg-%s + ohvol_rg-i_sg-%s' % (sg.lower(), sg.lower()))        
            else:
                lines.append('  *SOURCE ohvol_rg-r_sg-%s' % sg.lower())        
        outputname = 'ohvol_total'
        lines.append('*OUTPUT %s' % outputname)
        lines.append('  *SOURCE %s' % ' +\n          '.join(tmplist))
        

        # inventory area by feature stratum
        fs_ti = self.woodstock_landscape_theme_index('feature_stratum')
        comment = ' Area by feature stratum (THEME%i)' % (fs_ti+1)
        lines.append('*OUTPUT oarea_fs(_TH%i) %s' % ((fs_ti+1), comment))
        lines.append('  *SOURCE %s _INVENT _AREA' % self.empty_woodstock_mask())
        # inventory area by treatment stratu
        ts_ti = self.woodstock_landscape_theme_index('treatment_stratum')
        comment = ' Area by treatment stratum (THEME%i)' % (ts_ti+1)
        lines.append('*OUTPUT oarea_ts(_TH%i) %s' % ((ts_ti+1), comment))
        lines.append('  *SOURCE %s _INVENT _AREA' % self.empty_woodstock_mask())

        #for fsid in self.feature_stratum_id_list():
        #    # build mask
        #    mask = ''
        #    for ti in range(0, len(self._woodstock_landscape_list)):
        #        if ti == fs_ti: mask += fsid+' ' 
        #        else: mask += '? '
        #    lines.append('*OUTPUT oarea_fs-%s' % fsid)
        #    lines.append('  *SOURCE %s _INVENT _AREA' % mask)
        #for tsid in self.treatment_stratum_id_list():
        #    # build mask
        #    ts_ti = self.woodstock_landscape_theme_index('treatment_stratum')
        #    mask = ''
        #    for ti in range(0, len(self._woodstock_landscape_list)):
        #        if ti == ts_ti: mask += tsid+' ' 
        #        else: mask += '? '
        #    lines.append('*OUTPUT oarea_ts-%s' % tsid)
        #    lines.append('  *SOURCE %s _INVENT _AREA' % mask)


        # output growing stock
        tmplist1 = []
        rg_ti = self.woodstock_landscape_theme_index('regime')
        # ... by species
        #for regime in ['R', 'I']:
        for regime in self.woodstock_landscape_theme('regime'):
            mask = ''
            for ti in range(0, len(self._woodstock_landscape_list)):
                if ti == rg_ti: mask += regime+' ' 
                else: mask += '? '
            for sg in sg_list:
                for pc in pc_list:
                    comment = 'Growing stock (regime: %s, species group: %s, product class: %s)' % (regime.lower(), sg.lower(), pc)
                    outputname = 'ogvol_rg-%s_sg-%s_pc-%s' % (regime.lower(), sg.lower(), pc)
                tmplist1.append(outputname)
                lines.append('*OUTPUT %s %s' % (outputname, comment))
                lines.append('  *SOURCE %s _INVENT yvol_%s_%s' % (mask, sg.lower(), pc))
                
        # area and growing stock by regime, by age class (theme-based output)
        lines.append('FOR ageclass := 1 to %s' % self.period(self._horizon))
        comment = 'Area by age class'
        lines.append('  *OUTPUT oarea_ac-ageclass(_TH%s) %s' % (rg_ti, comment))
        lines.append('    *SOURCE %s @AGE(ageclass) _INVENT _AREA' % self.empty_woodstock_mask())
        comment = 'Growing stock by age class'
        lines.append('  *OUTPUT ogvol_ac-ageclass(_TH%s) %s' % (rg_ti, comment))
        lines.append('    *SOURCE %s @AGE(ageclass) _INVENT yvol_total' % self.empty_woodstock_mask())
        lines.append('ENDFOR')

        # operable area by treatment type
        for tid in self.treatment_id_list():
            comment = 'Operable area (treatment: %s)' % tid.lower()
            lines.append('*OUTPUT ooperable_tr-%s %s' % (tid.lower(), comment))
            lines.append('  *SOURCE _INVENT(%s) _AREA' % tid.lower())

        return lines

        
    def empty_woodstock_mask(self):
        return ('? ' * len(self._woodstock_landscape_list)).strip()


    #def is_empty_woodstock_mask(self, mask):
    #    return self.empty_woodstock_mask().find(mask) == 0
            

    def _dump_woodstock_reports_section(self, enabled=False):
        if enabled:
            lines = ['', 'REPORTS']
            lines.append('*TARGET all.csv')
            lines.append('  _ALL 1.._LENGTH')
            lines.append('*TARGETS traceact.csv')
            lines.append('  _TRACE 1.._LENGTH')
            lines.append('*TARGET actions.csv')
            lines.append('  _ACTION(~_DEATH) 1.._LENGTH')
        else:
            lines = []
        return lines
        

    def _dump_woodstock_graphics_section(self):
        lines = []
        return lines
        

    def _dump_woodstock_optimize_section(self):
        lines = []
        return lines
        

    def _dump_woodstock_lpschedule_section(self):
        lines = []
        return lines
        

    def _dump_woodstock_schedule_section(self):
        lines = []
        return lines
        

    def _dump_woodstock_queue_section(self):
        lines = []
        return lines
        

    def _dump_woodstock_control_section(self):
        lines = []
        return lines
        

       
if __name__ == "__main__":
    # test code for ForestModel class

    ############################
    # this test code is dated... (GEP 20061024)

    import copy
    import win32pipe # for popen command, to run 'tidy'
    import os

    from fmg.assign import Assign
    from fmg.input import Input
    #from fmg.output import Output
    from fmg.define import Define
    from fmg.curve import Curve
    from fmg.attribute import Attribute
    from fmg.attributes import Attributes
    from fmg.treatment import Treatment
    from fmg.retention import Retention
    from fmg.succession import Succession
    from fmg.select import Select
    from fmg.featurestratum import FeatureStratum
    from fmg.treatmentstratum import TreatmentStratum

##
##    reload(fmg.input)    
##    reload(fmg.output)    
##    reload(fmg.define)    
##    reload(fmg.curve)
##    reload(fmg.attribute)
##    reload(fmg.attributes)
##    reload(fmg.treatment)
##    reload(fmg.retention)
##    reload(fmg.succession)
##    reload(fmg.select)

    print "test ForestModel class"
    print
    f = ForestModel(10, 1)

    f.set_input_element(Input("AREA", "BLOCK", "AGE"))

    d1 = Define("column.field.name", "column.name", False) 
    d2 = Define("constant.field.name", "'foo,bar'", True)
    f.add_define(d1)
    f.add_define(d2)            

    c = Curve()
    c.set_id("curve.id")
    c.add_point(10, 100)
    c.add_point(20, 200)
    c.add_point(30, 300)
    c.add_point(40, 400)
    cref = Curve(c.id(), True)

    a = Attribute("attribute.label",factor="0.1")
    a.set_id("attribute.id")
    a.set_curve(cref)
    aref = Attribute("reference.attribute.label", "reference.attribute.id", True)

    aa = Attributes("attributes.label", "attributes.id")
    aa.add_attribute(aref)
    aaref = Attributes("reference.attribute.label", "reference.attributes.id", True)

    fs = FeatureStratum("featurestratum.id")
    fs.add_attribute(aref)
    f.add_feature_stratum(fs)

    t1 = Treatment("treatment.label.1", 10, 100, "age", 1, 11, "R", description="bogus treatment 1")
    #t.set_minage(10)
    #t.set_maxage(100)
    #t.set_offset(1)
    #t.set_retain(11)
    #t.set_adjust("R")
    aaa1 = Assign("numeric.field.name", "999")
    aaa2 = Assign("string.field.name", "'foo'")
    t1.add_produce_assign(aaa1)
    t1.add_transition_assign(aaa2)

    t2 = Treatment("treatment.label.CT",
                   id="treatment.id.CT",
                   oplmin=50,
                   oplmax=60,
                   opltype="age",
                   offset=0,
                   retain=10,
                   adjust="R",
                   description="commercial thinning",
                   type_code="CT")


    t3 = copy.deepcopy(t2)
    t3.set_label("treatment.label.3")
    t2.set_description("")
    t3.add_fu("foo")
    t3.add_fu("bar")    

    #print t1.fu_set()
    #print t2.fu_set()
    #print t3.fu_set()
    
    ts = TreatmentStratum("treatmentstratum.id")
    ts.add_treatment(t1)
    ts.add_treatment(t2)
    ts.add_treatment(t3)
    f.add_treatment_stratum(ts)
    
    r = Retention(0.99)
    ss = Succession(111, 11)

    #     s = Select()
    #     s.set_statement("theme1='xxx'")
    #     s.add_feature_attribute(aref)
    #     s.add_product_attribute(a)
    #     s.add_treatment(t)
    #     s.set_retention(r)
    #     s.set_succession(ss)

    f.add_curve(c)
    f.add_attribute(a)
    f.add_attributes(aa)
    #    f.add_select(s)

    print "testing eval_expression()", f.eval_expression("curveid('curve.id')", 15)
    print "testing eval_expression()", f.eval_expression("attributeid('attribute.id')", 16)
    print "testing eval_expression()", f.eval_expression("attributeid('attribute.id') + curveid('curve.id') + 1000.0", 16)
        
    lines = f.dump_xml()
    #print "\n".join(lines)

    ofname = "fmtest1.xml"
    of = open(ofname, "w")
    of.writelines(lines)
    of.close()

    # assume 'tidy' command installed (clean up XML output file)
    cmd = "tidy -xml -m -i %s" % os.getcwd()+"\\"+ofname
    print cmd
    print os.getcwd()
    rslt = win32pipe.popen(cmd)
    print rslt.readlines()
