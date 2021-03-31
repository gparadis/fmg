from attributedescriptor import AttributeDescriptor

class Attribute:
    """ForestModel attribute element data
    """

    _label_default = ""
    _id_default = ""
    _is_ref_default = False
    _cycle_default = True
    _factor_default = 1.0
    _future_default = 0.0
    _is_volume_default = False
    _is_value_default = False
    _species_code_default = ""
    _product_code_default = ""
    _force_local_default = False

    def __init__(self,
                 label,
                 id="",
                 is_ref=_is_ref_default,
                 cycle=_cycle_default,
                 factor=_factor_default,
                 future=_future_default,
                 is_volume=_is_volume_default,
                 is_value=_is_value_default,
                 species_code=_species_code_default,
                 product_code=_product_code_default,
                 curve=None,
                 expression=None,
                 final_harvest_cost_expression_id=None,
                 partial_harvest_cost_expression_id=None,
                 final_harvest_value_expression_id=None,
                 partial_harvest_value_expression_id=None,
                 base_curve=None,
                 descriptor=None,
                 suppress_id=False,
                 force_local=_force_local_default):
        if is_ref: assert id
        self._label = label
        #self._id = (id if id else label) # only works with Python 2.5 :(
        if id:
            self._id = id
        else:
            self._id = label
        self._is_ref = bool(is_ref)
        self._cycle = bool(cycle)
        self._factor = float(factor)
        self._future = int(future)
        if descriptor:
            self._is_volume = descriptor.is_volume()
            self._is_value = descriptor.is_value()
            self._species_code = descriptor.species_code()
            self._product_code = descriptor.product_code()
        else:
            self._is_volume = bool(is_volume)
            self._is_value = bool(is_value)
            self._species_code = species_code        
            self._product_code = product_code
        self._curve = curve
        self._expression = expression
        self._key = "%s-future%s-factor%s" % (self._id, str(future) ,str(factor))
        self._pdcid = ""
        self._final_harvest_cost_expression_id=final_harvest_cost_expression_id
        self._partial_harvest_cost_expression_id=partial_harvest_cost_expression_id
        self._final_harvest_value_expression_id=final_harvest_value_expression_id
        self._partial_harvest_value_expression_id=partial_harvest_value_expression_id
        self._base_curve = base_curve
        self._descriptor = descriptor
        self._suppress_id = suppress_id
        self._force_local = force_local

    def set_force_local(self, val):
        self._force_local = val

    def force_local(self):
        return self._force_local

    def set_suppress_id(self, val):
        self._suppress_id = val

    def set_descriptor(self, descriptor):
        self._descriptor = descriptor
    
    def has_descriptor(self):
        return not self._descriptor is None

    def descriptor(self):
        return self._descriptor
        
    def set_base_curve(self, curve):
        self._base_curve = curve

    def base_curve(self):
        return self._base_curve

    def set_final_harvest_cost_expression_id(self, e):
        self._final_harvest_cost_expression_id = e

    def final_harvest_cost_expression_id(self):
        return self._final_harvest_cost_expression_id

    def set_partial_harvest_cost_expression_id(self, e):
        self._partial_harvest_cost_expression_id = e

    def partial_harvest_cost_expression_id(self):
        return self._partial_harvest_cost_expression_id

    def set_final_harvest_value_expression_id(self, e):
        self._final_harvest_value_expression_id = e

    def final_harvest_value_expression_id(self):
        return self._final_harvest_value_expression_id

    def set_partial_harvest_value_expression_id(self, e):
        self._partial_harvest_value_expression_id = e

    def partial_harvest_value_expression_id(self):
        return self._partial_harvest_value_expression_id

    def set_product_distribution_curve_id(self, pdcid):
        self._pdcid = pdcid

    def product_curve_distribution(self):
        return self._pdcid

    def set_key(self, key):
        self._key = key

    def key(self):
        return self._key

    def is_group(self):
        return False

    def set_label(self, label):
        self._label = label

    def label(self):
        return self._label

    def _reset_defaults(self):
        self._id = self._id_default
        self._is_ref = self._is_ref_default
        self._cycle = self._cycle_default
        self._factor = self._factor_default
        self._future = self._future_default    
        self._curve = None
        self._expression = None

    def set_ref(self, idref):
        assert idref # check for null idref
        self._reset_defaults()
        self._is_ref = True
        self._id = str(idref)

    def set_is_ref(self, val):
        self._is_ref = val

    def is_ref(self):
        return self._is_ref

    def as_ref(self, ):
        import copy
        a = copy.deepcopy(self)
        a.set_ref(self._id)
        return a

    def is_volume(self):
        return self._is_volume

    def is_value(self):
        return self._is_value

    def set_species_code(self, val):
        self._species_code = val

    def species_code(self):
        return self._species_code

    def set_product_code(self, val):
        self._product_code = val

    def product_code(self):
        return self._product_code

    def set_species_code(self, species_code):
        self._species_code = species_code

    def set_id(self, id):
        self._id = id

    def id(self):
        return self._id
        
    def set_cycle(self, cycle):
        self._cycle = bool(cycle)

    def cycle(self):
        return self._cycle

    def set_factor(self, factor):
        self._factor = float(factor)

    def factor(self):
        return self._factor
        
    def set_future(self, future):
        self._future = int(future)

    def future(self):
        return self._future

    def set_curve(self, curve):
        if not self._is_ref: # and not self._expression:
            # only add curve if NOT attribute reference
            self._curve = curve

    def curve(self):
        return self._curve

    def set_expression(self, expression):
        if not self._is_ref: # and not self._curve:
            # only add expression if NOT attribute reference
            self._expression = expression

    def expression(self):
        return self._expression 
                                
    def dump_xml(self):
        lines = []
        if self._is_ref:
            tmp = """<attribute label="%s" idref="%s" """ % (self._label, self._id)
            if self.factor() != 1.0:
                tmp += """factor="%s" """ % self.factor()

            # TO DO: confirm future works for reference attribute #
            if self._future != self._future_default:
                tmp += """future="%s" """ % self._future
            #######################################################
                
            tmp += "/>"
            lines.append(tmp)
        else:
            tmp1 = []
            if self._curve:
                tmp1.extend(self._curve.dump_xml())
            elif self._expression:
                e = self._expression
                if self._factor != 1.0:
                    # this is a dirty hack to get around bug in MatrixBuilder
                    e.set_statement("%(factor)s*(%(statement)s)" % {"factor":self._factor, "statement":e.statement()})
                    self._factor = 1.0
                if isinstance(e, basestring): print e
                tmp1.extend(e.dump_xml())
            #assert self._label and (self._curve or self._expression) # debug
            tmp = """<attribute label="%s" """ % self._label
            if self._id and not self._suppress_id:
                tmp += """id="%s" """ % self._id
            if self._cycle != self._cycle_default:
                #print type(self._cycle), type(self._cycle_default)
                tmp += """cycle="%s" """ % self._cycle
            #print "attribute.dump_xml()", self.id(), self._factor, self._factor_default # debug
            if self._factor != self._factor_default:
                tmp += """factor="%s" """ % self._factor
            if self._future != self._future_default:
                tmp += """future="%s" """ % self._future
            tmp += ">"            
            lines.append(tmp)
            lines += tmp1
            lines.append("</attribute>")

        return lines
        
if __name__ == "__main__":
    print "test Attribute class"

    from expression import Expression
    from curve import Curve
    
    e = Expression("curveid('curve.id') * 10 + 99")
    c = Curve()
    c.set_id("curve.id")
    c.add_point(1, 11)
    c.add_point(2, 22)
    c.add_point(3, 33)
    c.add_point(4, 44)
    a1 = Attribute("attribute.with.curve")
    a1.set_id("attribute.id")
    a1.set_curve(c)
    print "dumping attribute values..."
    tmp = [str(a1.is_ref()),
           str(a1.id()),
           str(a1.cycle()),
           str(a1.factor()),
           str(a1.future()),
           str(a1.curve()),
           str(a1.expression())]
    print ";".join(tmp)
    print
    print "dumping a1 XML..."
    print "\n".join(a1.dump_xml())

    # try to assign expression to attribute when curve already set
    # (should ignore request and do nothing)
    print "setting a1 expression..."
    a1.set_expression(e)
    print
    print "dumping a1 XML again..."
    print "\n".join(a1.dump_xml())

    a2 = Attribute("attribute.with.expression")
    a2.set_id("attribute.id")
    a2.set_cycle(False)
    a2.set_factor(10)
    a2.set_future(5)
    a2.set_expression(e)
    print
    print "dumping a2 XML..."
    print "\n".join(a2.dump_xml())

    # try to assign curve to attribute when expression already set
    # (should ignore request and do nothing)
    print "setting a2 curve..."
    a2.set_curve(c)
    print "dumping a2 XML again..."
    print "\n".join(a2.dump_xml())

    # set a2 as reference curve
    print
    print "setting a2 as reference attribute..."
    a2.set_ref("attribute.idref")
    print "dumping a2 XML..."
    print "\n".join(a2.dump_xml())
    
    print "dumping attribute values..."
    tmp = [str(a2.is_ref()),
           str(a2.id()),
           str(a2.cycle()),
           str(a2.factor()),
           str(a2.future()),
           str(a2.curve()),
           str(a2.expression())]
    print ";".join(tmp)
