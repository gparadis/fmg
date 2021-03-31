# -*- coding: iso-8859-15 -*-

import os, sys
import dbaccess_vfp
from dbaccess_vfp import dbVFP
import tgscurve
from tgscurve import TgsCurve
from sirf import Sirf
from sir import Sir
#import progressbar

def sirf_stand_forexpert(sirf_map,
                         filename,
                         species_code_map,
                         dbh_min,
                         dbh_max,
                         null_qual_value="X",
                         output_format="csv"):
    """
    Output stand tables from sirf_list to ForExpert-compatible table (CSV).
    """
    import copy
    outfile = open(filename, "w")
    lines = []
    header_list = ["SIRF_ID", "ESS", "QUAL"]
    i = 4
    d1 = {}
    for dbh in range(dbh_min, dbh_max+1, 2):
        header_list.append(str(dbh))
        d1[dbh] = "0"
        i += 1   
    lines.append(",".join(header_list))
    st = {}
    for sirfid in sirf_map:
        if not sirf_map[sirfid].stock(): continue
        for species in species_code_map.values():
            for qual in ["A", "B", "C", "D", null_qual_value]:
                st[",".join([sirfid, species, qual])] = copy.deepcopy(d1)
    for sirfid in sirf_map:
        sirf = sirf_map[sirfid]
        if not sirf.stock(): continue
        for species in sirf.species_list():
            species2 = species_code_map[species]
            for diam in sirf.diam_list(species):
                for qual in sirf.qual_list(species, diam):
                    if not sirf.stand(species, diam, qual): continue
                    key1 = ",".join([sirfid, species2, qual])
                    #if key1 not in st:
                    #    st[key1] = copy.deepcopy(d1)
                    key2 = int(diam)
                    if int(diam) >= dbh_max:
                        key2 = dbh_max
                    val = float(st[key1][key2]) + sirf.stand(species, diam, qual)
                    st[key1][key2] = str(val)
    for key1 in st:
        lines.append(",".join([key1, ",".join(st[key1].values())]))
    outfile.write("\n".join(lines))
    outfile.close()


def _import_tse(filename,
                dbpath="",
                val_map={},
                com_species_list=None,
                idregro_pos=(19,24),
                essence_pos=(24,27),
                qual_pos=(28,29),
                diam_pos=(29,31),
                val_pos=(31,37),
                pad_idregro=True,
                skip_first_line=False,
                skip_null_values=False,
                null_qual_value=""):
    """
    Import stand or stock tables from TSE file
    """
    #print "_import_tse(), null_qual_value:", null_qual_value # debug
    
    filtering = False
    if com_species_list:
        filtering = True
    #print "val_map", type(val_map) # debug
    idregro_list = val_map.keys()
    i = 0
    for line in open(dbpath+"/"+filename, "r"):
        if skip_first_line and not i:
            i += 1
            continue
        idregro = int(line[idregro_pos[0]:idregro_pos[1]])
        if pad_idregro:
            idregro = "%05d" % idregro
        if idregro in idregro_list: continue # skip if exists
        essence = line[essence_pos[0]:essence_pos[1]].strip()
        if filtering and essence not in com_species_list: continue
        qual = line[qual_pos[0]:qual_pos[1]].strip()
        if not qual:
            #print "not qual" # debug
            qual = null_qual_value
        diam = line[diam_pos[0]:diam_pos[1]].strip()
        val = float(line[val_pos[0]:val_pos[1]])
        if skip_null_values and not val: continue
        if idregro not in val_map:
            val_map[idregro] = {}
        if essence not in val_map[idregro]:
            val_map[idregro][essence] = {}
        if diam not in val_map[idregro][essence]:
            val_map[idregro][essence][diam] = {}
        val_map[idregro][essence][diam][qual] = val 
    return val_map


def import_stand_tables_tse(filename,
                            dbpath="",
                            val_map={},
                            com_species_list=None,
                            idregro_pos=(19,24),
                            essence_pos=(24,27),
                            qual_pos=(28,29),
                            diam_pos=(29,31),
                            val_pos=(31,37),
                            pad_idregro=True,
                            skip_first_line=False,
                            null_qual_value=""):
    #print "import+_stand_tables_tse(), null_qual_value:", null_qual_value # debug
    return _import_tse(filename=filename,
                       dbpath=dbpath,
                       val_map=val_map,
                       com_species_list=com_species_list,
                       idregro_pos=idregro_pos,
                       essence_pos=essence_pos,
                       qual_pos=qual_pos,
                       diam_pos=diam_pos,
                       val_pos=val_pos,
                       pad_idregro=pad_idregro,
                       skip_first_line=skip_first_line,
                       null_qual_value=null_qual_value)


def import_stock_tables_tse(filename,
                            dbpath="",
                            val_map={},
                            com_species_list=None,
                            idregro_pos=(19,24),
                            essence_pos=(24,27),
                            qual_pos=(28,29),
                            diam_pos=(29,31),
                            val_pos=(37,44),
                            pad_idregro=True,
                            skip_first_line=False,
                            null_qual_value=""):
    #print "val_map", val_map
    #print "import+_stand_tables_tse(), null_qual_value:", null_qual_value # debug
    return _import_tse(filename=filename,
                       dbpath=dbpath,
                       val_map=val_map,
                       com_species_list=com_species_list,
                       idregro_pos=idregro_pos,
                       essence_pos=essence_pos,
                       qual_pos=qual_pos,
                       diam_pos=diam_pos,
                       val_pos=val_pos,
                       pad_idregro=pad_idregro,
                       skip_first_line=skip_first_line,
                       null_qual_value=null_qual_value)


def generate_unique_sirfids(filename,
                            dbpath="",
                            worksheet=1,
                            column_index=1):
    tmp = ""
    if not dbpath:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = dbpath
    
    import win32com.client
    xl = win32com.client.Dispatch("Excel.Application")
    xl.Workbooks.Open(tmp+"/"+filename)
    ws = xl.Worksheets(worksheet_index)
    ur = ws.UsedRange

    s = set()
    skipped_header_row = False
    for row in ur.Rows:
        if not skipped_header_row:
            skipped_header_row = True
            continue
        s.add(str(row.Cells(column_index)))
    l = list(s)
    l.sort()
    print
    print "---------------------"
    print "ORIGINAL_SIRF_ID,UNIQUE_SIRF_ID"
    i = 1
    for sirfid in l:
        print '\"%(sirfid)s\",\"%(newid)04d\"' % {"sirfid":sirfid,"newid":i}
        #print '%(sirfid)s,%(newid)04d' % {"sirfid":sirfid,"newid":i}
        i += 1
    print "---------------------"
        

    
def import_stock_tables_excel(filename,
                              dbpath="",
                              com_species_list=None,
                              uc_pos=1,
                              idregro_pos=2,
                              essence_pos=3,
                              diam_pos=4,
                              qual_pos=5,
                              val_pos=6,
                              pad_idregro=True,
                              skip_first_line=True,
                              worksheet_index=1,
                              null_qual_value=""):

    tmp = ""
    if not dbpath:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = dbpath
    
    import win32com.client
    xl = win32com.client.Dispatch("Excel.Application")
    xl.Workbooks.Open(tmp+"/"+filename)
    ws = xl.Worksheets(worksheet_index)
    ur = ws.UsedRange

    m = {}
    skipped_header_row = False
    for row in ur.Rows:
        if not skipped_header_row:
            skipped_header_row = True
            continue
        uni_co = str(row.Cells(uc_pos))
        #print uni_co, type(uni_co)
        #print uni_co, type(uni_co), m, type(m) # debug
        if uni_co not in m.keys():
            m[uni_co] = {}
        idregro = str(row.Cells(idregro_pos))
        if idregro not in m[uni_co]:
            m[uni_co][idregro] = {}
        essence = str(row.Cells(essence_pos))
        if essence not in m[uni_co][idregro]:
            m[uni_co][idregro][essence] = {}
        diam = str(row.Cells(diam_pos))
        if diam not in m[uni_co][idregro][essence]:
            m[uni_co][idregro][essence][diam] = {}
        qual = str(row.Cells(qual_pos))
        if qual=="None":
            qual = null_qual_value
        val = str(row.Cells(val_pos))
        #print uni_co, idregro, essence, diam, qual # debug
        m[uni_co][idregro][essence][diam][qual] = val
    xl.ActiveWorkbook.Close()
    return m
        
    
#    print len(row[0])
    #print row #ur.Cells(row, 1)
    #for item in row:
    #    print item


                              
                              



# def import_stock_tables_tse(filename, dbpath="", stock_map={}, com_species_list=None):
#     """
#     Import stock tables from TSE file
#     """

#     gaules = [2, 4, 6, 8]

#     filtering = False
#     if com_species_list:
#         filtering = True
    
#     idregro_list = stock_map.keys()
#     for line in open(dbpath+"/"+filename, "r"):
#         #print line # debug
#         idregro = line[19:24]
#         if idregro in idregro_list: continue # skip if exists
#         essence = line[24:27]
#         if filtering and essence not in com_species_list:
#             continue
#         cl_diam = int(line[29:31])
#         if cl_diam in gaules: continue
#         vol_ha = float(line[37:44])
#         if idregro not in stock_map:
#             stock_map[idregro] = {}
#         if essence not in stock_map[idregro]:
#             stock_map[idregro][essence] = {}
#         stock_map[idregro][essence][cl_diam] = vol_ha 
#     return stock_map

    
def import_stock_tables(dbpath="", com_species_list=None):
    """
    Import standard  (SIEF?) stock tables
    """

    gaules = [2, 4, 6, 8]

    filtering = False
    if com_species_list: filtering = True

    tmp = ""
    if not dbpath:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = dbpath
    db = dbVFP(tmp)
    stratum_id_map = {}
    stock_map = {}
    
    sqlresult = db.dbRecordSet("select * from REG_RESU")
    # record[0] -> IDREGRO
    # record[1] -> NOMREGRO
    for record in sqlresult:
        stratum_id_map[record[3].strip()] = record[2].strip()

    sqlresult = db.dbRecordSet("select * from TABLEESS")
    # record[1] -> NOMREGRO
    # record[2] -> ESSENCE
    # record[3] -> CL_DIAM
    # record[5] -> VOL_HA
    for record in sqlresult:
        idregro = stratum_id_map[record[1].strip()]
        essence = record[2].strip()
        if filtering and essence not in com_species_list:
            continue
        cl_diam = record[3]
        if cl_diam in gaules: continue
        vol_ha = record[5]
        if idregro not in stock_map:
            stock_map[idregro] = {}
        if essence not in stock_map[idregro]:
            stock_map[idregro][essence] = {}
        stock_map[idregro][essence][cl_diam] = record[5]
    return stock_map

def import_sirf_excel(dbpath="",
                      filename="sirf-summary.xls",
                      worksheet=1,
                      idregro_column=1,
                      sirfid_column=2,
                      unit_id="",
                      concat_unit_id=False):
    tmp = ""
    if not dbpath:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = dbpath
    import win32com.client
    xl = win32com.client.Dispatch("Excel.Application")
    wb = xl.Workbooks.Open(dbpath+"/"+filename)
    # todo: check if 'worksheet' is valid index or name (otherwise crashes)
    #print "import_sirf_excel()", worksheet #, xl.Worksheets(1).Name
    ws = xl.Worksheets(worksheet)
    ur = ws.UsedRange
    sirf_map = {}
    
    skipped_header_row = False    
    for row in ur.Rows:
        if not skipped_header_row:
            skipped_header_row = True
            continue # better way to do this?
        sirfid = str(row.Cells(sirfid_column)).strip()
        idregro = str(row.Cells(idregro_column)).strip()
        if concat_unit_id:
            #print worksheet, sirfid, ur.Columns.Count, ur.Rows.Count, ur.Rows(1)
            sirfid = "%(uid)s-%(sirfid)04d" % {"uid":unit_id, "sirfid":int(sirfid)}
        if sirfid not in sirf_map:
            sirf_map[sirfid] = []
        sirf_map[sirfid].append(idregro)
    wb.Close()
    del ur
    del ws
    del wb
    #del xl
    return sirf_map


def import_sirf(dbpath="", unit_id="", concat_unit_id=False):
    #print "dbpath:", dbpath
    tmp = ""
    if not dbpath:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = dbpath
    db = dbVFP(tmp)
    sirf_map = {}
    sqlresult = db.dbRecordSet("select * from sirf")
    # record[0] -> SIRF_ID
    # record[1] -> SIR_ID
    for record in sqlresult:
        key = "%(uid)s-%(sid)04d" % {"uid":unit_id, "sid":int(record[0])}
        if key not in sirf_map:
            sirf_map[key] = []
        sirf_map[key].append(record[1].strip())
    return sirf_map


def import_sir_areas(tablename="sir", dbpath="", factor=1.0, idregro_index=0, area_index=1):
    tmp = ""
    if not dbpath:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = dbpath
    db = dbVFP(tmp)
    sir_map = {}
    sqlresult = db.dbRecordSet("select * from %s" % tablename)
    # record[0] -> IDREGRO
    # record[1] -> AREA
    for record in sqlresult:
        key = record[idregro_index].strip()
        sir_map[key] = record[area_index] * factor
    return sir_map


def sirf_stock_tables(stock_map, sirf_map, sir_map, path="", filename="sirf-stock.csv"):
    """
    Generate area-weighed stock tables for SIRF (strates d'inventaire regroupées fusionnées)
    """
    tmp = ""
    if not path:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = path
    outfile = open(tmp+"/"+filename, "w")
    outfile.write("ID_SIRF,ESS,CLD,VOLHA\n")

    # generate area-weighted stock table entry for each combination of species and diameter
    sirf_stock_map = {}
    for sirf in sirf_map:
        if sirf not in sirf_stock_map: sirf_stock_map[sirf] = {}
        sum_area = 0
        for sir in sirf_map[sirf]:
            for ess in stock_map[sir]:
                if ess not in sirf_stock_map[sirf]: sirf_stock_map[sirf][ess] = {}
                for cld in stock_map[sir][ess]:
                    tmp = stock_map[sir][ess][cld]
                    if cld not in sirf_stock_map[sirf][ess]: sirf_stock_map[sirf][ess][cld] = 0
                    sir_area = 0
                    if sir in sir_map: sir_area = sir_map[sir]
                    sirf_stock_map[sirf][ess][cld] += stock_map[sir][ess][cld] * sir_area
            sum_area += sir_area
        del_list = []
        for ess in sirf_stock_map[sirf]:
            for cld in sirf_stock_map[sirf][ess]:
                if not sirf_stock_map[sirf][ess][cld]:
                    del_list.append((sirf,ess,cld))
                else:
                    sirf_stock_map[sirf][ess][cld] /= sum_area
        for i in del_list:
            del sirf_stock_map[i[0]][i[1]][i[2]]

    sirf_keys = sirf_stock_map.keys()
    sirf_keys.sort()
    for sirf in sirf_keys:
        ess_keys = sirf_stock_map[sirf].keys()
        ess_keys.sort()
        for ess in ess_keys:
            cld_keys = sirf_stock_map[sirf][ess].keys()
            cld_keys.sort()
            for cld in cld_keys:
                outfile.write(sirf+","+ess+","+str(cld)+","+str(sirf_stock_map[sirf][ess][cld])+"\n")
    outfile.close()
    return sirf_stock_map

def import_sir_curves(dbpath="",
                      tablename="sir-curveids",
                      sir_index=4,
                      inv_ess_index=11,
                      sylva_ess_index=49,
                      curveid_index=51,
                      age_index=52):
    """
    Import volume curve id for each sir/species combination.

    sir -> imported from field NOSTRINV21
    inv_ess -> imported from field ESS41
    sylva_ess -> imported from field SAESSSYL85
    curveid -> imported from field SACOCO87
    species_age -> imported from field SAAA88
    """
    print dbpath
    tmp = ""
    if not dbpath:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = dbpath
    db = dbVFP(tmp)

    sir_species_curve_map = {}
    sir_species_age_map = {}
    #species_map = {}

    #print "tablename", tablename # debug
    sqlresult = db.dbRecordSet("select * from %s" % tablename)
    for record in sqlresult:
        inv_ess = record[inv_ess_index].strip()
        sylva_ess = record[sylva_ess_index].strip()
        #if inv_ess not in species_map:
        #    species_map[inv_ess] = sylva_ess
        if not sylva_ess: continue
        sir = record[sir_index].strip()
        if sir not in sir_species_curve_map: sir_species_curve_map[sir] = {}
        if sir not in sir_species_age_map: sir_species_age_map[sir] = {}
        curveid = record[curveid_index].strip()
        age = record[age_index]
        #sir_species_curve_map[sir][sylva_ess] = curveid[:-1]+"M"
        sir_species_curve_map[sir][sylva_ess] = curveid
        sir_species_age_map[sir][sylva_ess] = age
    #return (sir_species_curve_map, sir_species_age_map, species_map)
    return (sir_species_curve_map, sir_species_age_map)


def import_sir_ages(dbpath="", tablename="sir-ages", sir_index=0, age_index=1):
    """
    Import SIR ages from DBF file.
    """
    tmp = ""
    if not dbpath:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = dbpath
    db = dbVFP(tmp)
    sir_age_map = {}
    sqlresult = db.dbRecordSet("select * from %s" % tablename)
    for record in sqlresult:
        sir = record[sir_index].strip()
        age = record[age_index]
        sir_age_map[sir] = age
    return sir_age_map


def sirf_ages(sirf_map, sir_area_map, sir_age_map):
    """
    Calculate area-weighted ages for each sirf.
    """
    
    sirf_age_map = {}
    for sirf in sirf_map:
        sirf_age_map[sirf] = 0
        sum_area = 0
        for sir in sirf_map[sirf]:
            if sir in sir_age_map and sir in sir_area_map:
                if sir_age_map[sir]==0: continue
                #print sirf, sir_age_map[sir], sir_area_map[sir]
                sirf_age_map[sirf] += sir_age_map[sir] * sir_area_map[sir]
                sum_area += sir_area_map[sir]
        sirf_age_map[sirf] /= sum_area
        #print sirf, sirf_age_map[sirf], sum_area
        #print
    return sirf_age_map


def assign_sirf_curves(sirf_map,
                       sir_area_map,
                       sir_curve_map,
                       stock_map,
                       out_path="",
                       out_filename=""):
    """
    Automatically assign reference volume curve id (from tgs.dbf)
    to each sirf/species combination.

    Curve id selected from list of proposed sir curves.
    Curve majority determined by volume representation (i.e. for each curve id, greatest
    sum of [sir_area * sir_ess_volha]).
    """

    sirf_curve_map = {}

    outfile = None
    if out_filename:
        tmp_path = ""
        if not out_path:
            # assume current working directory
            tmp_path = os.getcwd()
        else:
            tmp_path = out_path
            outfile = open(tmp_path+"/%s"%out_filename, "w")
            outfile.write("SIRF,ESS,CURVE,VOL,SUMVOL\n")

    for sirf in sirf_map:
        sirf_curve_map[sirf] = {}
        tmp_map = {}
        for sir in sirf_map[sirf]:
            if sir not in sir_curve_map or sir not in sir_area_map: continue
            for ess in stock_map[sir]:
                if ess not in tmp_map: tmp_map[ess] = {}
                sum_volha = 0
                curveid = ""
                if ess in sir_curve_map[sir]:
                    curveid = sir_curve_map[sir][ess]
                for cld in stock_map[sir][ess]:
                    sum_volha += stock_map[sir][ess][cld]
                vol = sir_area_map[sir] * sum_volha
                if curveid:
                    tmp_map[ess][sir] = (curveid, vol, sum_volha)
        for ess in tmp_map:
            vol = 0
            sum_vol = 0
            sum_volha = 0
            tmp_curveid = ""
            for sir in sirf_map[sirf]:
                if sir in tmp_map[ess] and tmp_map[ess][sir][1] > vol:
                    tmp_curveid = tmp_map[ess][sir][0]
                    sum_vol += tmp_map[ess][sir][1]
                    sum_volha += tmp_map[ess][sir][2]
            if tmp_curveid:
                sirf_curve_map[sirf][ess] = (tmp_curveid,sum_vol,sum_volha)
                if outfile:
                    outfile.write("%(sirf)s,%(ess)s,%(curveid)s,%(vol)s,%(sum_vol)s\n" % \
                                  {"sirf":sirf,
                                   "ess":ess,
                                   "curveid":tmp_curveid,
                                   "vol":int(vol),
                                   "sum_vol":int(sum_vol)})
    if outfile: outfile.close()
    return sirf_curve_map


def import_tgs_curves(dbpath="", force_unimodal=False):
    """
    Import pure species curve data from Sylva II curve database.
    """

    curve_map = {}

    tmp = ""
    if not dbpath:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = dbpath
    db = dbVFP(tmp)
    sirf_map = {}
    sqlresult = db.dbRecordSet("select * from tgs")
    for record in sqlresult:
        code_tgs = record[0]
        #assert code_tgs != "nEpnC9c18M"
        age_explo = record[1]
        curve_map[code_tgs] = TgsCurve(code_tgs, age_explo)
    sqlresult = db.dbRecordSet("select * from ltgs")
    for record in sqlresult:
        code_tgs = record[0]
        age_ltgs = record[1]
        vol = record[2]
        curve_map[code_tgs].add_point(age_ltgs, vol)

    if force_unimodal:
        for curveid in curve_map:
            curve_map[curveid].force_unimodal()
    
    return curve_map


def assign_sirf_scaled_curves(sirf_stock_map,
                              sirf_curve_map,
                              sirf_age_map,
                              tgscurve_map,
                              out_path="",
                              out_filename=""):
    """
    Assign scaled pure volume yield curve to each sirf/species combination.
    """
    for sirf in sirf_curve_map:
        for ess in sirf_curve_map[sirf]:
            code_tgs = sirf_curve_map[sirf][ess][0]
            volha = sirf_curve_map[sirf][ess][2]
            tgscurve = tgscurve_map[code_tgs]
            scaling_factor = volha / tgscurve.value(sirf_age_map[sirf])
            tgscurve.set_scaling_factor(scaling_factor)
    return sirf_curve_map


def sort_sirf_scaled_curves(sirf_curve_map):
    curve_map = {}
    for sirf in sirf_curve_map:
        for ess in sirf_curve_map[sirf]:
            code_tgs = sirf_curve_map[sirf][ess][0]


def import_com_species(dbpath="", tablename="com-species-codes"):
    """
    Import species code groups from DBF file.
    """
    tmp = ""
    if not dbpath:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = dbpath
    db = dbVFP(tmp)
    species_invsyl_map = {}
    species_sylgrp_map = {}
    sqlresult = db.dbRecordSet("select * from %s" % tablename)
    for record in sqlresult:
        species_invsyl_map[record[1].strip()] = record[1].strip()
        species_invsyl_map[record[0].strip()] = record[1].strip()
        species_sylgrp_map[record[1].strip()] = record[2].strip()
    return (species_invsyl_map, species_sylgrp_map)


def import_noncom_species(dbpath="", tablename="noncom-species-codes"):
    """
    Import species code groups from DBF file.
    """
    tmp = ""
    if not dbpath:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = dbpath
    db = dbVFP(tmp)
    species_list = []
    sqlresult = db.dbRecordSet("select * from %s" % tablename)
    for record in sqlresult:
        species_list.append(record[0].strip())
    return species_list


def compile_sirf(stock_threshold=0.0,
                 dbpath="",
                 tgs_dbpath="c:/sylva_ii/data_pe/",
                 tse_filename="",
                 sir_area_tablename="sir-area",
                 sir_area_factor=0.0001,
                 sir_idregro_index=0,
                 sir_area_index=1,
                 sir_curveid_tablename="sir-curve",
                 unit_id="",
                 concat_unit_id=False,
                 compile_curves=False,
                 force_unimodal_curves=False,
                 sir_stand_map={},
                 sir_stock_map={},
                 null_qual_value="",
                 import_sirf_source="excel",
                 tgscurve_map={},
                 sirf_sir_map={},
                 sir_area_map={},
                 sir_age_map={},
                 sir_curve_map={},
                 species_invsyl_map={},
                 species_sylgrp_map={},
                 noncom_species_list=[]):
    sir_map = {} # map SIR id strings to Sir objects
    sirf_map = {} # map SIRF id strings to Sirf objects
    
    if not dbpath:
        # assume current working directory
        dbpath = os.getcwd()
    #db = dbVFP(dbpath)
    
    # import data from databases
    sirf_sir_map = {}
    if not sirf_sir_map: 
        if import_sirf_source=="excel":
            worksheet=1
            if unit_id:
                worksheet=unit_id
            sirf_sir_map = import_sirf_excel(os.path.abspath(dbpath+"/../"),
                                             filename="sirf-summary.xls",
                                             worksheet=worksheet,
                                             idregro_column=1,
                                             sirfid_column=2,
                                             unit_id=unit_id,
                                             concat_unit_id=concat_unit_id)
        elif import_sirf_source=="dbf":
            sirf_sir_map = import_sirf(dbpath, unit_id)
            
    if compile_curves and (not sir_curve_map or not sir_age_map):
        sir_curve_map, sir_age_map = import_sir_curves(dbpath, sir_curveid_tablename)
    if not species_invsyl_map or not species_sylgrp_map:
        species_invsyl_map, species_sylgrp_map = import_com_species(dbpath)
    if not noncom_species_list:
        noncom_species_list = import_noncom_species(dbpath)
    #sir_stock_map = import_stock_tables(dbpath, com_species_list=species_invsyl_map)
    #sir_stock_map = import_stock_tables_tse(tse_filename, dbpath, sir_stock_map, com_species_list=species_invsyl_map)

    #####################################################################################################################
    # re-enable condition?
    #if compile_curves:
    #    print "sir_stock_map", sir_stock_map # debug 
    #    sir_stock_map = import_stock_tables_tse(tse_filename, dbpath, sir_stock_map, com_species_list=species_invsyl_map)
    sir_stock_map = import_stock_tables_tse(tse_filename,
                                            dbpath,
                                            sir_stock_map,
                                            com_species_list=species_invsyl_map,
                                            null_qual_value=null_qual_value)
    #####################################################################################################################
    #print "compile_sirf()", sir_stock_map # debug
    
    #if not sir_stock_map:
    #    print "sir_stock_map empty" # debug
    #    print "species_invsyl_map", species_invsyl_map
    if not sir_stand_map:
        sir_stand_map = import_stand_tables_tse(tse_filename, dbpath, sir_stand_map, com_species_list=species_invsyl_map,null_qual_value=null_qual_value)
    #sir_age_map = import_sir_ages(dbpath)
    if not sir_area_map:
        sir_area_map = import_sir_areas(sir_area_tablename, dbpath, sir_area_factor, sir_idregro_index, sir_area_index)
    if compile_curves and not tgscurve_map:
        tgscurve_map = import_tgs_curves(tgs_dbpath, force_unimodal_curves) # map curve id strings to TgsCurve objects

    for sirfid in sirf_sir_map:
        sirf = Sirf(sirfid)
        sirf_map[sirfid] = sirf
        for sirid in sirf_sir_map[sirfid]:
            #print sirid
            if sirid not in sir_area_map: continue
            if sirid not in sir_stand_map: continue
            sir = Sir(sirid)
            sir_map[sirid] = sir
            sir.set_area(sir_area_map[sirid])
            if compile_curves and sirid in sir_curve_map:
                    for species in sir_curve_map[sirid]:
                        tgscurve = tgscurve_map[sir_curve_map[sirid][species]]
                        sir.set_curve(species, tgscurve)
                        sir.set_age(species, sir_age_map[sirid][species])       
            #if sirid not in sir_stock_map:
            #    print "missing SIR,", sirid # debug
            #    continue
            #for species in sir_stand_map[sirid]:
            #    sylva_species = species_invsyl_map[species]
            #    sylva_species_group = species_sylgrp_map[sylva_species]
            #    sirf.assign_species_group(sylva_species, sylva_species_group)
            #    for diam in sir_stand_map[sirid][species]:
            #        sir.set_stock(species_invsyl_map[species], diam, sir_stock_map[sirid][species][diam])
            #print sir_stand_map # debug
            for species in sir_stand_map[sirid]:
                sylva_species = species_invsyl_map[species]
                sylva_species_group = species_sylgrp_map[sylva_species]
                sirf.assign_species_group(sylva_species, sylva_species_group)
                for diam in sir_stand_map[sirid][species]:
                    tmpsum = 0.0
                    for qual in sir_stand_map[sirid][species][diam]:
                        #if sirid=="00117" and qual=="X":
                        #    print ",".join([str(sirid),
                        #                    str(species),
                        #                    str(sylva_species),
                        #                    str(diam),
                        #                    str(qual),
                        #                    str(sir_stand_map[sirid][species][diam][qual])]) # debug
                        #print "foo2", sir.stand(sylva_species, diam, qual) # debug
                        sir.set_stand(sylva_species,
                                      diam,
                                      qual,
                                      sir_stand_map[sirid][species][diam][qual])
                        if sir_stock_map:
                            if sirid in sir_stock_map:
                                if species in sir_stock_map[sirid]:
                                    if diam in sir_stock_map[sirid][species]:
                                        tmpsum += sir_stock_map[sirid][species][diam][qual]
                    #if compile_curves and diam in sir_stock_map[sirid][species]:
                    if sir_stock_map:
                       if sirid in sir_stock_map:
                           if species in sir_stock_map[sirid]:
                               if diam in sir_stock_map[sirid][species]:
                                   #print sirid, ",", species_invsyl_map[species], ",", diam, tmpsum
                                   sir.set_stock(sylva_species,
                                                 diam,
                                                 sir.stock(sylva_species, diam) + tmpsum)
            sirf.add_sir(sir)
        sirf.update()
        if stock_threshold:
            sirf.set_stock_threshold(stock_threshold)
            sirf.clean()

    return sirf_map


def compile_sirf_access2(dbpath,
                         sirf_table_name="sirf",
                         regen_table_name="regen",
                         sirf_stock_threshold=0.0,
                         curve_species_field_name="SAESSSYL85",
                         curve_code_field_name="SACOCO87",
                         curve_age_field_name="SAAA88",
                         feature_stratum_id_filter_list=None,
                         show_progress=True,
                         force_idr="",
                         force_meanage_lookup=False):
    import pyodbc
    
    if __debug__:
        print "compiling sirf list"

    cnxn = pyodbc.connect("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % dbpath)
    cursor = cnxn.cursor()

    curve_species_field_index = 0
    curve_code_field_index = 0
    curve_age_field_index = 0
    for row in cursor.columns(table="sir_curves"):
        if row.column_name == curve_species_field_name:
            curve_species_field_index = row.ordinal - 1
        if row.column_name == curve_code_field_name:
            curve_code_field_index = row.ordinal - 1
        if row.column_name == curve_age_field_name:
            curve_age_field_index = row.ordinal - 1

    regen_dict = {}
    cursor.execute("SELECT * FROM %s" % regen_table_name)
    for row in cursor.fetchall():
        regenid = row.REGEN_ID
        if regenid not in regen_dict:
            regen_dict[regenid] = {}
        regen_dict[regenid][row.SPECIES_CODE] = row.CURVE_FACTOR

    sirf_dict = {}
    cursor.execute("SELECT * FROM %s" % sirf_table_name)
    for row in cursor.fetchall():
        if not row.ACTIVE: continue
        sirfid = row.SIRF_ID
        if feature_stratum_id_filter_list and sirfid not in feature_stratum_id_filter_list: continue
        sirf = Sirf(sirfid,
                    mean_inventory_age=row.MEAN_AGE,
                    force_meanage_lookup=force_meanage_lookup)
        sirf.has_stock = row.HAS_STOCK
        sirf.set_product_distribution_id(row.PRODUCT_DISTRIBUTION_ID)
        sirf.set_final_harvest_cost_expression_id(row.FINAL_HARVEST_COST_EXPRESSION_ID)
        sirf.set_partial_harvest_cost_expression_id(row.PARTIAL_HARVEST_COST_EXPRESSION_ID)
        sirf.set_final_harvest_value_expression_id(row.FINAL_HARVEST_VALUE_EXPRESSION_ID)
        sirf.set_partial_harvest_value_expression_id(row.PARTIAL_HARVEST_VALUE_EXPRESSION_ID)
        sirf.set_invasion(row.INVASION_FACTOR, row.INVASION_TYPE)
        if row.REGEN_ID in regen_dict and row.INVASION:
            for species_code in regen_dict[row.REGEN_ID]:
                sirf.set_invasion_species_factor(species_code, regen_dict[row.REGEN_ID][species_code])
        sirf_dict[sirfid] = sirf
    sir_dict = {}
    cursor.execute("SELECT * FROM sir_sirf")
    for row in cursor.fetchall():
        sirid = row.SIR_ID
        sir = Sir(sirid)
        sir_dict[sirid] = sir
        sir.set_sirf(str(row.SIRF_ID_1))
        sir.set_area(row.AREA)

    invsyl_dict = {}
    cursor.execute("SELECT * FROM species_codes")
    for row in cursor.fetchall():
        inv = str(row.INVENTAIRE).strip()
        syl = str(row.SYLVA).strip()
        gr1 = str(row.GROUPE1).strip()
        invsyl_dict[inv] = syl
        Sirf().assign_species_group(syl, gr1)

    tgscurve_dict = {}
    cursor.execute("SELECT * FROM tgs")
    for row in cursor.fetchall():
        code_tgs = row.CODE_TGS
        age_explo = row.AGE_EXPLO
        tgscurve = TgsCurve(code_tgs, age_explo)
        tgscurve_dict[code_tgs] = tgscurve

    for code_tgs in tgscurve_dict:
        tgscurve = tgscurve_dict[code_tgs]
        cursor.execute("SELECT * FROM ltgs WHERE CODE_TGS = '%s'" % code_tgs)
        for row in cursor.fetchall():
            tgscurve.add_point(row.AGE_LTGS, row.VOL)

    if __debug__ and show_progress:
        import progressbar
        i = 0
        p = progressbar.ProgressBar(maxval=len(sir_dict)).start()
    for sirid in sir_dict:
        i += 1
        if __debug__ and show_progress:
            p.update(i)
        sir = sir_dict[sirid]
        
        if sir.sirf() not in sirf_dict or feature_stratum_id_filter_list and sir.sirf() not in feature_stratum_id_filter_list: continue
        
        cursor.execute("SELECT * FROM sir_curves WHERE SIR_ID = '%s'" % sirid)
        for row in cursor.fetchall():
            if not row[curve_species_field_index]: continue
            species = str(row[curve_species_field_index]).strip()
            code_tgs = str(row[curve_code_field_index]).strip()
            if force_idr:
                tmp_code_tgs = code_tgs[:-1]+force_idr # strip last character, concatenate new idr
                #if __debug__:
                #    print "compile_sirf_access2, force_idr", force_idr, ":", code_tgs, tmp_code_tgs, tgscurve_dict[tmp_code_tgs]
                if tmp_code_tgs in tgscurve_dict:
                    code_tgs = tmp_code_tgs
            age = row[curve_age_field_index]
            sir.set_curve(species, tgscurve_dict[code_tgs])
            sir.set_age(species, age)

        cursor.execute("SELECT * FROM tse WHERE SIR_ID = '%s'" % sirid)
        for row in cursor.fetchall():
            ess = row.ESS
            if ess not in invsyl_dict: continue # skip non-commercial species
            qual = row.QUAL
            diam = row.DIAM
            tigesha = row.TIGESHA
            volha = row.VOLHA
            sir.set_stand(ess, diam, qual, tigesha)
            sir.set_stock(ess, diam, sir.stock(ess, diam) + volha)

        sirf = sirf_dict[sir.sirf()]
        
        if sirf.has_stock:
            sirf.add_sir(sir)
        else:
            if not sirf.sir_id_list():
                sirf.add_sir(Sir("x"))
            sirx = sirf.sir("x")
            sirx.set_area(sirx.area() + sir.area())
            cursor.execute("SELECT * FROM sirf_curves WHERE SIRF_ID = '%s'" % sirf.id())
            for row in cursor.fetchall():
                species = str(row.SPECIES).strip()
                tgscurve = tgscurve_dict[row.CODE_TGS]
                sirx.set_curve(species, tgscurve)
                sirx.set_age(species, row.AGE)
                sirx.set_stock(species, 10, row.VOLHA)

    if __debug__ and show_progress:
        p.finish()
        
    for sirfid in sirf_dict:
        if feature_stratum_id_filter_list and sirfid not in feature_stratum_id_filter_list: continue
        sirf = sirf_dict[sirfid]
        sirf.update()
        if sirf_stock_threshold:
            sirf.set_stock_threshold(sirf_stock_threshold)
        sirf.clean()
    
    cnxn.close()
    return sirf_dict

    
# def compile_sirf_access(dbpath,
#                         sirf_stock_threshold=0.0):
#     import win32com.client
#     conn = win32com.client.Dispatch(r'ADODB.Connection')
#     DSN = 'PROVIDER=Microsoft.Jet.OLEDB.4.0;DATA SOURCE=%s;' % dbpath
#     conn.Open(DSN)

#     sirf_dict = {}
#     rsname = "sirf"
#     rs = win32com.client.Dispatch(r'ADODB.Recordset')
#     rs.Open("[%s]" % rsname, conn, 1, 1)
#     while not rs.EOF:
#         sirfid = rs.Fields("SIRF_ID").Value
#         sirf = Sirf(sirfid)
#         sirf.has_stock = rs.Fields("HAS_STOCK").Value
#         sirf_dict[sirfid] = sirf
#         rs.MoveNext()

#     sir_dict = {}
#     rsname = "sir-sirf"
#     rs = win32com.client.Dispatch(r'ADODB.Recordset')
#     rs.Open("[%s]" % rsname, conn, 1, 1)
#     while not rs.EOF:
#         sirid = rs.Fields("SIR_ID").Value
#         sir = Sir(sirid)
#         sir_dict[sirid] = sir
#         sirfid1 = rs.Fields("SIRF_ID_1").Value
#         sirfid2 = rs.Fields("SIRF_ID_2").Value
#         sirfid3 = rs.Fields("SIRF_ID_3").Value
#         #         if sirfid1 not in sirf_dict:
#         #             sirf_dict[sirfid1] = Sirf(sirfid1)
#         #         if sirfid2 not in sirf_dict:
#         #             sirf_dict[sirfid2] = Sirf(sirfid2)
#         #         if sirfid3 not in sirf_dict:
#         #             sirf_dict[sirfid3] = Sirf(sirfid3)
#         sir.set_sirf_id_init(sirfid1)
#         sir.set_sirf_id_finalcut(sirfid2)
#         sir.set_sirf_id_succession(sirfid3)
#         sir.set_area(rs.Fields("AREA").Value)
#         rs.MoveNext()

#     invsyl_dict = {}
#     rsname = "species-codes"
#     rs = win32com.client.Dispatch(r'ADODB.Recordset')
#     rs.Open("[%s]" % rsname, conn, 1, 1)
#     while not rs.EOF:
#         inv = rs.Fields("INVENTAIRE").Value
#         syl = rs.Fields("SYLVA").Value
#         gr1 = rs.Fields("GROUPE1").Value
#         invsyl_dict[inv] = syl
#         Sirf().assign_species_group(syl, gr1)
#         rs.MoveNext()        

#     tgscurve_dict = {}
#     rsname = "tgs"
#     rs = win32com.client.Dispatch(r'ADODB.Recordset')
#     rs.Open("[%s]" % rsname, conn, 1, 1)
#     while not rs.EOF:
#         code_tgs = rs.Fields("CODE_TGS").Value
#         age_explo = rs.Fields("AGE_EXPLO").Value
#         tgscurve = TgsCurve(code_tgs, age_explo)
#         tgscurve_dict[code_tgs] = tgscurve
#         rs.MoveNext()

#     rsname = "ltgs"
#     for code_tgs in tgscurve_dict:
#         rs = win32com.client.Dispatch(r'ADODB.Recordset')
#         tgscurve = tgscurve_dict[code_tgs]
#         rs.Open("SELECT * FROM [%(rsname)s] WHERE [CODE_TGS] = '%(code_tgs)s'" %
#                 {"rsname":rsname, "code_tgs":code_tgs}, conn, 1, 1)
#         while not rs.EOF:
#             age_ltgs = rs.Fields("AGE_LTGS").Value
#             vol = rs.Fields("VOL").Value
#             tgscurve.add_point(age_ltgs, vol)
#             rs.MoveNext()


#     for sirid in sir_dict:
#         print sirid # debug

#         sir = sir_dict[sirid]
        
#         rsname = "sir-curves"
#         rs = win32com.client.Dispatch(r'ADODB.Recordset')
#         rs.Open("SELECT * FROM [%(rsname)s] WHERE [SIR_ID] = '%(sirid)s'" %
#                 {"rsname":rsname, "sirid":sirid}, conn, 1, 1)
#         while not rs.EOF:
#             uc = rs.Fields("UC11").Value
#             idregro = rs.Fields("NOSTRINV21").Value
#             species = rs.Fields("SAESSSYL85").Value
#             if not species: continue
            
#             # import init curve and age
#             code_tgs = rs.Fields("SACOCO87").Value
#             sir.set_curve_init(species, tgscurve_dict[code_tgs])
#             age = rs.Fields("SAAA88").Value
#             sir.set_age_init(species, age)
            
#             # import finalcut curve and age
#             code_tgs = rs.Fields("RACOCO96").Value # fix me: field name?
#             if not code_tgs: continue
#             sir.set_curve_finalcut(species, tgscurve_dict[code_tgs])
#             age = rs.Fields("RAAR97").Value	     # fix me: field name?
#             sir.set_age_finalcut(species, age)
            
#             # import succession curve and age
#             code_tgs = rs.Fields("RSCOCO105").Value # fix me: field name?
#             if not code_tgs: continue
#             sir.set_curve_init(species, tgscurve_dict[code_tgs])
#             age = rs.Fields("RSAA106").Value	      # fix me: field name?
#             sir.set_age_init(species, age)
            
#             rs.MoveNext()
            
#         #rsname = "sir-tse"
#         #rs = win32com.client.Dispatch(r'ADODB.Recordset')
#         #rs.Open("SELECT * FROM [%(rsname)s] WHERE [SIR_ID] = '%(sirid)s'" %
#         #        {"rsname":rsname, "sirid":sirid}, conn, 1, 1)
#         #while not rs.EOF:
#         #    ess = rs.Fields("ESS").Value
#         #    if ess not in invsyl_dict: continue # skip non-commercial species
#         #    qual = rs.Fields("QUAL").Value
#         #    diam = rs.Fields("DIAM").Value
#         #    tigesha = rs.Fields("TIGESHA").Value
#         #    volha = rs.Fields("VOLHA").Value
#         #    sir.set_stand(ess, diam, qual, tigesha)
#         #    sir.set_stock(ess, diam, sir.stock(ess, diam) + volsha)
#         #    rs.MoveNext()

#         sirfid_set = set([sir.sirf_id_init(),
#                           sir.sirf_id_finalcut(),
#                           sir.sirf_id_succession()])
#         for sirfid in sirfid_set:
#             sirf = sirf_dict[sirfid]
#             if sirf.has_stock:
#                 sirf.add_sir(sir)
#             else:
#                 if not sirf.sir_id_list():
#                     xsir = Sir("x")
#                 sirf.add_sir(xsir)
#                 rsname = "sirf-curves"
#                 rs = win32com.client.Dispatch(r'ADODB.Recordset')
#                 rs.Open("SELECT * FROM [%(rsname)s] WHERE [SIRF_ID] = '%(sirfid)s'" %
#                         {"rsname":rsname, "sirfid":sirfid}, conn, 1, 1)
#                 while not rs.EOF:
#                     species = rs.Fields("SPECIES").Value
#                     tgscurve = tgscurve_dict[rs.Fields("CODE_TGS").Value]
#                     xsir.set_curve_init(species, tgscurve)
#                     xsir.set_age_init(species, rs.Fields("AGE").Value)
#                     xsir.set_stock(rs.Fields("VOLHA").Value)
#                     rs.MoveNext()
#                     sirf.sir("x").set_area(sirf.sir("x").area() + sir.area())

#     for sirfid in sirf_dict: sirf = sirf_dict[sirfid] sirf.update() if
#         stock_threshold: sirf.set_stock_threshold(stock_threshold)
#         sirf.clean()

#     conn.Close()
#     return sirf_dict


def import_tse_access(dbpath, tablename="tse"):
    import win32com.client
    conn = win32com.client.Dispatch(r'ADODB.Connection')
    DSN = 'PROVIDER=Microsoft.Jet.OLEDB.4.0;DATA SOURCE=%s;' % dbpath
    conn.Open(DSN)

    #rsname = "sir-tse"
    rs = win32com.client.Dispatch(r'ADODB.Recordset')
    #rs = conn.OpenSchema(20)
    #for f in rs.Fields:
    #    print f.Name
    #while not rs.EOF:
    #    print rs.Fields("TABLE_NAME").Value
    #    rs.MoveNext()

    #rs.Open("[%s]" % rsname)
    rs.Open("[%s]" % tablename, conn, 1, 1)
    while not rs.EOF:
        ess = rs.Fields("ESS").Value
        #if ess not in invsyl_dict: continue # skip non-commercial species
        qual = rs.Fields("QUAL").Value
        diam = rs.Fields("DIAM").Value
        tigesha = rs.Fields("TIGESHA").Value
        volha = rs.Fields("VOLHA").Value
        #sir.set_stand(ess, diam, qual, tigesha)
        #sir.set_stock(ess, diam, sir.stock(ess, diam) + volsha)
        rs.MoveNext()
    conn.Close()
    return None


if __name__ == "__main__":
    #import pprint
    print "running"
    
    # Import Psyco if available
    try:
        import psyco
        psyco.log()
    #    psyco.profile()
        psyco.full()
    except ImportError:
        pass

    path_prefix = "d:/work/optivert/45-385/local/curves"
    dbpath = "%s/sir.mdb" % path_prefix
    #stand_dict = import_stand_tables_tse("tse", path_prefix)
    #print len(stand_dict)
    #import_tse_access(dbpath)
    
    stock_threshold = 0.04
    sirf_dict = compile_sirf_access2(dbpath, stock_threshold)

    

    print "done"
