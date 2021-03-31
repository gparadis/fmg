class Define:
    """
    ForestModel define element data class
    """

    def __init__(self, field, value="", is_constant=False):
        self._field = field
        self._value = value
        self._is_constant = is_constant

    def field(self):
        return self._field

    def value(self):
        return self._value

    def is_constant(self):
        return self._is_constant

    def dump_xml(self):
        lines = []
        value_keyword = ""
        if self._is_constant:
            value_keyword = "constant"
        else:
            value_keyword = "column"
        if self._value:
            lines.append("""<define field="%(field)s" %(value_keyword)s="%(value)s" />""" \
                         % {"field":self._field,
                            "value_keyword":value_keyword,
                            "value":self._value})
        else:
            lines.append("""<define field="%s" />""" % self._field)
        return lines


if __name__ == "__main__":
    # test code for Define class
    
    print "test Define class..."
    d = Define("field.name", "COLUMN.NAME", False)
    print "\n".join(d.dump_xml())
    d = Define("field.name", "'foo,bar'", True)
    print "\n".join(d.dump_xml())

