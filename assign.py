class Assign:
    """
    ForsetModel assign element data
    """
    
    def __init__(self, field, value):
        self._field = field
        self._value = value

    def dump_xml(self):
        lines = []
        ################################################################################
        # todo: check if value corresponds to numeric value (skip single quotes)
        ################################################################################
        lines.append("""<assign field="%(field)s" value="'%(value)s'" />""" \
                     % {"field":self._field, "value":self._value})
        
        return lines

if __name__ == "__main__":
    print "test Assign class..."

    a = Assign("field.name", "999")
    print "\n".join(a.dump_xml())

    a = Assign("field.name", "'999'")
    print "\n".join(a.dump_xml())

