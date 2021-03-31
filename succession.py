class Succession:
    """
    ForestModel succession element data
    """

    _renew_default = 0

    #_breakup = _breakup_default
    #_renew = _breakup_default

    def __init__(self, breakup, renew):
        self._breakup = int(breakup)
        self._renew = int(renew)
        self._assign_list = []

    def set_breakup(self, breakup):
        self._breakup = int(breakup)

    def breakup(self):
        return self._breakup

    def set_renew(self, renew):
        self._renew = int(renew)

    def renew(self):
        return self._renew
    
    def add_assign(self, assign):
        self._assign_list.append(assign)

    def dump_xml(self):
        lines = []
        tmp = """<succession breakup="%s" """ % self._breakup
        if self._renew != self._renew_default:
            tmp += """renew="%s" """ % self._renew
        if not self._assign_list:
            tmp += "/>"
            lines.append(tmp)
            return lines
        else:
            tmp += ">"
            lines.append(tmp)
        if self._assign_list:
            for assign in self._assign_list:
                lines.extend(assign.dump_xml())
        lines.append("</succession>")
        return lines
      
if __name__ == "__main__":
    # test code for Succession class

    s = Succession(111, 11)
    a = Assign("field.name", "123")
    s.add_assign(a)
    a = Assign("field.name", "'foo'")
    s.add_assign(a)

    print "\n".join(s.dump_xml())

