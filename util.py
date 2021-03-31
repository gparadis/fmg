#import os
#import sylvaii
#import csv
# from forestmodel import ForestModel
# from input import Input
# from define import Define
# from assign import Assign
# from retention import Retention
# from retentionstratum import RetentionStratum
# from successionstratum import SuccessionStratum
# from featurestratum import FeatureStratum
# from treatmentstratum import TreatmentStratum
# from productstratum import ProductStratum
# from attribute import Attribute
# from curve import Curve
# from expression import Expression
# from attributes import Attributes
# from succession import Succession
# from treatment import Treatment
# from productdistribution import ProductDistribution
# from attributedescriptor import AttributeDescriptor
# from retention import Retention

# from fmg.forestmodel import ForestModel
# from fmg.input import Input
# from fmg.define import Define
# from fmg.assign import Assign
# from fmg.retention import Retention
# from fmg.retentionstratum import RetentionStratum
# from fmg.successionstratum import SuccessionStratum
# from fmg.featurestratum import FeatureStratum
# from fmg.treatmentstratum import TreatmentStratum
# from fmg.productstratum import ProductStratum
# from fmg.attribute import Attribute
# from fmg.curve import Curve
# from fmg.expression import Expression
# from fmg.attributes import Attributes
# from fmg.succession import Succession
# from fmg.treatment import Treatment
# from fmg.productdistribution import ProductDistribution
# from fmg.attributedescriptor import AttributeDescriptor
# from fmg.retention import Retention

from famcourb import FamCourb

import time
 
def print_timing(func):
    def wrapper(*arg):
        t1 = time.clock()
        res = func(*arg)
        t2 = time.clock()
        print '%s took %0.3fms.' % (func.func_name, (t2-t1)*1000.)
        return res
    return wrapper

def load_forestmodel_retention_strata(forestmodel):
    from retentionstratum import RetentionStratum
    from retention import Retention
    for i in range(0,1000):
        forestmodel.add_retention_stratum(RetentionStratum(id="%03d"%i,
                                                           retention=Retention(float(i)*0.001)))

    
def gen_forestmodel(horizon,
                    year,
                    input_area="AREA",
                    input_block="BLOCK",
                    input_age="AGE",
                    input_exclude="",
                    add_defines=True,
                    invasion=True):
    """
    Generate empty ForestModel object with default values
    """
    from forestmodel import ForestModel
    from input import Input
    fm = ForestModel(horizon, year, invasion=invasion)
    fm.set_input_element(Input(input_area,
                               input_block,
                               input_age,
                               input_exclude))
    if add_defines:
        add_forestmodel_defines(fm)
    return fm


def load_forestmodel_attribute_data(forestmodel, dbpath):
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()

    cursor.execute("SELECT * FROM attribute")
    for row in cursor.fetchall():
        if row.ATTRIBUTE_ID not in forestmodel.attribute_id_list():
            forestmodel.add_attribute(Attribute(id=row.ATTRIBUTE_ID,
                                                label=row.LABEL,
                                                cycle=bool(row.CYCLE),
                                                factor=row.FACTOR,
                                                future=row.FUTURE,
                                                is_volume=bool(row.IS_VOLUME),
                                                species_code=row.SPECIES_CODE))
            forestmodel.attribute(row.ATTRIBUTE_ID).set_expression(Expression(row.EXPRESSION))
    cnxn.close()
    return forestmodel

def load_forestmodel_track_filter(forestmodel,
                                  dbpath,
                                  tablename,
                                  tsid_fieldname,
                                  fsid_fieldname):
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT %s, %s FROM %s" % (tsid_fieldname, fsid_fieldname, tablename))
    for row in cursor.fetchall():
        forestmodel.add_track_filter(row[0], row[1])
    cnxn.close()
    return forestmodel

def load_forestmodel_utr_theme(forestmodel, dbpath):
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    utr_list = []
    cursor.execute("SELECT * FROM utr")
    for row in cursor.fetchall():
        utr_list.append(row.UTR_ID)
    forestmodel.add_woodstock_landscape_theme('utr', utr_list)
    

def load_forestmodel_attributes_data(forestmodel, dbpath):
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()

    cursor.execute("SELECT * FROM attributes")
    for row in cursor.fetchall():
        if row.ATTRIBUTES_ID not in forestmodel.attributes_id_list():
            forestmodel.add_attributes(Attributes(row.ATTRIBUTES_ID,
                                                  cycle=row.CYCLE,
                                                  factor=row.FACTOR,
                                                  is_volume=bool(row.IS_VOLUME)))
    cursor.execute("SELECT * FROM attributes")
    for row in cursor.fetchall():
        a = forestmodel.attribute(row.ATTRIBUTE_ID)
        forestmodel.attributes(row.ATTRIBUTES_ID).add_attribute(Attribute(a.label(),
                                                                          id=row.ATTRIBUTE_ID,
                                                                          is_ref=True,
                                                                          is_volume=a.is_volume()))
    cnxn.close()
    return forestmodel

def add_forestmodel_treatment(forestmodel,
                              finalcut_treatment,
                              precommercial_treatment=None,
                              partialcut_treatment=None):
    """
    Assumes all treatments are final cut treatments.

    Mid-rotation treatments can be tacked on to front or back (depending on type),
    with future product attributes generated appropriately.
    """

    if partialcut_treatment:
        # assume no volume loss or gain for partial cut treatments
        intensity = finalcut_treatment.intensity() - partialcut_treatment.intensity()
        finalcut_treatment.set_intensity(intensity)
        

def load_forestmodel_treatments(forestmodel, dbpath):
    from treatment import Treatment
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()

    cursor.execute("SELECT * FROM treatment")
    for row in cursor.fetchall():
        if not row.ACTIVE: continue
        #label = row.LABEL if row.LABEL else ""
        #id = row.TREATMENT_ID if row.TREATMENT_ID
        forestmodel.add_treatment(Treatment(label=row.LABEL,
                                            id=row.TREATMENT_ID,
                                            oplmin=row.OPLMIN,
                                            oplmintype=row.OPLMINTYPE,
                                            oplmax=row.OPLMAX,
                                            oplmaxtype=row.OPLMAXTYPE,
                                            offset=row.OFFSET,
                                            retain=row.RETAIN,
                                            future=row.FUTURE,
                                            adjust=row.ADJUST,
                                            type_code=row.TYPE_CODE,
                                            fu_transition=row.FU_TRANSITION,
                                            feature_stratum_transition=row.FEATURE_STRATUM_TRANSITION,
                                            treatment_stratum_transition=row.TREATMENT_STRATUM_TRANSITION,
                                            intensity=row.INTENSITY,
                                            irregoplmax=row.IRREGOPLMAX, # ugly hack... yuck!
                                            description=row.DESCRIPTION,
                                            next_pass_treatment_id=row.NEXT_PASS_TREATMENT_ID))
    cursor.execute("SELECT * FROM treatment_detail")
    for row in cursor.fetchall():
        forestmodel.add_treatment_species_code(treatment_id=row.TREATMENT_ID,
                                               species_code=row.SPECIES_CODE)
    cursor.execute("SELECT * FROM feature_stratum_transition")
    for row in cursor.fetchall():
        forestmodel.add_feature_stratum_transition(treatment_id=row.TREATMENT_ID,
                                                   from_feature_stratum_id=row.FROM_FEATURE_STRATUM_ID,
                                                   to_feature_stratum_id=row.TO_FEATURE_STRATUM_ID)
    cursor.execute("SELECT * FROM produce")
    for row in cursor.fetchall():
        forestmodel.treatment(row.TREATMENT_ID).add_produce_assign(Assign(row.FIELD, row.VALUE))
    cnxn.close()
    return forestmodel
    

def load_forestmodel_retention_strata(forestmodel, dbpath=""):
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()

    cursor.execute("SELECT * FROM retention_stratum")
    for row in cursor.fetchall():
        forestmodel.add_retention_stratum(RetentionStratum(row.RETENTION_STRATUM_ID,
                                                           Retention(row.FACTOR),
                                                           row.DESCRIPTION))
    cnxn.close()
    return forestmodel


def load_forestmodel_succession_strata(forestmodel, dbpath=""):
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM succession_stratum")
    for row in cursor.fetchall():
        s = Succession(row.BREAKUP_AGE, row.RENEW_AGE)
        s.add_assign(Assign("feature_stratum_id", row.RENEW_FEATURE_STRATUM_ID))
        forestmodel.add_succession_stratum(SuccessionStratum(r.SUCCESSION_STRATUM_ID,
                                                             s,
                                                             row.DESCRIPTION))
    cnxn.close()
    return forestmodel


def load_forestmodel_succession_strata(forestmodel, dbpath=""):
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM succession_stratum")
    for row in cursor.fetchall():
        s = Succession(row.BREAKUP_AGE, row.RENEW_AGE)
        s.add_assign(Assign("feature_stratum_id", row.RENEW_FEATURE_STRATUM_ID))
        forestmodel.add_succession_stratum(SuccessionStratum(r.SUCCESSION_STRATUM_ID,
                                                             s,
                                                             row.DESCRIPTION))
    cnxn.close()
    return forestmodel


def load_forestmodel_product_distributions(forestmodel, dbpath=""):
    from curve import Curve
    from productdistribution import ProductDistribution
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM product_distribution")
    pd_dict = {}
    for row in cursor.fetchall():
        pdid = row.PRODUCT_DISTRIBUTION_ID
        pd_dict[pdid] = ProductDistribution(pdid)
    cursor.execute("SELECT * FROM product_distribution_curves")
    for row in cursor.fetchall():
        pdid = row.PRODUCT_DISTRIBUTION_ID
        pd = pd_dict[pdid]
        sc = row.SPECIES_CODE
        pc = row.PRODUCT_CODE
        curveid = "%(pdid)s.%(sc)s.%(pc)s" % {"pdid":pdid, "sc":sc, "pc":pc}
        if not pd.curve(sc, pc):
            pd.set_curve(sc, pc, Curve(curveid))
        pd.curve(sc, pc).add_point(row.X, row.Y)
    cnxn.close()
    for pdid in pd_dict:
        forestmodel.add_product_distribution(pd_dict[pdid])
    return forestmodel

  
def load_forestmodel_treatment_strata(forestmodel, dbpath):
    from treatmentstratum import TreatmentStratum
    import pyodbc
    import copy
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()

    cursor.execute("SELECT * FROM treatment_stratum")
    for row in cursor.fetchall():
        if row.TREATMENT_STRATUM_ID not in forestmodel.treatment_stratum_id_list():
            forestmodel.add_treatment_stratum(TreatmentStratum(row.TREATMENT_STRATUM_ID))
    cursor.execute("SELECT * FROM treatment_stratum_detail")
    for row in cursor.fetchall():
        if not row.ACTIVE or not forestmodel.treatment(row.TREATMENT_ID):
            continue
        t = copy.deepcopy(forestmodel.treatment(row.TREATMENT_ID))
        t.set_force_extensive(bool(row.FORCE_EXTENSIVE))
        t.set_init_extensive(bool(row.INIT_EXTENSIVE))
        #if __debug__:
        #    print row.TREATMENT_STRATUM_ID, row.TREATMENT_ID
        forestmodel.treatment_stratum(row.TREATMENT_STRATUM_ID).add_treatment(t)
    cursor.execute("SELECT * FROM feature_stratum_transition")
    for row in cursor.fetchall():
        forestmodel.add_feature_stratum_transition(row.TREATMENT_ID,
                                                   row.FROM_FEATURE_STRATUM_ID,
                                                   row.TO_FEATURE_STRATUM_ID)
    cnxn.close()    
    return forestmodel


def load_forestmodel_curves(forestmodel, dbpath, curve_tablename="curve", curve_detail_tablename="curve_detail"):
    from curve import Curve
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM %s" % curve_tablename)
    tmp = {}
    for row in cursor.fetchall():
        if row.CURVE_ID not in forestmodel.curve_id_list():
            c = Curve(id=row.CURVE_ID)
            forestmodel.add_curve(c)
            tmp[row.CURVE_ID] = (row.EXTRAPOLATE_LEFT_STEPS, row.EXTRAPOLATE_RIGHT_STEPS)
    cursor.execute("SELECT * FROM %s" % curve_detail_tablename)
    for row in cursor.fetchall():
        #if curveid not in forestmodel.curve_id_list():
        #    forestmodel.add_curve(Curve(id=curveid))
        c = forestmodel.curve(row.CURVE_ID)
        c.add_point(row.X, row.Y)
    cnxn.close()
    for id in forestmodel.curve_id_list():
        c = forestmodel.curve(id)
        if id not in tmp: continue
        #print "extrapolating", id
        c.extrapolate(tmp[id][0], tmp[id][1])
        #for x in c.age_list(update=True):
        #    print x, c.value(x)
        #print "\n".join(c.dump_xml())

    return forestmodel


def load_forestmodel_defines(forestmodel, dbpath, tablename="defines"):
    from define import Define
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM %s" % tablename)
    for row in cursor.fetchall():
        forestmodel.add_define(Define(row.FIELD, row.VALUE,bool(row.IS_CONSTANT)))
    cnxn.close()
    return forestmodel


def load_forestmodel_species_groups(forestmodel, dbpath, tablename="species_groups"):
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM %s" % tablename)
    for row in cursor.fetchall():
        forestmodel.set_species_group(row.SPECIES_GROUP, row.SPECIES_CODE, row.GROUP_CODE)
    cnxn.close()
    return forestmodel


def load_forestmodel_expressions(forestmodel, dbpath, tablename="expressions"):
    from expression import Expression
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM %s" % tablename)
    for row in cursor.fetchall():
        if not row.ACTIVE: continue
        forestmodel.add_expression(Expression(statement=row.STATEMENT, id=row.EXPRESSION_ID))
    cnxn.close()
    return forestmodel


# def load_forestmodel_feature_attributes_irreg(forestmodel, dbpath, tablename="feature_attributes_irreg"):
#     import pyodbc
#     cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
#     cursor = cnxn.cursor()
#     cursor.execute("SELECT * FROM %s" % tablename)
#     for row in cursor.fetchall():
#         sirf_id = row.SIRF_ID
#         if sirf_id not in forestmodel.feature_stratum_id_list():
#             forestmodel.add_feature_stratum()
            
#         # do something
#     cnxn.close()
#     return forestmodel


def load_forestmodel_feature_attributes_irreg(forestmodel,
                                              dbpath,
                                              tablename="feature_attributes_irreg",
                                              show_progress=True):
    from curve import Curve
    from attribute import Attribute
    import pyodbc
    ad_dict = compile_attribute_descriptor_dict(dbpath)
    
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM %s" % tablename)
    rows = cursor.fetchall();
    
    if __debug__ and show_progress:
        import progressbar
        print "Loading irregular feature attributes into ForestModel..."
        p = progressbar.ProgressBar(maxval=len(rows)).start()
        i = 0
    curve_dict = {}
    for row in rows:
        if __debug__ and show_progress:
            p.update(i)
            i += 1
        if not row.CURVE_ID in ad_dict["feature"]:
            continue
        ad = ad_dict["feature"][row.CURVE_ID]        
        fsid = row.STRATUM_ID
        #if fsid not in forestmodel.feature_stratum_id_list():
        #    forestmodel.add_feature_stratum(FeatureStratum(fsid, treatment_stratum_id=fsid))
        #    forestmodel.add_treatment_stratum(TreatmentStratum(fsid))
        #    forestmodel.add_track_filter(fsid, fsid)
        fs = forestmodel.feature_stratum(fsid)


        
        key = (row.STRATUM_ID, row.CURVE_ID)
        if key not in curve_dict:
            #c = Curve(id=row.CURVE_ID)
            c = Curve()
            curve_dict[key] = c
            #ad = ad_dict["feature"][row.CURVE_ID]
            fs.add_attribute(Attribute(label=ad.label(),
                                       id=row.CURVE_ID,
                                       is_ref=False,
                                       curve=c,
                                       descriptor=ad,
                                       suppress_id=True))
        c = curve_dict[key]
        c.add_point(row.AGE, row.VALUE)
    if __debug__ and show_progress:
        p.finish()
    cnxn.close()
    return forestmodel 


def load_forestmodel_feature_stratum_transition_irreg(forestmodel,
                                                      dbpath,
                                                      tablename="feature_stratum_transition_irreg",
                                                      age_step_size=5,
                                                      force_dominant_transition=True,
                                                      filter_treatments=True):
    class Ndtrans:
        """
        non-dominant transition block
        """
        def __init__(self):
            self.age_list = []
            self.a1 = None
            self.a2 = None
        def to_age(self):
            assert self.a1 or self.a2
            if self.a1 and self.a2: return (self.a1+self.a2)*0.5
            elif self.a1: return self.a1
            elif self.a2: return self.a2

    from curve import Curve
    import copy
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()

    # read in entire table
    stratum_id_set = set()
    treatment_label_set = set()
    table = {}
    cursor.execute("SELECT * FROM %s ORDER BY FROM_STRATUM_ID, TREATMENT_LABEL, FROM_AGE" % tablename)
    for row in cursor.fetchall():
        key = row.FROM_STRATUM_ID+row.TREATMENT_LABEL
        if key not in table: table[key] = [[], {}]
        table[key][0].append([row.FROM_STRATUM_ID, row.TREATMENT_LABEL, row.FROM_AGE, row.TO_STRATUM_ID, row.TO_AGE])
        #print table[key][1]
        if row.TO_STRATUM_ID not in table[key][1]: table[key][1][row.TO_STRATUM_ID] = 1
        table[key][1][row.TO_STRATUM_ID] += 1
        stratum_id_set.add(row.FROM_STRATUM_ID)
        if forestmodel.treatment(row.TREATMENT_LABEL):
            treatment_label_set.add(row.TREATMENT_LABEL)

    for from_stratum_id in stratum_id_set:
        fs = forestmodel.feature_stratum(from_stratum_id)
        for treatment_label in treatment_label_set:
            key = from_stratum_id+treatment_label
            
            #print 'key', key
            #print fs.treatment_stratum_id_list()
            
            for tsid in fs.treatment_stratum_id_list():
                ts = forestmodel.treatment_stratum(tsid)
                if treatment_label not in ts.treatment_label_list():
                    #print "skipping", treatment_label, ts.treatment_label_list()
                    continue
                #else:
                    #print "processing", treatment_label, ts.treatment_label_list()
                rows = table[key][0]
                transition_dict = {}
                for row in rows:
                    #print row
                    transition_dict[row[2]] = (row[3], row[4])
                from_age_list = copy.deepcopy(transition_dict.keys())
                from_age_list.sort()
                # build transition age curve
                cid = "%s-%s" % (from_stratum_id, treatment_label)
                c = Curve(id=cid)
                forestmodel.add_curve(c)
                t = ts.treatment(row[1])

                #print forestmodel._treatment_stratum_dict.keys()
                #print 'XXX', ts._treatment_map
                #print row
                #print tsid, ts
                #for foo in ts.treatment_list():
                #    print foo.id()

                if (force_dominant_transition):
                    dt = sorted(table[key][1], lambda x, y: table[key][1][x] - table[key][1][y]).pop()
                    # scan for contiguous age-blocks of non-dominant transition records                    
                    b_list = []
                    b = None
                    a1 = None
                    for from_age in from_age_list:
                        if not b:
                            if transition_dict[from_age][0] != dt:
                                # start new block
                                b = Ndtrans()
                                b.age_list.append(from_age)
                                b.a1 = a1
                            else:
                                a1 = transition_dict[from_age][1]
                        else:
                            if transition_dict[from_age][0] != dt:
                                b.age_list.append(from_age)
                            else:
                                # finish block
                                b.a2 = transition_dict[from_age][1]
                                b_list.append(b)
                                # process block
                                for aa in b.age_list:
                                    transition_dict[aa] = (dt, b.to_age())
                                b = None
                    ttsid = "%s-%s" % (dt, t.treatment_stratum_transition())
                    for from_age in from_age_list:
                        c.add_point(from_age, transition_dict[from_age][1])
                        t.set_feature_stratum_transition(dt, from_age)
                        t.set_treatment_stratum_transition(ttsid, from_age)
                    # for backwards compatibility with ForestModel output
                    t.set_feature_stratum_transition(dt)
                    t.set_treatment_stratum_transition(ttsid)
                else: # not forcing dominant transition (allow variable transition)
                    #print t
                    tstt = t.treatment_stratum_transition() # treatment stratum transition template code
                    for from_age in from_age_list:
                        c.add_point(from_age, transition_dict[from_age][1])
                        t.set_feature_stratum_transition(transition_dict[from_age][0], from_age)
                        ttsid = "%s-%s" % (transition_dict[from_age][0], tstt)
                        t.set_treatment_stratum_transition(ttsid, from_age)
                        #print fs.id(), from_age, transition_dict[from_age][0], transition_dict[from_age][1], ttsid
                        

                t.set_minage(from_age_list[0])
                if t.irreg_oplmax():
                    # use age of last explicit transition as maximum operable age
                    t.set_maxage(from_age_list[len(from_age_list)-1])
                t.set_offset_curve(c)
                #print fs.id(), ts.id(), t.id(), t.irreg_oplmax(), t.minage(), t.maxage()


################################################################################
# old code (date 20080306)
################################################################################
# def load_forestmodel_feature_stratum_transition_irreg(forestmodel,
#                                                       dbpath,
#                                                       tablename="feature_stratum_transition_irreg",
#                                                       age_step_size=5,
#                                                       force_dominant_transition=True,
#                                                       filter_treatments=True):
#     import copy
#     import pyodbc
#     cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
#     cursor = cnxn.cursor()

#     # build list of unique STRATUM_ID, TREATMENT_LABEL and SITECLASS values
#     stratum_id_set = set()
#     treatment_label_set = set()
#     siteclass_set = set()
#     cursor.execute("SELECT * FROM %s" % tablename)
#     for row in cursor.fetchall():
#         stratum_id_set.add(row.FROM_STRATUM_ID)
#         treatment_label_set.add(row.TREATMENT_LABEL)
#         siteclass_set.add(row.TREATMENT_LABEL)
#     #treatment_filter = None
#     #if filter_treatments:
#     #    treatment_filter = compile_treatment_stratum_detail_irreg(dbpath)
#     for from_stratum_id in stratum_id_set:
#         fs = forestmodel.feature_stratum(from_stratum_id)
#         for treatment_label in treatment_label_set:
#             for tsid in fs.treatment_stratum_id_list():
#                 ts = forestmodel.treatment_stratum(tsid)
#                 if not ts.treatment(treatment_label): continue
#                 #if treatment_filter and (from_stratum_id, treatment_label) not in treatment_filter: continue
#                 cursor.execute("SELECT * FROM %s WHERE FROM_STRATUM_ID = '%s' AND TREATMENT_LABEL = '%s' ORDER BY FROM_AGE ASC"
#                                % (tablename, from_stratum_id, treatment_label))
#                 if (force_dominant_transition):
#                     # find dominant transition
#                     tmp_dict = {} # tally TO_STRATUM_ID code frequencies to determine dominant transition
#                     transition_dict = {}
#                     for row in cursor.fetchall():
#                         transition_dict[row.FROM_AGE] = (row.TO_STRATUM_ID, row.TO_AGE)
#                         if row.TO_STRATUM_ID not in tmp_dict:
#                             tmp_dict[row.TO_STRATUM_ID] = 0
#                         tmp_dict[row.TO_STRATUM_ID] += 1
#                     dominant_transition = ("", 0)
#                     for key in tmp_dict:
#                         if tmp_dict[key] > dominant_transition[1]:
#                             dominant_transition = (key, tmp_dict[key])
#                     dt = dominant_transition[0]

#                     from_age_list = copy.deepcopy(transition_dict.keys())
#                     from_age_list.sort()
#                     # scan for contiguous age-blocks of non-dominant transition records                    
#                     b_list = []
#                     b = None
#                     a1 = None
#                     for a in from_age_list:
#                         #print "xxx", from_stratum_id, treatment_label, a, transition_dict[a], dominant_transition
#                         if not b:
#                             #print "not b", transition_dict[a][0], dt
#                             if transition_dict[a][0] != dt:
#                                 # start new block
#                                 b = Ndtrans()
#                                 b.age_list.append(a)
#                                 b.a1 = a1
#                             else:
#                                 a1 = transition_dict[a][1]
#                         else:
#                             if transition_dict[a][0] != dt:
#                                 b.age_list.append(a)
#                             else:
#                                 # finish block
#                                 b.a2 = transition_dict[a][1]
#                                 b_list.append(b)
#                                 # process block
#                                 for aa in b.age_list:
#                                     transition_dict[aa] = (dt, b.to_age())
#                                 b = None
#                     # build transition age curve
#                     cid = "%s-%s" % (from_stratum_id, treatment_label)
#                     c = Curve(id=cid)
#                     forestmodel.add_curve(c)
#                     for from_age in from_age_list:
#                         c.add_point(from_age, transition_dict[from_age][1])
#                     t = ts.treatment(row.TREATMENT_LABEL)
#                     t.set_minage(from_age_list[0])
#                     if t.irreg_oplmax():
#                         # use age of last explicit transition as maximum operable age
#                         t.set_maxage(from_age_list[len(from_age_list)-1])
#                     # to do: set max age for CMCD
#                     t.set_offset_curve(c)
#                     t.set_feature_stratum_transition(dt)
#                     ttsid = "%s-%s" % (dt, t.treatment_stratum_transition())
#                     t.set_treatment_stratum_transition(ttsid)
#                     #print "feature stratum transition:", from_stratum_id, treatment_label, ts.id(), dt, ttsid
#                 else:
#                     pass # not implemented yet...

# deprecated?
def compile_treatment_stratum_detail_irreg(dbpath,
                                           tablename="treatment_stratum_detail_irreg"):
    import pyodbc
    filter_set = set()
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM %s" % tablename)
    for row in cursor.fetchall():
        if row.CJ:
            filter_set.add((row.STRATUM_ID, row.CJ))
        if row.ESI:
            filter_set.add((row.STRATUM_ID, row.ESI))
        if row.ECS:
            filter_set.add((row.STRATUM_ID, row.ECS))
        if row.CMCD:
            filter_set.add((row.STRATUM_ID, row.CMCD))
        return filter_set


def load_forestmodel_product_attributes_irreg(forestmodel,
                                              dbpath,
                                              tablename="product_attributes_irreg",
                                              age_step_size=5,
                                              show_progress=True,
                                              filter_treatment=True,
                                              extrapolate_treatments=[],
                                              extrapolate_steps=10,
                                              combine_multipass=False):
    """
    Note:
    Call these functions first:
            load_forestmodel_feature_attributes_irreg()
            load_forestmodel_feature_stratum_transition_irreg()
    """
    from attribute import Attribute
    from productstratum import ProductStratum
    from curve import Curve
    import pyodbc
    ad_dict = compile_attribute_descriptor_dict(dbpath)
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM %s" % tablename)
    rows = cursor.fetchall();
    if __debug__ and show_progress:
        import progressbar
        print "Loading irregular product attributes into ForestModel..."
        p = progressbar.ProgressBar(maxval=len(rows)).start()
        i = 0
    curve_dict = {}
    for row in rows:
        #print row
        if __debug__ and show_progress:
            p.update(i)
            i += 1
        if not row.CURVE_ID in ad_dict["product"]:
            continue
        ad = ad_dict["product"][row.CURVE_ID]
        fsid = row.STRATUM_ID
        fs = forestmodel.feature_stratum(fsid)
        key = (row.STRATUM_ID, row.TREATMENT_LABEL, row.CURVE_ID)
        #cid = "%s-%s-%s" % (row.STRATUM_ID, row.TREATMENT_LABEL, row.CURVE_ID)
        if key not in curve_dict:
        #if cid not in forestmodel.curve_id_list():
            # add reference curve to ForestModel
            #ad = ad_dict["product"][row.CURVE_ID]
            #cid = "%s-%s" % (row.STRATUM_ID, row.CURVE_ID)
            cid = "%s-%s-%s" % (row.STRATUM_ID, row.TREATMENT_LABEL, row.CURVE_ID)
            c = Curve(id=cid)
            forestmodel.add_curve(c)
            curve_dict[key] = c
        #c = forestmodel.curve(cid)
        c = curve_dict[key]
        c.add_point(row.AGE, row.VALUE)

#             ad = ad_dict["product"][row.CURVE_ID]
#             if ad.force_reference():
#                 cid = "%s-%s" % (row.STRATUM_ID, row.CURVE_ID)
#                 c = Curve(id=cid)
#                 forestmodel.add_curve(c)
#                 a = Attribute(label=ad.label(),
#                               id=row.CURVE_ID,
#                               is_ref=False,
#                               curve=Curve(id=cid, is_ref=True),
#                               descriptor=ad,
#                               suppress_id=True)
#             else:
#                 c = Curve()
#                 a = Attribute(label=ad.label(),
#                               id=row.CURVE_ID,
#                               is_ref=False,
#                               curve=c,
#                               descriptor=ad,
#                               suppress_id=True)
#                 curve_dict[key] = c
#                 ps.add_attribute(a)
#             c = curve_dict[key]
#             c.add_point(row.AGE, row.VALUE)
        
        for tsid in fs.treatment_stratum_id_list():
             if not forestmodel.treatment_stratum(tsid).treatment(row.TREATMENT_LABEL): continue
             psid = forestmodel.product_stratum_id(tsid,
                                                   fsid,
                                                   row.TREATMENT_LABEL)
             if not forestmodel.product_stratum(psid):
                 forestmodel.add_product_stratum(ProductStratum(id=psid,
                                                                treatment_stratum_id=tsid,
                                                                feature_stratum_id=fsid,
                                                                current_treatment_id=row.TREATMENT_LABEL))
             ps = forestmodel.product_stratum(psid)
             a = Attribute(label=ad.label(),
                          id=row.CURVE_ID,
                          is_ref=False,
                          #curve=Curve(id=cid, is_ref=True),
                          curve=Curve(id=c.id(), is_ref=True),
                          descriptor=ad,
                          suppress_id=True)
             ps.add_attribute(a)
    #print 'extrapolate treatments', extrapolate_treatments
    for key in [key for key in curve_dict.keys() if key[1] in extrapolate_treatments]:
        #print 'extrapolating curves for key', key
        #curve_dict[key].dump_csv()
        curve_dict[key].extrapolate(0, extrapolate_steps, sample=5)
        #curve_dict[key].dump_csv()
        

    if __debug__ and show_progress:
        p.finish() 
    cnxn.close()
    return forestmodel


def compile_attribute_descriptor_dict(dbpath, tablename="attribute_descriptors_irreg"):
    from attributedescriptor import AttributeDescriptor
    ad_dict = {"feature":{}, "product":{}}
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM %s" % tablename)
    for row in cursor.fetchall():
        if not (row.IS_CURVE_ID and row.ACTIVE): continue
        ad_dict[row.TYPE_CODE][row.CURVE_ID] = \
            AttributeDescriptor(id=row.CURVE_ID,
                                type_code=row.TYPE_CODE,
                                attribute_code=row.ATTRIBUTE_CODE,
                                is_total=row.IS_TOTAL,
                                is_residual=row.IS_RESIDUAL,
                                is_percent=row.IS_PERCENT,
                                is_value=row.IS_VALUE,
                                is_volume=row.IS_VOLUME,
                                is_basalarea=row.IS_BASALAREA,
                                is_dbh=row.IS_DBH,
                                is_stemvol=row.IS_STEMVOL,
                                is_stemsperha=row.IS_STEMSPERHA,
                                force_reference=row.FORCE_REFERENCE,
                                species_code=row.SPECIES_CODE,
                                product_code=row.PRODUCT_CODE,
                                extrapolate_steps_left=row.EXTRAPOLATE_STEPS_LEFT,
                                extrapolate_steps_right=row.EXTRAPOLATE_STEPS_RIGHT,
                                description="")
    cnxn.close()
    return ad_dict


def load_forestmodel_product_attributes(forestmodel, dbpath, tablename="product_attributes"):
    from attribute import Attribute
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM %s" % tablename)
    for row in cursor.fetchall():
        if not row.ACTIVE: continue
        a = Attribute(label=row.LABEL,
                      id=row.ID,
                      is_ref=False,
                      force_local=row.FORCE_LOCAL)
        if row.CURVE_ID:
            a.set_curve(Curve(id=row.CURVE_ID, is_ref=True))
        elif row.EXPRESSION_ID:
            if __debug__:
                #print row.FEATURE_STRATUM_ID, row.TREATMENT_STRATUM_ID, row.TREATMENT_ID, row.ID, row.LABEL, row.CURVE_ID, row.EXPRESSION_ID
                assert forestmodel.expression(row.EXPRESSION_ID)
            a.set_expression(forestmodel.expression(row.EXPRESSION_ID))
        forestmodel.add_product_attribute(row.FEATURE_STRATUM_ID, row.TREATMENT_STRATUM_ID, row.TREATMENT_ID, a)
    #for key in forestmodel._product_attribute_dict:
    #    print key
    #    for item in forestmodel._product_attribute_dict[key]:
    #        print "\n".join(item.dump_xml())
    cnxn.close()
    return forestmodel

def load_forestmodel_feature_attributes(forestmodel, dbpath, tablename="feature_attributes"):
    from curve import Curve
    from attribute import Attribute
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM %s" % tablename)
    for row in cursor.fetchall():
        fs = forestmodel.feature_stratum(row.FEATURE_STRATUM_ID)
        if not fs: continue
        if row.ID not in forestmodel.attribute_id_list():
            a = Attribute(label=row.LABEL,
                          id=row.ID,
                          is_ref=False)
            if row.CURVE_ID:
                a.set_curve(Curve(id=row.CURVE_ID, is_ref=True))
            elif row.EXPRESSION_ID:
                a.set_expression(forestmodel.expression(row.EXPRESSION_ID))
            forestmodel.add_attribute(a)
        fs.add_attribute(Attribute(label=row.LABEL,
                                   id=row.ID,
                                   is_ref=True,
                                   factor=row.FACTOR))
    cnxn.close()
    return forestmodel


def add_forestmodel_defines(forestmodel):
    from fmg.define import Define
    
    forestmodel.add_define(Define("status","STATUS"))
    forestmodel.add_define(Define("retention_stratum_id", "R_ID"))
    forestmodel.add_define(Define("succession_stratum_id", "S_ID"))
    forestmodel.add_define(Define("feature_stratum_id", "F_ID"))
    forestmodel.add_define(Define("treatment_stratum_id", "T_ID"))
    forestmodel.add_define(Define("sn_feature_stratum_id","SN_F_ID"))
    forestmodel.add_define(Define("sn_age","SN_AGE"))
    forestmodel.add_define(Define("fc_feature_stratum_id","FC_F_ID"))
    forestmodel.add_define(Define("fc_age","FC_AGE"))

    forestmodel.add_define(Define("managed", "'managed,MANAGED'", is_constant=True))
    forestmodel.add_define(Define("unmanaged", "'unmanaged,UNMANAGED'", is_constant=True))
    forestmodel.add_define(Define("product_stratum_id"))
    forestmodel.add_define(Define("treatment"))
    forestmodel.add_define(Define("fu"))

    return forestmodel


def tgscurve_to_curve(tgscurve):
    from curve import Curve
    curve = Curve(id=tgscurve.id())
    for age in tgscurve.age_list():
        curve.add_point(age, tgscurve.value(age))
    return curve


def load_forestmodel_stratum_irreg(forestmodel,
                                   dbpath,
                                   tablename="stratum_irreg",
                                   tsttablename="treatment_stratum_template_detail_irreg"):
    from featurestratum import FeatureStratum
    import pyodbc, copy
    tstdict = load_forestmodel_treatment_stratum_template_detail_irreg(forestmodel, dbpath, tsttablename)
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM %s" % tablename)
    for row in cursor.fetchall():
        fsid = row.STRATUM_ID
        fs = FeatureStratum(fsid,
                            #treatment_stratum_id=row.STRATUM_ID,
                            partial_harvest_cost_expression_id=row.PARTIAL_HARVEST_COST_EXPRESSION_ID,
                            final_harvest_cost_expression_id=row.FINAL_HARVEST_COST_EXPRESSION_ID,
                            regime="I")
        forestmodel.add_feature_stratum(fs)
        tsidlist = []
        for key in tstdict:
            tst = tstdict[key]
            ts = copy.deepcopy(tst)
            tsid = "%s-%s" % (fsid, tst.id())
            ts.set_id(tsid)
            tsidlist.append(tsid)
            forestmodel.add_treatment_stratum(ts)
            #print "addding track filter:", tsid, fsid
            forestmodel.add_track_filter(tsid, fsid)
        fs.set_treatment_stratum_id_list(tsidlist)
    cnxn.close()
    #print "TRACK FILTER SET"
    #for item in forestmodel._track_filter_set:
    #    print item
    #assert False

def load_forestmodel_treatment_stratum_template_detail_irreg(forestmodel,
                                                             dbpath,
                                                             tablename="treatment_stratum_template_detail_irreg"):
    from treatmentstratum import TreatmentStratum
    import pyodbc
    import copy
    tstdict = {}
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM %s" % tablename)
    for row in cursor.fetchall():
        if not row.ACTIVE: continue
        if row.STRATUM_ID not in tstdict:
            tstdict[row.STRATUM_ID] = TreatmentStratum(row.STRATUM_ID)
        tst = tstdict[row.STRATUM_ID]
        #print row.TREATMENT_ID
        #print forestmodel._treatment_dict.keys()
        t = copy.deepcopy(forestmodel.treatment(row.TREATMENT_ID))
        #print row.TREATMENT_ID
        if row.TREATMENT_STRATUM_TRANSITION != row.TREATMENT_ID:
            t.set_treatment_stratum_transition(row.TREATMENT_STRATUM_TRANSITION)
        t.set_retain(row.RETAIN)
        tst.add_treatment(t)
    return tstdict      
        

def load_forestmodel_sirf(forestmodel,
                          sirf,
                          force_unimodal_curves=False,
                          curve_xoffset=True,
                          product_distribution_id=""):
    """
    Deprecated
    """
    import copy
    aaid = "volume-%s" % str(sirf.id())
    aa = Attributes(id=aaid, is_volume=True)
    forestmodel.add_attributes(aa)
    fsid = sirf.id()
    fs = FeatureStratum(id=fsid,
                        invasion_factor=sirf.invasion_factor(),
                        invasion_type=sirf.invasion_type())
    if product_distribution_id:
        fs.set_product_distribution_id(product_distribution_id)
    else:
        fs.set_product_distribution_id(sirf.product_distribution_id())
    fs.add_attribute(Attributes(id=aaid,is_ref=True, is_volume=True))
    forestmodel.add_feature_stratum(fs)
    for species in sirf.species_list():
        base_curve = sirf.curve()
        assert base_curve
        curve = copy.deepcopy(base_curve)
        #if not curve: continue
        
        curveid = curve.id()
        if curve_xoffset:
            sign = ""
            if sirf.curve_xoffset(species) < 0:
                sign = "neg"
            elif sirf.curve_xoffset(species) > 0:
                sign = "pos"
            curveid += "-xoffset_%(sign)s%(xoffset)s" % \
                       {"sign":sign, "xoffset":abs(sirf.curve_xoffset(species))}

        aid = "volume-%(sirfid)s-%(species)s" % {"sirfid":str(sirf.id()), "species":species}
        alabel = "%%f.volume.%%m.%s" % species
        # if attributeid not in forestmodel.attribute_id_list():

        # final harvest cost expression
        hce1 = copy.deepcopy(forestmodel.expression(sirf.final_harvest_cost_expression_id()))
        hce1.set_statement(hce1.statement().replace("speciescode", species))
        hce1.set_id("%(eid)s.%(s)s" % {"eid":hce1.id(), "s":species})
        if not forestmodel.has_expression(hce1):
            forestmodel.add_expression(hce1)
        # partial harvest cost expression
        hce2 = copy.deepcopy(forestmodel.expression(sirf.partial_harvest_cost_expression_id()))
        hce2.set_statement(hce2.statement().replace("speciescode", species))
        hce2.set_id("%(eid)s.%(s)s" % {"eid":hce2.id(), "s":species})
        if not forestmodel.has_expression(hce2):
            forestmodel.add_expression(hce2)
            
        # final harvest value expression
        hve1 = copy.deepcopy(forestmodel.expression(sirf.final_harvest_value_expression_id()))
        hve1.set_statement(hve1.statement().replace("speciescode", species))
        hve1.set_statement(hve1.statement().replace("speciesgroup-account", forestmodel.species_group("account", species)))
        hve1.set_id("%(eid)s.%(s)s" % {"eid":hve1.id(), "s":species})
        if not forestmodel.has_expression(hve1):
            forestmodel.add_expression(hve1)
        # partial harvest value expression
        hve2 = copy.deepcopy(forestmodel.expression(sirf.partial_harvest_value_expression_id()))
        hve2.set_statement(hve2.statement().replace("speciescode", species))
        hve2.set_statement(hve2.statement().replace("speciesgroup-account", forestmodel.species_group("account", species)))
        hve2.set_id("%(eid)s.%(s)s" % {"eid":hve2.id(), "s":species})
        if not forestmodel.has_expression(hve2):
            forestmodel.add_expression(hve2)

        #if __debug__:
        #    print forestmodel.species_group("account", species)
        #    print hve1.statement(), hve2.statement()

            
        forestmodel.add_attribute(Attribute(id=aid,
                                            label=alabel,
                                            factor=sirf.curve_factor(species),
                                            is_volume=True,
                                            species_code=species,
                                            curve=Curve(id=curveid, is_ref=True),
                                            final_harvest_cost_expression_id=hce1.id(),
                                            partial_harvest_cost_expression_id=hce2.id(),
                                            final_harvest_value_expression_id=hve1.id(),
                                            partial_harvest_value_expression_id=hve2.id(),
                                            base_curve=base_curve))
        aa.add_attribute(Attribute(id=aid,
                                   label=alabel,
                                   is_ref=True,
                                   is_volume=True,
                                   species_code=species,
                                   final_harvest_cost_expression_id=hce1.id(),
                                   partial_harvest_cost_expression_id=hce2.id(),
                                   final_harvest_value_expression_id=hve1.id(),
                                   partial_harvest_value_expression_id=hve2.id(),
                                   base_curve=base_curve))
        
        if forestmodel.curve(curveid): continue # skip if reference curve already in forestmodel
        if force_unimodal_curves:
            curve.force_unimodal()
        forestmodel.add_curve(Curve(curveid))
        for x in curve.point_dict():
            if curve_xoffset:
                x += sirf.curve_xoffset(species)
            forestmodel.curve(curveid).add_point(x, curve.value(x))
        forestmodel.curve(curveid).update_ages()
    return forestmodel


def load_forestmodel_base_curves(forestmodel, dbpath):
    from curve import Curve
    import pyodbc
    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()
    cursor.execute("SELECT * FROM species")
    for row1 in cursor.fetchall():
        c = Curve(row1.CURVE_ID)
        cursor.execute("SELECT * FROM ltgs WHERE CODE_TGS = '%s'" % row1.CURVE_ID)
        for row2 in cursor.fetchall():
            c.add_point(row2.AGE_LTGS, row2.VOL)
        forestmodel.set_base_curve(row1.SPECIES_CODE, c)

        
def load_forestmodel_sirf2(forestmodel,
                           sirf,
                           force_unimodal_curves=False,
                           curve_xoffset=True,
                           product_distribution_id="",
                           normalise_curve_factors=True,
                           curve_factor_factor=1.0):
    """
    Implemented without grouped volume attributes.
    """
    from attribute import Attribute
    from curve import Curve
    from featurestratum import FeatureStratum
    import copy
    fsid = sirf.id()
    fs = FeatureStratum(id=fsid,
                        invasion_factor=sirf.invasion_factor(),
                        invasion_type=sirf.invasion_type(),
                        final_harvest_cost_expression_id=sirf.final_harvest_cost_expression_id(),
                        partial_harvest_cost_expression_id=sirf.partial_harvest_cost_expression_id(),
                        final_harvest_value_expression_id=sirf.final_harvest_value_expression_id(),
                        partial_harvest_value_expression_id=sirf.partial_harvest_value_expression_id())
    if product_distribution_id:
        fs.set_product_distribution_id(product_distribution_id)
    else:
        fs.set_product_distribution_id(sirf.product_distribution_id())
    forestmodel.add_feature_stratum(fs)
    for species in sirf.invasion_species_list():
        fs.enable_invasion()
        fs.set_invasion_species_factor(species, sirf.invasion_species_factor(species))

    curve_factor_sum = 0.0
    if normalise_curve_factors:
        for species in sirf.species_list():
            curve_factor_sum += sirf.curve_factor(species)
    
    for species in sirf.species_list():
        if not sirf.curve(species): continue
        base_curve = tgscurve_to_curve(sirf.curve(species))
        curve = sirf.curve(species)
        curveid = curve.id()
        if curve_xoffset:
            sign = ""
            if sirf.curve_xoffset(species) < 0:
                sign = "neg"
            elif sirf.curve_xoffset(species) > 0:
                sign = "pos"
            curveid += "-xoffset_%(sign)s%(xoffset)s" % \
                       {"sign":sign, "xoffset":abs(sirf.curve_xoffset(species))}

        aid = "volume-%(sirfid)s-%(species)s" % {"sirfid":str(sirf.id()), "species":species}
        alabel = "%%f.volume.%%m.%s" % species
        # final harvest cost expression
        hce1 = copy.deepcopy(forestmodel.expression(sirf.final_harvest_cost_expression_id()))
        hce1.set_statement(hce1.statement().replace("speciescode", species))
        hce1.set_id("%(eid)s.%(s)s" % {"eid":hce1.id(), "s":species})
        if not forestmodel.has_expression(hce1):
            forestmodel.add_expression(hce1)
        # partial harvest cost expression
        hce2 = copy.deepcopy(forestmodel.expression(sirf.partial_harvest_cost_expression_id()))
        hce2.set_statement(hce2.statement().replace("speciescode", species))
        hce2.set_id("%(eid)s.%(s)s" % {"eid":hce2.id(), "s":species})
        if not forestmodel.has_expression(hce2):
            forestmodel.add_expression(hce2)
            
        # final harvest value expression
        hve1 = copy.deepcopy(forestmodel.expression(sirf.final_harvest_value_expression_id()))
        hve1.set_statement(hve1.statement().replace("speciescode", species))
        hve1.set_statement(hve1.statement().replace("speciesgroup-account", forestmodel.species_group("account", species)))
        hve1.set_id("%(eid)s.%(s)s" % {"eid":hve1.id(), "s":species})
        if not forestmodel.has_expression(hve1):
            forestmodel.add_expression(hve1)
        # partial harvest value expression
        hve2 = copy.deepcopy(forestmodel.expression(sirf.partial_harvest_value_expression_id()))
        hve2.set_statement(hve2.statement().replace("speciescode", species))
        hve2.set_statement(hve2.statement().replace("speciesgroup-account", forestmodel.species_group("account", species)))
        hve2.set_id("%(eid)s.%(s)s" % {"eid":hve2.id(), "s":species})
        if not forestmodel.has_expression(hve2):
            forestmodel.add_expression(hve2)

        if not forestmodel.curve(curveid): # skip if reference curve already in forestmodel
            if force_unimodal_curves:
                curve.force_unimodal()
            forestmodel.add_curve(Curve(curveid))
            for x in curve.point_dict():
                if curve_xoffset:
                    x += sirf.curve_xoffset(species)
                forestmodel.curve(curveid).add_point(x, curve.value(x))
            forestmodel.curve(curveid).update_ages()

        curve_factor = sirf.curve_factor(species)
        if normalise_curve_factors and curve_factor_sum < 1.0:
            curve_factor *= curve_factor_factor/curve_factor_sum
        a = Attribute(id=aid,
                      label=alabel,
                      factor=curve_factor,
                      is_volume=True,
                      species_code=species,
                      curve=Curve(id=curveid, is_ref=True),
                      final_harvest_cost_expression_id=hce1.id(),
                      partial_harvest_cost_expression_id=hce2.id(),
                      final_harvest_value_expression_id=hve1.id(),
                      partial_harvest_value_expression_id=hve2.id(),
                      base_curve=base_curve)

        forestmodel.add_attribute(a)
        aref = copy.deepcopy(a).as_ref()
        forestmodel.add_volume_attribute(fs.id(), aref)
    #forestmodel.update_total_volume_curve(fs)
    return forestmodel

    
# declare the @ decorator just before the function, invokes print_timing()
#@print_timing
def dump_forestmodel_xml(forestmodel):
    lines = []
    lines.append("""<?xml version="1.0" encoding="ISO-8859-1"?>""")
    lines.append("""<!DOCTYPE ForestModel PUBLIC "ForestModel" "http://www.spatial.ca/ForestModel.dtd">""")
    lines.extend(forestmodel.dump_xml())
    return lines

if __name__ == "__main__":
    # test functions defined in this module

    try:
        import psyco
        psyco.log()
        psyco.full()
        #psyco.profile()
    except ImportError:
        pass

    import win32pipe
    
    import sys

    sys.path.append('Y:/')

    #from sylvaii import *
    #from famcourb import FamCourb
    #from define import Define
    #from treatment import Treatment

    #reload(sylvaii)

    from forestmodel import ForestModel
    #from fmg import attribute
    #from fmg import attributes
    #from fmg import retention
    #from fmg import select
    
    #reload(forestmodel)
    #reload(attribute)
    #reload(attributes)
    #reload(retention)
    #reload(select)
    

    horizon = 100
    year= 2000
    dbpath = "e:/projets/48-503/sync/data/fmg/fmg.mdb"
    #dbpath = "D:/work/optivert/python/data/"

    fm = gen_forestmodel(horizon, year)

    load_forestmodel_treatments(fm, dbpath=dbpath)
    load_forestmodel_stratum_irreg(fm,
                                   dbpath,
                                   "stratum_irreg",
                                   "treatment_stratum_template_detail_irreg")
    load_forestmodel_feature_attributes_irreg(fm, dbpath)
    print "Loading feature stratum transitions (irreg)..."
    load_forestmodel_feature_stratum_transition_irreg(fm, dbpath)
    #load_forestmodel_product_attributes_irreg(fm, dbpath)



    assert False

    # test generate forestmodel from CSV curves

    # assume default csv volume curve path "curve-data.csv"
    print
    print "generate forestmodel from CSV curves"
    print
    fm = gen_forestmodel(horizon, year)
    fm.set_description("foo")
    d1 = Define("column.field.name", "column.name", False) 
    d2 = Define("constant.field.name", "'foo,bar'", True)
    d3 = Define("0.constant.field.name", "'foo,bar'", True)
    fm.add_define(d1)
    fm.add_define(d2)
    fm.add_define(d3)            

    # test load sylvaii curves
    ##load_forestmodel_curve_data(fm, input_source="sylvaii", data_path=dbpath)
    
    load_forestmodel_curve_data(fm, input_source="csv", data_path=dbpath)
    load_forestmodel_attribute_data(fm, input_source="csv", data_path=dbpath)
    load_forestmodel_attributes_data(fm, input_source="csv", data_path=dbpath)
    load_forestmodel_treatment_data(fm, input_source="csv", data_path=dbpath)
    load_forestmodel_retention_strata(fm, input_source="csv", data_path=dbpath)
    load_forestmodel_succession_strata(fm, input_source="csv", data_path=dbpath)
    load_forestmodel_feature_strata(fm, input_source="csv", data_path=dbpath)
    load_forestmodel_treatment_strata(fm, input_source="csv", data_path=dbpath)
    load_forestmodel_product_strata(fm, input_source="csv", data_path=dbpath)
    
    lines = dump_forestmodel_xml(fm)
    #print "\n".join(lines)

    ofname = "fmtest1.xml"
    of = open(ofname, "w")
    of.writelines(lines)
    of.close()

    # assume 'tidy' command installed (clean up XML output file)
    cmd = "tidy -xml -m -i %s" % os.getcwd()+"\\"+ofname
    print "running 'tidy' using command:"
    print cmd
    rslt = win32pipe.popen(cmd)
    if len(rslt.readlines()):
        print "tidy errors:", rslt.readlines()



