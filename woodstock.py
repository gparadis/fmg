# Functions to import Woodstock model data

def import_yields(modelname, 
                  fc_themenum,
                  modelpath='',
                  speciesvol_curvenames=[],
                  species_names=[],
                  totvol_curvename='',
                  ghost_species_name='',
                  ypp=5.0,
                  fc_filter=None):
    """
    Read yield curve data from Woodstock model, 
    and return FamCourb map (compatible with reassfc module).
    Assumes multi-file model (ie. YIELDS section in *.yld file)
    """

    import copy, os
    from fmg.famcourb import FamCourb
    from fmg.curve import Curve

    fc_map = {}
    tmp = ""
    if not modelpath:
        # assume cwd
        tmp = os.getcwd()
    else:
        tmp = modelpath
    yfile = open(tmp+os.sep+modelname+'.yld')

    #print yfile.readline()

    foomax = 10
    foo = 0
    fc_name = ''
    fc = None
    tmpcurve_list = []
    yname_list = []
    factor_list = None
    lcount = 0

    for line in yfile:
        foo = foo + 1
        line = line.strip()
        if line.startswith('*Y') or line.startswith('end'): 
            # wrap up previous FamCourb before starting new one
            if fc:
                #print "importing fc", fc_name
                tvc = Curve()
                tvc.add_point(0, 0)
                tmp_tvc = Curve()
                tmp_tvc.add_point(0, 0)
                svc_list = []
                
                for svcn in speciesvol_curvenames:
                    if totvol_curvename and svcn==totvol_curvename:
                        tvc = tmpcurve_list[yname_list.index(svcn)]
                    else:
                        svc0 = tmpcurve_list[yname_list.index(svcn)]
                        svc_list.append(svc0)
                if not totvol_curvename:
                    for svc in svc_list:
                        tvc = tvc + svc
                else:
                    for svc in svc_list:
                        tmp_tvc = tmp_tvc + svc
                
                fc.set_volume_curve(copy.deepcopy(tvc))
                #fc.volume_curve().dump_csv() 
                i = 0
                for svcn in speciesvol_curvenames:
                    #print svcn, totvol_curvename
                    if totvol_curvename and svcn == totvol_curvename: continue
                    svc0 = tmpcurve_list[yname_list.index(svcn)]
                    svc1 = Curve()
                    svc1.set_id(fc_name+".ESSENCE."+species_names[i])
                    for age in svc0.age_list():
                        if tvc.value(age):
                            svc1.add_point(age, svc0.value(age)/tvc.value(age))
                        else:
                            svc1.add_point(age, 0)
                    fc.add_repar_vol_essen_curve(species_names[i], copy.deepcopy(svc1))
                    i = i + 1
                
                if ghost_species_name:
                    svc1 = Curve()
                    svc1.set_id(fc_name+".ESSENCE."+ghost_species_name)
                    for age in tvc.age_list():
                        if tvc.value(age):
                            svc1.add_point(age, max(0, (tvc.value(age) - tmp_tvc.value(age))/tvc.value(age)))
                        else:
                            svc1.add_point(age, 0)
                    fc.add_repar_vol_essen_curve(ghost_species_name, copy.deepcopy(svc1))
                    

                #fc.set_volume_curve(copy.deepcopy(tvc))
                fc_map[fc_name] = copy.deepcopy(fc)
                factor_list = None
                #print fc_name
                #fc.volume_curve().dump_csv()
                #fc.repar_vol_essen_curve('sep').dump_csv()
                #fc.repar_vol_essen_curve('peu').dump_csv()
                #fc.repar_vol_essen_curve('bou').dump_csv()
                #assert len(fc_map) < 3
            if line.startswith('end'):
                break

            # new yield definition, extract mask (ignore end-of-line comments)
            masklist = line[2:].partition(';')[0].strip().split()
            fc_name = masklist[fc_themenum - 1]
            #print fc_filter
            if fc_filter and fc_name not in fc_filter: # this used to be backwards (ie. filter represented curves to exclude) 
                #skip = True
                fc = None
                print 'skipping curve set ', fc_name
                continue
            else:
                #skip = False
                print 'importing curve set', fc_name

            # debug...
            #if fc_name == 'N':
            #    print line
            #    assert False

            fc = FamCourb()
            fc.set_id_fam_courb(fc_name)
            fc.set_code(fc_name)
            #fc_map[fc_name] = copy.deepcopy(fc)
        elif line.startswith('_AGE'):
            # yield name header row (import yield names)
            yname_list = line.split()[1:]
            tmpcurve_list = []
            for yname in yname_list:
                c = Curve()
                c.set_id(yname)
                tmpcurve_list.append(c)
        elif line.startswith('*P'):
            # scaled curve (percent adjustment values)
            factor_list = [float(i)*0.01 for i in line.split()[1:]]
            for i in range(len(tmpcurve_list)):
                tmpcurve_list[i].set_factor(factor_list[i])
        elif line and not line.strip().startswith(';'): # skip blank lines and comment lines
            # data line (import curve data)
            values = line.split()
            age = int(values[0]) * 5
            for i in range(len(tmpcurve_list)):
                tmpcurve_list[i].add_point(age, float(values[i+1]))
                    
    return fc_map

if __name__ == '__main__':
    import sys, os
    path = os.getcwd()
    if path in sys.path:
        sys.path.remove(path)
    sys.path.append(path)
    sys.path.append('Volumes/grpar5/optivert/fmg')

    import os
    from famcourb import FamCourb
    from curve import Curve

    fc_map = import_yields('test2', 
                           2, 
                           '', 
                           ['Ysepdsp_n', 'Yboudsp_n','Ypeudsp_n'], 
                           ['SEP', 'BOU', 'PEU'], 

                           'Ytotdsp_n')
    print len(fc_map), 'FamCourb imported\n'

    #fc = fc_map['59CA9R001']
    #print fc.id_fam_courb()
    #print fc.volume_curve().dump_csv()
    #print fc.repar_vol_essen_curve('sep').dump_csv()
    #print fc.repar_vol_essen_curve('bou').dump_csv()

    for fc_name in fc_map:
        fc = fc_map[fc_name]
        print fc.id_fam_courb(), fc._repar_vol_essen_curve_map, fc.repar_vol_essen_curve('sep').id(), fc.repar_vol_essen_curve('bou').id(), fc.repar_vol_essen_curve('peu').id()
        for age in fc.volume_curve().age_list():
            print str(age).rjust(3), \
                  ('%.1f' % fc.volume_curve().value(age)).rjust(5), \
                  '%.2f %.2f %.2f' % (fc.repar_vol_essen_curve('sep').value(age), 
                                      fc.repar_vol_essen_curve('bou').value(age), 
                                      fc.repar_vol_essen_curve('peu').value(age))
#         print fc.volume_curve().dump_csv()
#         print fc.repar_vol_essen_curve('sep').dump_csv()
#         print fc.repar_vol_essen_curve('bou').dump_csv()
        print
