import os
import dbaccess_vfp
from dbaccess_vfp import dbVFP
from famcourb import FamCourb
from fmg.curve import Curve

##reload(famcourb)

def import_fam_courb(dbpath=""):
    """
    Read curve family (familles de courbes) data from Sylva II database
    """
    # Assumes following tables exported from FoxPro database to dbpath:
    #   FILENAME    TABLENAME
    #   famc.dbf    fam_courb
    #   dcour.dbf   detai_courb 
    #   rve.dbf     repar_vol_essen

    fc_map = {}
    tmp = ""
    if not dbpath:
        # assume current working directory
        tmp = os.getcwd()
    else:
        tmp = dbpath
    db = dbVFP(tmp)

    # import curve descriptions (fam_courb)
    sqlresult = db.dbRecordSet("select * from famc")
    for record in sqlresult:
        fc = FamCourb()
        fc.set_id_fam_courb(record[0])
        fc.set_code(record[1].strip())
        fc.set_descr(record[2])
        fc.set_age_explo(record[4])
        fc.set_age_bris(record[5])
        fc_map[fc.id_fam_courb()] = fc

    # import yield data (detai_courb)
    sqlresult = db.dbRecordSet("select * from dcour")
    for record in sqlresult:
        fc_id = record[0]
        x = record[1]
        curve_type = record[2]
        y = record[3]

        # import only VOLUME curves: id_type_courb='000000000'
        if (curve_type!='000000000'):
            continue
        if fc_id not in fc_map:
            continue
        fc = fc_map[fc_id]
        if not fc.volume_curve():
            c = Curve()
            c.set_id(fc.code()+".VOLUME")
            fc.set_volume_curve(c)
        fc.volume_curve().add_point(x, y)   

    # import species data (repar_vol_essen)
    sqlresult = db.dbRecordSet("select * from rve")
    for record in sqlresult:
        fc_id = record[0]
        x = record[1]
        species = record[2]
        y = record[3]
        
        if fc_id not in fc_map:
            continue
        fc = fc_map[fc_id]
        if not fc.repar_vol_essen_curve(species):
            c = Curve()
            c.set_id(fc.code()+".ESSENCE."+species.strip())
            fc.add_repar_vol_essen_curve(species, c)
        fc.repar_vol_essen_curve(species).add_point(x, y)
        
    return fc_map

if __name__ == "__main__":
    from famcourb import FamCourb
    reload(famcourb)
##    print dir(famcourb.FamCourb)

    fc_map = import_fam_courb("d:/work/optivert/python/data")

    for id_fc in fc_map:
        print id_fc
        


