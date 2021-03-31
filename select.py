class Select:
    """
    ForestModel select element data
    """
    
    _statement_default = ""

    #_statement = _statement_default
    
    def __init__(self, statement=_statement_default):
        self._statement = statement
        self._feature_attribute_list = []
        self._product_attribute_list = []
        self._treatment_dict = {}
        self._retention = None
        self._succession = None

    def is_empty(self):
        result = False
        if not (self._feature_attribute_list or
                self._product_attribute_list or
                self._treatment_dict or
                self._retention or
                self._succession):
            result = True
        return result

    def treatment_list(self):
        return self._treatment_dict.values()

    def set_statement(self, statement):
        self._statement = statement

    def retention(self):
        return self._retention

    def statement(self):
        return self._statement

    def add_feature_attribute(self, attribute):
        assert attribute
        self._feature_attribute_list.append(attribute)
        
    def add_product_attribute(self, attribute):
        self._product_attribute_list.append(attribute)

    def add_treatment(self, treatment):
        self._treatment_dict[treatment.id()] = treatment

    def treatment(self, id):
        result = None
        if id in self._treatment_dict: result = self._treatment_dict[id]
        return result
        
    def set_retention(self, retention):
        self._retention = retention
        
    def set_succession(self, succession):
        self._succession = succession
        
    def dump_xml(self):
        lines = []
        if not self._statement:
            lines.append("<select>")
        else:
            lines.append("""<select statement="%s">""" % self._statement)
        if self._feature_attribute_list:
            lines.append("<features>")
            for attribute in self._feature_attribute_list:
                lines.extend(attribute.dump_xml())
            lines.append("</features>")
        if self._product_attribute_list:
            lines.append("<products>")
            for attribute in self._product_attribute_list:
                if not attribute.is_ref():
                    attribute.set_id("")
                #if __debug__:
                #    print "select debug"
                #    print "\n".join(attribute.dump_xml())
                lines.extend(attribute.dump_xml())
            lines.append("</products>")
        if self.treatment_list():
            lines.append("<track>")
            for treatment in self.treatment_list():
                lines.extend(treatment.dump_xml())
            lines.append("</track>")
        if self._retention:
            lines.extend(self._retention.dump_xml())
        if self._succession:
            #print self._succession # debug
            lines.extend(self._succession.dump_xml())
        lines.append("</select>")
        return lines

      
if __name__ == "__main__":
    from fmg.treatment import Treatment

    reload(fmg.treatment)

    print "test Select class"

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

    a = Attributes()
    a.set_id("attributes.id")
    a.set_cycle(False)
    a.set_factor(0.1)
    a.add_attribute(a1)
    a.add_attribute(a2)
    a.add_attribute(a3)

    s = Select()
    s.set_statement("theme1='xxx'")
    s.add_feature_attribute(a1)
    s.add_product_attribute(a)

    t = Treatment("treatment.label")
    t.set_minage(10)
    t.set_maxage(100)
    t.set_offset(1)
    t.set_retain(11)
    t.set_adjust("R")
    aa1 = Assign("numeric.field.name", "999")
    aa2 = Assign("string.field.name", "'foo'")
    t.add_produce_assign(aa1)
    t.add_transition_assign(aa2)
    s.add_treatment(t)
    
    print
    print "dump XML"
    print "\n".join(s.dump_xml())

            
