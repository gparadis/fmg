class Input:
    """
    ForestModel input element data
    """

    _exclude_default = ""

    #_exclude = _exclude_default
    
    def __init__(self, area, block, age, exclude=_exclude_default):
        self._area = area
        self._block = block
        self._age = age
        self._exclude = exclude

    def area(self):
        return self._area

    def block(self):
        return self._block

    def age(self):
        return self._age

    def set_exclude(self, exclude):
        self._exclude = exclude

    def dump_xml(self):
        lines = []
        tmp = """<input area="%(area)s" block="%(block)s" age="%(age)s" """ \
                     % {"area":self._area, "block":self._block, "age":self._age}
        if self._exclude:
            tmp += """exclude="%s" """ % self._exclude
        tmp += " />"
        lines.append(tmp)
        return lines

if __name__ == "__main__":
    i = Input("AREA", "BLOCK", "AGE")
    print i.dump_xml()
        
        
