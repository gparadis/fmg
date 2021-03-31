from fmg.assign import Assign

class Treatment:
    """
    ForestModel treatment element data
    
    Operability limits (OPL) can be specified using the following schemes:
    AGE: directly using age
    VOL: as a volume on total volume yield curve (or corresponding age)
    RMV: as a fraction of maximum volume age
    RMM: as a fraction of maximum MAI age
    BA: as a basal area on BA yield curve (or corresponding age)

    Treatment type codes:
    PC: partial cut
    CT: commercial thinning (constant species harvest proportions)
    SC: species cut (variable species harvest proportions)
    FC: final cut
    IR: irregular structure
    """

    _type_code_dict = {'pc':'PC',
                       'ct':'CT',
                       'sc':'SC',
                       'fc':'FC',
                       'ir':'IR'}

    _id_default = ''
    _minage_default = 0
    _maxage_default = 10000
    _oplmin_default = 0
    _oplmintype_default = 'AGE'
    _oplmax_default = 10000
    _oplmaxtype_default = 'AGE'
    _offset_default = 0
    _retain_default = 0
    _future_default = 0
    _adjust_default = 'A'
    _fu_fieldname_default = 'fu'
    _feature_stratum_id_fieldname_default = 'feature_stratum_id'
    _treatment_stratum_id_fieldname_default = 'treatment_stratum_id'
    _description_default = ''
    _type_code_default = ''
    _intensity_default = 1.0
    _fu_transition_default = ''
    _feature_stratum_transition_default = ''
    _treatment_stratum_transition_default = ''

    def __init__(self,
                 label,
                 id=_id_default,
                 oplmin=_oplmin_default,
                 oplmintype=_oplmintype_default,
                 oplmax=_oplmax_default,
                 oplmaxtype=_oplmaxtype_default,
                 offset=_offset_default,
                 offset_curve=None,
                 retain=_retain_default,
                 future=_future_default,
                 adjust=_adjust_default,
                 description=_description_default,
                 fu_fieldname=_fu_fieldname_default,
                 feature_stratum_id_fieldname=_feature_stratum_id_fieldname_default,
                 treatment_stratum_id_fieldname=_treatment_stratum_id_fieldname_default,
                 type_code=_type_code_default,
                 intensity = _intensity_default,
                 fu_transition=_fu_transition_default,
                 feature_stratum_transition=_feature_stratum_transition_default,
                 irregoplmax=False,
                 treatment_stratum_transition=_treatment_stratum_transition_default,
                 next_pass_treatment_id=''):
        self._irregoplmax = irregoplmax # ugly hack... yuck!
        self._label = label
        self._id = id     
               
        # lower operability
        self._oplmin = oplmin
        self._minage = self._minage_default
        if oplmintype in ['AGE','age']:
            self._oplmintype = 'AGE'
            self._minage = oplmin
        elif oplmintype in ['VOL', 'vol']:
            self._oplmintype = 'VOL'
        elif oplmintype in ['RMV', 'rmv']:
            self._oplmintype = 'RMV'
        elif oplmintype in ['RMM', 'rmm']:
            self._oplmintype = 'RMM'
        elif oplmintype in ['BA', 'ba']:
            self._oplmintype = 'BA'
        #else:
        #    self._minage = self._minage_default

        # upper operabilty
        self._oplmax = oplmax
        self._maxage = self._maxage_default
        if oplmaxtype in ['AGE','age']:
            self._oplmaxtype = 'AGE'
            self._maxage = oplmax
        elif oplmaxtype in ['VOL', 'vol']:
            self._oplmaxtype = 'VOL'
        elif oplmaxtype in ['RMV', 'rmv']:
            self._oplmaxtype = 'RMV'
        elif oplmaxtype in ['RMM', 'rmm']:
            self._oplmaxtype = 'RMM'
        elif oplmaxtype in ['BA', 'ba']:
            self._oplmaxtype = 'BA'
        #else:
        #    self._maxage = self._maxage_default

        self._offset = offset
        self._offset_curve = offset_curve
        self._retain = retain
        self._future = future
        self._adjust = adjust
        self._fu_fieldname = fu_fieldname
        self._feature_stratum_id_fieldname = feature_stratum_id_fieldname
        self._treatment_stratum_id_fieldname = treatment_stratum_id_fieldname
        self._description = description
        self._type_code = type_code
        self._intensity = intensity
        #if fu_transition:
        self.set_fu_transition(fu_transition)
        self._fu_transition = fu_transition
        self._feature_stratum_assign = None
        self._treatment_stratum_assign = None
        #if feature_stratum_transition:
        #self.set_feature_stratum_transition(feature_stratum_transition)
        self._feature_stratum_transition = feature_stratum_transition
        self._feature_stratum_transition_dict = {}
        #if treatment_stratum_transition:
        #self.set_treatment_stratum_transition(treatment_stratum_transition)
        self._treatment_stratum_transition = treatment_stratum_transition
        self._treatment_stratum_transition_dict = {}
        self._produce_assign_list = []
        self._transition_assign_list = []
        self._species_code_list = []
        self._fu_set = set()
        self._fu_assign = None
        self._midrotation_treatment_dict={'precom':[], 'harvest':[]}
        self._force_extensive = False
        self._init_extensive = False
        self._is_extensive = False

    def irreg_oplmax(self):
        return self._irregoplmax # ugly hack... yuck!

    def update_operability_limits(self, total_volume_curve=None, debug=False):
        if debug: print 'Treatment.update_operability_limits() debug'
        if self._oplmintype == 'VOL':
            vol = self._oplmin
            age = total_volume_curve.age(vol, direction='l')
            if debug: print 'VOL, min:', self._oplmin, age 
            if age == -1:
                self._minage = self._minage_default
            else:
                self._minage = age
        elif self._oplmintype == 'RMV':                
            self._minage = int(self.oplmin() * total_volume_curve.max_value_age())
        elif self._oplmintype == 'RMM':
            self._minage = int(self.oplmin() * total_volume_curve.max_mai_age())
            #if debug:
            #    print 'RMM, min:', self._oplmin, total_volume_curve.max_mai_age(), self._minage
            #    #print self._id, 'total_volume_curve'
            #    #print '\n'.join(total_volume_curve.dump_xml())
        elif self._oplmintype == 'AGE':
            pass
        else:
            pass

        if self._oplmaxtype == 'VOL':
            vol = self._oplmax
            age = total_volume_curve.age(vol, direction='r')
            if debug: print 'VOL, max', self._oplmax, age 
            if age == -1:
                self._maxage = self._maxage_default
            else:
                self._maxage = age
                if debug: print 'self._maxage', self._maxage
        elif self._oplmaxtype == 'RMV':                
            self._maxage = int(self.oplmax() * total_volume_curve.max_value_age())
        elif self._oplmaxtype == 'RMM':
            if debug:
                import pdb
                pdb.set_trace()
                self._maxage = int(self.oplmax() * total_volume_curve.max_mai_age())
            else:
                self._maxage = int(self.oplmax() * total_volume_curve.max_mai_age())
        elif self._oplmaxtype == 'AGE':
            pass
        else:
            pass

        for mrt in self.midrotation_harvest_treatment_list():
            mrt.update_operability_limits(total_volume_curve)
            self._minage = mrt.minage() - mrt.future()
            self._maxage = mrt.maxage() - mrt.future()

    def set_force_extensive(self, val):
        self._force_extensive = val

    def force_extensive(self):
        return self._force_extensive

    def set_init_extensive(self, val):
        self._init_extensive = val

    def init_extensive(self):
        return self._init_extensive

    def set_extensive(self, val):
        self._is_extensive = val

    def is_extensive(self):
        return self._is_extensive

    def is_irregular(self):
        return self._type_code == self.irregular_type_code()

    def is_precommercial(self):
        return self._type_code == self.precommercial_type_code()

    def is_harvest(self):
        return self._type_code in [self.finalcut_type_code(), self.commercialthinning_type_code()]
        
    def is_commercialthinning(self):
        return self._type_code == self.commercialthinning_type_code()
        
    def is_speciescut(self):
        return self._type_code == self.speciescut_type_code()
        
    def is_finalcut(self):
        return self._type_code == self.finalcut_type_code()

    def is_special(self):
        return not (self.is_finalcut() or
                    self.is_precommercial() or
                    self.is_commercialthinning() or
                    self.is_speciescut())
        
    def add_midrotation_treatment(self, t):
        if t.is_precommercial():
            self._midrotation_treatment_dict['precom'].append(t)
            self.set_retain(max(self._retain, t.future() + t.retain()))
            if t.feature_stratum_transition():
                self.set_feature_stratum_transition(t.feature_stratum_transition())
        else:
            # assume partial cut treatment, with no net loss or gain of total harvested volume
            if not self._midrotation_treatment_dict['harvest']:
                # only add partial cut treatment if none defined
                self._midrotation_treatment_dict['harvest'].append(t)
                self._intensity = self._intensity * (1 - t.intensity())
                
    def midrotation_treatment_list(self):
        return self._midrotation_treatment_dict['precom'] + self._midrotation_treatment_dict['harvest']

    def midrotation_precommercial_treatment_list(self):
        return self._midrotation_treatment_dict['precom']
    
    def midrotation_harvest_treatment_list(self):
        return self._midrotation_treatment_dict['harvest']
    
    def midrotation_harvest_treatment(self):
        result = None
        if self._midrotation_treatment_dict['harvest']:
            result = self._midrotation_treatment_dict['harvest'][0]
        return result
        
    def set_future(self, future):
        """
        For use with mid-rotation treatments (affects product attribute generation)
        """
        self._future = future

    def future(self):
        return self._future

    def set_irregular_type_code(self, val):
        self._type_code_dict['ir'] = val

    def set_precommercial_type_code(self, val):
        self._type_code_dict['pc'] = val

    def set_commercialthinning_type_code(self, val):
        self._type_code_dict['ct'] = val

    def set_speciescut_type_code(self, val):
        self._type_code_dict['sc'] = val

    def set_finalcut_type_code(self, val):
        self._type_code_dict['fc'] = val

    def irregular_type_code(self):
        return self._type_code_dict['ir']

    def precommercial_type_code(self):
        return self._type_code_dict['pc']

    def commercialthinning_type_code(self):
        return self._type_code_dict['ct']

    def speciescut_type_code(self):
        return self._type_code_dict['sc']

    def finalcut_type_code(self):
        return self._type_code_dict['fc']

    def set_oplmin(self, oplmin):
        self._oplmin = oplmin

    def oplmin(self):
        return self._oplmin

    def set_oplmax(self, oplmax):
        self._oplmax = oplmax

    def oplmax(self):
        return self._oplmax

    def set_oplmintype(self, oplmintype):
        self._oplmintype = oplmintype

    def oplmintype(self):
        return self._oplmintype

    def set_oplmaxtype(self, oplmaxtype):
        self._oplmaxtype = oplmaxtype

    def oplmaxtype(self):
        return self._oplmaxtype

    def set_intensity(self, intensity):
        self._intensity = intensity

    def intensity(self):
        return self._intensity

    def set_type_code(self, type_code):
        self._type_code = type_code

    def type_code(self):
        return self._type_code

    def set_id(self, id):
        self._id = id

    def id(self):
        return self._id

    def set_description(self, description):
        self._description = description

    def description(self):
        return str(self._description)

    def set_label(self, label):
        self._label = label

    def label(self):
        return self._label

    def set_minage(self, minage):
        self._minage = int(minage)

    def minage(self):
        if self._minage:
            return int(self._minage)
        else:
            return self._minage_default

    def set_maxage(self, maxage):
        self._maxage = int(maxage)

    def maxage(self):
        if self._maxage:
            return int(self._maxage)
        else:
            return self._maxage_default
    def set_offset(self, offset):
        self._offset = int(offset)

    def offset(self):
        return self._offset

    def set_retain(self, retain):
        self._retain = int(retain)

    def retain(self):
        return self._retain

    def set_retaintype(self, retaintype):
        self._retaintype = int(retaintype)

    def retaintype(self):
        return self._retaintype

    def set_offset_curve(self, curve):
        self._offset_curve = curve

    def offset_curve(self):
        return self._offset_curve

    def set_adjust(self, adjust):
        assert str(adjust) in ['A', 'a', 'R', 'r'] # debug
        self._adjust = str(adjust)

    def adjust(self):
        return self._adjust

    #def set_fu_fieldname(self, fu_fieldname):
    #    self._fu_fieldname = fu_fieldname
    
    #def fu_fieldname(self):
    #   return self._fu_fieldname

    #def default_fu_fieldname(self):
    #    return self._fu_fieldname_default

    def add_species_code(self, species_code):
        self._species_code_list.append(species_code)

    def species_code_list(self):
        return self._species_code_list

    def add_produce_assign(self, assign):
        #if __debug__: print self._id, assign.dump_xml()
        self._produce_assign_list.append(assign)
        
    def add_transition_assign(self, assign):
        self._transition_assign_list.append(assign)

    def set_fu_transition(self, fu):
        self._fu_assign = Assign(self._fu_fieldname, fu)

    def fu_transition(self):
        return self._fu_transition

    def feature_stratum_transition(self):
        return self._feature_stratum_transition

    def feature_stratum_transition(self, age=None):
        if age:
            return self._feature_stratum_transition_dict[age]
        else:
            return self._feature_stratum_transition

    def has_treatment_stratum_transition(self):
        return (self._treatment_stratum_transition or self._treatment_stratum_transition_dict)

    def has_feature_stratum_transition(self):
        return (self._feature_stratum_transition or self._feature_stratum_transition_dict)

    def age_dependent_transitions(self):
        return self._feature_stratum_transition_dict

    def set_feature_stratum_transition(self, feature_stratum_id, age=None):
        if age:
            self._feature_stratum_transition_dict[age] = feature_stratum_id
        else:
            self._feature_stratum_transition = feature_stratum_id

    def treatment_stratum_transition(self, age=None):
        if age:
            if not age in self._treatment_stratum_transition_dict:
                print 'treatment.treatment_stratum_age: bad age', age
                print ' %s' % '\n ' % self._treatment_stratum_transition_dict.keys()
                return None
            return self._treatment_stratum_transition_dict[age]
        else:
            return self._treatment_stratum_transition

    def set_treatment_stratum_transition(self, treatment_stratum_id, age=None):
        if age:
            self._treatment_stratum_transition_dict[age] = treatment_stratum_id
        else:
            self._treatment_stratum_transition = treatment_stratum_id

    def add_fu(self, state):
        """Add fu code to list.
        
        Controls treatment eligibility: current fu must be in list
        for treatment to be eligible. Empty list interpreted as no fu constraint.
        """
        self._fu_set.add(state)

    def fu_set(self):
        return frozenset(self._fu_set)
    
    def is_relative_adjust(self):
        return self._adjust in ['R', 'r']        

    def is_absolute_adjust(self):
        return self._adjust in ['A', 'a']        

    def dump_xml(self):
        lines = []
        # build XML comment
        descr = ''
        if self._description: descr =': %s' % self._description
        tmp = "<!-- treatment '%(label)s'%(descr)s -->" % {'label':self._label, 'descr':descr}
        lines.append(tmp)
        
        tmp = """<treatment label="%s" """ % self._label
        if self._minage != self._minage_default:
            tmp += """minage="%s" """ % self._minage
        if self._maxage != self._maxage_default:
            tmp += """maxage="%s" """ % self._maxage

        # use either new-style curve-based age transition, or classic age transitions
        if self._offset_curve:
            tmp += """curveid="%s" """ % self._offset_curve.id()
        else:
            if self._offset != self._offset_default:
                tmp += """offset="%s" """ % self._offset
            if self.is_relative_adjust():
                tmp += """adjust="R" """
                
        if self._retain:
            tmp += """retain="%s" """ % self._retain
        if not self._produce_assign_list and not self._transition_assign_list:
            tmp += " />"
            lines.append(tmp)
            return lines
        tmp += ">"
        lines.append(tmp)
        if self._produce_assign_list:
            lines.append("<produce>")
            for assign in self._produce_assign_list:
                lines.extend(assign.dump_xml())
            lines.append("</produce>")
        if self._transition_assign_list or self._fu_transition or self._feature_stratum_transition or self._treatment_stratum_transition:
            lines.append("<transition>")
            if self._transition_assign_list:
                for assign in self._transition_assign_list:
                    lines.extend(assign.dump_xml())
            if self._fu_transition:
                lines.extend(Assign(self._fu_fieldname, self._fu_transition).dump_xml())
            if self._feature_stratum_transition:
                #debug
                if self.is_finalcut() and self.is_extensive(): print "treatment.dump_xml():", self.id(), self.label(), self.feature_stratum_transition()
                #debug
                
                lines.extend(Assign(self._feature_stratum_id_fieldname, self._feature_stratum_transition).dump_xml())
            if self._treatment_stratum_transition:
                lines.extend(Assign(self._treatment_stratum_id_fieldname, self._treatment_stratum_transition).dump_xml())
            #    lines.extend(self._feature_stratum_assign.dump_xml())
            #print "zzz", self._id, self._treatment_stratum_assign # debug
            #if self._treatment_stratum_assign:
            #    lines.extend(self._treatment_stratum_assign.dump_xml())
            lines.append("</transition>")
        lines.append("</treatment>")
        return lines
    
if __name__ == "__main__":
    import copy
    
    print "test Treatment class"

    t1 = Treatment("treatment.label")
    t1.set_minage(10)
    t1.set_maxage(100)
    t1.set_offset(1)
    t1.set_retain(11)
    t1.set_adjust("R")

    a1 = Assign("numeric.field.name", "999")
    a2 = Assign("string.field.name", "'foo'")

    t1.add_produce_assign(a1)
    t1.add_transition_assign(a2)
    t1.set_feature_stratum_transition("new.feature.stratum")

    t2 = copy.copy(t1)
    t2.set_description("bogus treatment description")

    print "dump XML"
    print "\n".join(t1.dump_xml())
    print "\n".join(t2.dump_xml())
