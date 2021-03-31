class Expression:
    """
    ForestModel expression element data
    """

    def __init__(self,
                 statement="",
                 id=""):
        self._statement = str(statement)
        self._id = str(id)
        
    def id(self):
        return self._id

    def set_id(self, id):
        self._id = id

    def statement(self):
        return self._statement

    def set_statement(self, statement):
        self._statement = statement

    def dump_xml(self):
        lines = []
        lines.append("""<expression statement="%s" />""" % self._statement)
        return lines

if __name__ == "__main__":
    e = Expression("foo")
    print e.statement()
    for line in e.dump_xml():
        print line
