from assign import Assign

class Retention:
    """
    ForestModel retention element data
    """
    
    def __init__(self, factor):
        self._feature_list = []
        self._factor = factor
        self._assign_list = []
        self._assign_list.append(Assign("status", "UNMANAGED"))

    def factor(self):
        return self._factor

    def add_assign(self, assign):
        self._assign_list.append(assign)
    
    def add_feature(self, feature):
        self._feature_list.append(feature)

    def dump_xml(self):
        lines = []
        tmp = """<retention factor="%s" """ % self._factor
        if not self._assign_list and not self._feature_list:
            tmp += "/>"
            lines.append(tmp)
            return lines
        else:
            tmp += ">"
            lines.append(tmp)
        if self._assign_list:
            for assign in self._assign_list:
                lines.extend(assign.dump_xml())
        if self._feature_list:
            empty = False
            lines.append("<features>")
            for attribute in self._feature_list:
                lines.extend(attribute.dump_xml())
            lines.append("</features>")
        
        lines.append("</retention>")
        return lines
      
if __name__ == "__main__":
    # test code for Retention class

    r = Retention(0.99)
    aa = Assign("field.name", "123")
    r.add_assign(aa)
    aa = Assign("field.name", "'foo'")
    r.add_assign(aa)

    c = Curve()
    c.set_id("curve.id")
    c.add_point(1, 11)
    c.add_point(2, 22)
    c.add_point(3, 33)
    c.add_point(4, 44)

    a = Attribute("attribute.label")
    a.set_id("attribute.id")
    a.set_curve(c)

    r.add_feature(a)
    r.add_feature(a)

    print
    print "dump XML..."
    print "\n".join(r.dump_xml())
