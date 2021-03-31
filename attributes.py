class Attributes:
    """ForestModel attributes element data
    """

    _id_default = ""
    _is_ref_default = False
    _cycle_default = True
    _is_volume_default = False
    _factor_default = 1.0

    def __init__(self,
                 id=_id_default,
                 is_ref=_is_ref_default,
                 cycle=_cycle_default,
                 factor=_factor_default,
                 is_volume=_is_volume_default):
        if is_ref: assert id
        self._id = id
        self._is_ref = bool(is_ref)
        self._cycle = bool(cycle)
        self._factor = float(factor)
        self._is_volume = bool(is_volume)
        self._attribute_list = []

    def _reset_defaults(self):
        self._id = self._id_default
        self._is_ref = self._is_ref_default
        self._cycle = self._cycle_default
        self._factor = self._factor_default
        self._is_volume = self._is_volume_default
        self._attribute_list = []

    def is_group(self):
        return True

    def set_id(self, id):
        self._id = str(id)

    def id(self):
        return self._id

    def set_ref(self, idref):
        assert idref # check for null idref
        self._reset_defaults()
        self._is_ref = True
        self._id = idref

    def is_ref(self):
        return self._is_ref

    def is_volume(self):
        return self._is_volume

    def set_cycle(self, cycle):
        self._cycle = cycle

    def cycle(self):
        return self._cycle

    def set_factor(self, factor):
        self._factor = factor

    def factor(self):
        return self._factor
        
    def add_attribute(self, attribute):
        self._attribute_list.append(attribute)

    def attribute_list(self):
        return self._attribute_list

    def dump_xml(self):
        lines = []
        if self._is_ref:
            lines.append("""<attributes idref="%s" />""" % self._id)
        else:
            tmp = "<attributes " # id="%s" """ % self._id
            if self._id != self._id_default:
                tmp += """id="%s" """ % self._id
            if not self._cycle:
                tmp += """cycle="false" """
            #print "attributes.dump_xml()", self._id, self._factor, self._factor_default # debug
            if self._factor != self._factor_default:
                tmp += """factor="%s" """ % self._factor
            tmp += ">"            
            lines.append(tmp)
            for attribute in self._attribute_list:
                lines.extend(attribute.dump_xml())
            lines.append("</attributes>")
        return lines

if __name__ == "__main__":
    print "test Attributes class"

    e = Expression("curveid(1.1) * 10 + 99")
    c = Curve()
    c.set_id("curve.id")
    c.add_point(1, 11)
    c.add_point(2, 22)
    c.add_point(3, 33)
    c.add_point(4, 44)

    a1 = Attribute("attribute.with.curve")
    a1.set_curve(c)

    a2 = Attribute("attribute.with.expression")
    a2.set_id("attribute.id")
    a2.set_cycle(False)
    a2.set_factor(10)
    a2.set_future(5)
    a2.set_expression(e)

    a3 = Attribute("attribute.with.idref")
    a3.set_ref("attribute.idref")

    a = Attributes("attributes.id",False,0.1)
    a.add_attribute(a1)
    a.add_attribute(a2)
    a.add_attribute(a3)

    print "dumping attribute values..."
    tmp = [str(a.is_ref()),
           str(a.id()),
           str(a.cycle()),
           str(a.factor()),
           str(a._attribute_list)]
    print ";".join(tmp)


    print
    print "dump XML..."
    print "\n".join(a.dump_xml())

    a.set_ref("attributes.id")
    print
    print "\n".join(a.dump_xml())
    print "dumping attribute values..."
    tmp = [str(a.is_ref()),
           str(a.id()),
           str(a.cycle()),
           str(a.factor()),
           str(a._attribute_list)]
    print ";".join(tmp)
