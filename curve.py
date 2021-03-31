class Curve:
    """
    ForestModel curve element data class
    """

    _id_default = ""
    _is_ref_default = False
    _age_sample_interval_default = 5
    _sigdigs_default = 5
    _factor_default = 1.0
    _prune_flat_default = True
    _max_mai_min_age = 50

    def __init__(self,
                 id=_id_default,
                 is_ref=_is_ref_default,
                 age_sample_interval=_age_sample_interval_default,
                 sigdigs=_sigdigs_default,
                 factor=_factor_default,
                 prune_flat=_prune_flat_default):
        if is_ref: assert id
        self._id = id
        self._is_ref = is_ref
        self._point_dict = {} #{0:0.0}
        self._age_list = []
        self._max_mai_age = self._max_mai_min_age
        self._max_value_age = 0
        self._is_empty = True
        self._age_sample_interval=age_sample_interval
        self._sigdigs=sigdigs
        self._factor=factor
        #self._flat = True
        #self._flat_y = 0.0
        self._prune_flat = prune_flat

    def is_flat(self):
        #return self._flat
        return len(set(self._point_dict.values())) == 1

    def is_flat_to(self, age, minage=0, tol=0.0):
        if age <= self.min_age(): return True
        if abs(self.value(minage) - self.value(age)) > tol: return False
        s = set()
        for a in range(minage, age+1):
            s.add(self.value(a))
            #if len(s) > 1: return False
        if (max(s) - min(s)) > tol: return False
        return True

    def is_flat_from(self, age, maxage=1000, tol=0.0):
        if age >= self.max_age(): return True
        if abs(self.value(maxage) - self.value(age)) > tol: return False
        s = set()
        for a in range(age, maxage+1):
            s.add(self.value(a))
            #if len(s) > 1: return False
        if (max(s) - min(s)) > tol: return False
        return True

    def is_null(self):
        return self.is_flat() and self.value(0) == 0

    def set_factor(self, factor):
        self._factor = factor

    def factor(self):
        return self._factor

    def _m(self, x1, x2, y1, y2):
        return (y2 - y1)/(x2 - x1)

    def _b(self, x, y, m):
        #print "_b", x, y, m
        return y - (m * x)

    def _extrapolate_right(self, steps, sample=2, debug=False):
        """
        Extrapolate curve data to the right.
        
        steps: number of steps (age sample intervals) to extrapolate curve
        sample: how far
        """
        from scipy import stats
        al = self.age_list(reverse=True)
        xlist = al[0:min(sample, len(al))]
        ylist = [self.value(x) for x in xlist]
        #print sample, xlist, ylist
        m, b, r_value, p_value, std_err = stats.linregress(xlist,ylist)
        #print m, b, r_value, p_value, std_err

        x1 = al[min(sample-1, len(al)-1)]
        x2 = al[0]
        y1 = self.value(x1)
        y2 = self.value(x2)
        d = steps * self._age_sample_interval

        self.add_point(x2+d, m*(x2+d)+b)


        #m = self._m(x1, x2, y1, y2)
        #if debug:
        #    print 'Curve._extrapolate_right(%s)' % steps, self._id
        #    print ' x1 x3 y1, y2 m:', x1, x2, y1, y2, m
        #    #print self._id
        #    #print x1, y1, ",", x2, y2


        if not m: return # flat line, no need to extrapolate
        #b = self._b(x1, y1, m)
        d = steps * self._age_sample_interval
        if m >= 0:
            self.add_point(x2+d, m*(x2+d)+b)
        else:
            #x_int = -b/m
            if ((-b/m)-x2) <= d:
                self.add_point(-b/m, 0)
            else:
                self.add_point(x2+d, m*(x2+d)+b)

    def _extrapolate_left(self, steps, sample=2):
        """
        Extrapolate curve data to the right.
        """
        al = self.age_list(reverse=False)
        # calculate
        
        x1 = al[0]
        x2 = al[1]
        y1 = self.value(x1)
        y2 = self.value(x2)
        m = self._m(x1, x2, y1, y2)
        if not m: return # flat line, no need to extrapolate
        b = self._b(x1, y1, m)
        d = steps * self._age_sample_interval
        #print self.id()
        #print "x1", x1, "x2", x2, "y1", y1, "y2", y2
        #print "m", m, "b", b, "d", d
        if b >= 0:
            if d >= x1:
                self.add_point(0, b)
                #print "adding point (b>=0, d>=x1):", 0, b
            else:
                self.add_point(x1-d, m*(x1-d)+b)
                #print "adding point (b>=0, d<x1):", x1-d, m*(x1-d)+b
        else:
            #x_int = -b/m
            if  (x1-(-b/m)) <= d:
                self.add_point(-b/m, 0)
                #print "adding point (b<0, x1-x_int<=d):", -b/m, 0
            else:
                self.add_point(x1-d, m*(x1-d)+b)
                #print "adding point (b<0, x1-x_int>d):", x1-d, m*(x1-d)+b

    def extrapolate(self, left_steps=10, right_steps=10, sample=3):
        """
        Extrapolates curve data in specified directions from last 3 points.
        """
        if self.is_flat() and self._prune_flat: return
        if len(self._point_dict) < 2: return # need at least 2 points to extrapolate
        if right_steps:
            self._extrapolate_right(right_steps, sample=sample)
        if left_steps:
            self._extrapolate_left(left_steps, sample=sample)
        #self._age_list = self.__age_list()

    def set_age_sample_interval(self, val):
        self._age_sample_interval = val

    def age_sample_interval(self):
        return self._age_sample_interval

    def set_sigdigs(self, sigdigs):
        self._sigdigs = sigdigs

    def sigdigs(self):
        return self._sigdigs

    def _reset_defaults(self):
        self._id = self._id_default
        self._is_ref = self._is_ref_default
        self._point_dict = {0:0.0}

    def max_mai_age(self):
        self._max_mai_age = self._max_mai_min_age
        a1 = self._max_mai_min_age + 1
        #al1 = self.age_list(update=True)
        al2 = self.age_list(reverse=True)
        a2 = al2[0]+1
        for age in range(a1, a2, 1):
            if self.mai(age) > self.mai(self._max_mai_age):
                self._max_mai_age = age
        return self._max_mai_age

    def max_value_age(self):
        self._max_value_age = 0
        al1 = self.age_list(update=True)
        al2 = self.age_list(reverse=True)
        for age in range(al1[0], al2[0]+1, 1):
            if self.value(age) > self.value(self._max_value_age):
                self._max_value_age = age
        return self._max_value_age

    def set_id(self, id):
        self._id = str(id)

    def id(self):
        return self._id

    def set_ref(self, idref):
        assert idref # check for null idref
        self._reset_defaults()
        self._is_ref = True
        self._id = str(idref)

    def is_ref(self):
        return self._is_ref

    def is_valid(self):
        return self.is_ref() or self._point_dict

    def mai(self, age):
        if not age: return 0
        return self.value(age) / age

    #     def age(self, value, direction="l", stepsize=1):
    #         if value > self.value(self._max_value_age):
    #             return -1
    #         if direction in ['L', 'l', 'LEFT', 'left']:
    #             step = 1 * stepsize
    #             age_list = self.age_list(False)
    #         else:
    #             step = -1 * stepsize
    #             age_list = self.age_list(True)
    #         rpm = (age_list[0],
    #                self._max_value_age,
    #                step) # range parameter tuple
    #         result = -1
    #         for age in range(rpm[0], rpm[1], rpm[2]):
    #             if self.value(age) > value:
    #                 result = age - rpm[2]
    #                 break
    #         return result

    def age(self, value, direction='l'):
        """
        Lookup age for given value.

        direction argument:
          if in L, l, LEFT, left: lookup from left
          if R, r, RIGHT, right: lookup from right
        """
        if direction in ['L', 'l', 'LEFT', 'left']:
            reverse = False
            rangeparams = (0, -1)
        else:
            reverse = True
            rangeparams = (1000, 1)
        lastage = 0
        for x in self.age_list(reverse=reverse):
            #print "point dict", self._point_dict
            if self._point_dict[x] == value: return x
            if self._point_dict[x] > value: # bust
                # back up in 1-year increments till bust again
                for xx in range(x, rangeparams[0], rangeparams[1]):
                    #if __debug__:
                    #    print "bust", direction, x, self.value(x), xx, self.value(xx) 
                    if self.value(xx) <= value:
                        return xx
        return -1

    def __age_list(self, reverse=False):
        result = self._point_dict.keys()
        result.sort()
        if reverse: result.reverse()
        return result

    def min_age(self, allow_negative=False):
        return sorted(self._point_dict.keys(), reverse=True).pop()
        #l = sorted(self._point_dict.keys(), reverse=True)
        #if not allow_negative:
        #    return max(l.pop(), 0)
        #else:
        #    return l.pop()

    def max_age(self):
        return sorted(self._point_dict.keys(), reverse=False).pop()

    def age_list(self, reverse=False, update=False):
        return sorted(self._point_dict.keys(), reverse=reverse)
        #import copy
        #if not self._age_list or update:
        #    self._age_list = self.__age_list()
        #result = copy.copy(self._age_list)
        #if reverse: result.reverse()
        #return result
        
        
    def value(self, age):
        """Evaluate curve at age.
        """
        if not self._point_dict: return None #0 # is this a good idea?
        result = 0.0
        #x_list = self._point_dict.keys()
        #x_list.sort()
        x_list = self.age_list()
        x_min = self.min_age() #x_list[0]
        #i_max = len(x_list) - 1
        x_max = self.max_age() #x_list[-1:][0]
        #print x_min, x_max
        if age in self._point_dict:
            result = float(self._point_dict[age])
        elif age > x_min and age < x_max:
            # interpolate
            x1 = 0
            y1 = 0
            x2 = 0
            y2 = 0
            x_last = 0
            for x in x_list:
                if age < x:
                    x1 = x_last
                    #if __debug__:
                    #    print self._point_dict
                    y1 = self._point_dict[x1]
                    x2 = x
                    y2 = self._point_dict[x2]
                    break
                x_last = x
            f = ((float(age) - float(x1)) / (float(x2) - float(x1)))
            #print x1,y1, x2, y2, f
            result = float(y1) + ((float(y2) - float(y1)) * f) 
        elif age < x_min:
            # extrapolate horizontally
            if not x_min in self._point_dict:
                print x_min, self._point_dict
            result = float(self._point_dict[x_min])
        elif age > x_max: 
            # extrapolate horizontally
            result = float(self._point_dict[x_max])
            #print 'age > x_max', age, x_max, result
        return result * self._factor

    def update_ages(self):
        self._age_list = self.__age_list()
        for age in self._age_list:
            if self.mai(age) > self.mai(self._max_mai_age):
                self._max_mai_age = age
            if self.value(age) > self.value(self._max_value_age):
                self._max_value_age = age

    def remove_point(self, x):
        if x in self._point_dict:
            del self._point_dict[x]

    def add_point(self, x, y):
        #if x < 0: return # skip negative values (break mai calculation)
        if self._is_ref: return # only add data if NOT curve reference
        #if self._point_dict:
        #    if self.is_flat() and y != self._flat_y:
        #        self._flat = False
        #else:
        #    self._flat_y = y
        self._point_dict[int(x)] = y
        self._is_empty = False

    def is_empty(self):
        return self._is_empty

    def _convert_sigdigs(self, num, digits, debug=False):
        if num < 0.000001: return 0.0
        digs, order = ('%.20e'%num).split('e') 
        order = int(order)
        if type(num) is long: digs = str(num) # Not needed for current tests
        digs = (digs.replace('.', '') + '0'*digits)[:digits]
        #if __debug__:
        #    print "curve debug", self._id ,'num=%r, order=%d, digits=%s'%(num, order, digs)
        if 0<=order<5 and order<len(digs)-1:
            return float('%s.%s'%(digs[:order+1], digs[order+1:]))
        elif -5<=order<0: 
            return float('0.%s%s'%('0'*(-order-1), digs))
        else:
            return float('%s.%se%+d'%(digs[0], digs[1:], order))

    def dump_xml(self):
        lines = []
        if self._is_ref:
            lines.append("""<curve idref="%s" />""" % self._id)
        else:
            if self._id:
                lines.append("""<curve id="%s">""" % self._id)
            else:
                lines.append("<curve>")
                
            l = self.age_list()
            #if __debug__:
            #    print "curve debug", self._id, self._point_dict
            #    assert self.__age_list
            x1 = 0
            x2 = 0
            if l:
                x1 = l[0]
                x2 = l[len(l)-1]
            step = self._age_sample_interval
            r = range((x1-(x1%step)), (x2+(step)), step)
            if self._prune_flat and self.is_flat():
                r = range(0, 1)
            for x in r:
                y = str(float(self._convert_sigdigs(self.value(x), self._sigdigs)))
                lines.append("""<point x="%(x)s" y="%(y)s" />""" % {"x":x, "y":y})
            lines.append("</curve>")
        return lines

    def dump_csv(self, nonnegative_ages=True):
        self.update_ages()
        if self._is_ref:
            print 'reference curve (no values to dump)'
            return
        else:
            print 'AGE,VALUE'
            l = self.age_list()
            x1 = 0
            x2 = 0
            if l:
                x1 = l[0]
                x2 = l[len(l)-1]
            #step = self._age_sample_interval
            #r = range((x1-(x1%step)), (x2+(step)), step)
            #if self._prune_flat and self._flat:
            #    r = range(0, 1)
            #for x in r:
            for x in self.age_list():
                if nonnegative_ages and x < 0: continue
                y = str(float(self._convert_sigdigs(self.value(x), self._sigdigs)))
                print '%s,%s' % (x, y)

    def __add__(self, other):
        age_set = set()
        age_set.update(self.age_list())
        age_set.update(other.age_list())        
        age_list = list(age_set)
        age_list.sort()
        c = Curve()
        for age in age_list:
            c.add_point(age, self.value(age)+other.value(age))
        return c

    def __mul__(self, other):
        age_set = set()
        age_set.update(self.age_list())
        age_set.update(other.age_list())        
        age_list = list(age_set)
        age_list.sort()
        c = Curve()
        for age in age_list:
            c.add_point(age, self.value(age)*other.value(age))
        return c

    def __sub__(self, other):
        age_set = set()
        age_set.update(self.age_list())
        age_set.update(other.age_list())        
        age_list = list(age_set)
        age_list.sort()
        c = Curve()
        for age in age_list:
            c.add_point(age, self.value(age)-other.value(age))
        return c

    def __div__(self, other):
        age_set = set()
        age_set.update(self.age_list())
        age_set.update(other.age_list())        
        age_list = list(age_set)
        age_list.sort()
        c = Curve()
        for age in age_list:
            if other.value(age) == 0:
                c.add_point(age, self.value(age))
            else:
                c.add_point(age, self.value(age)/other.value(age))
        return c

    
if __name__ == "__main__":
    print "test Curve class ..."

    c = Curve("curve.id", age_sample_interval=5)
    c.add_point(0, 0)
    c.add_point(10, 100)
    c.add_point(20, 200)
    c.add_point(30, 100)
    c.add_point(40, 0)


    print c.max_mai_age()
    print c.max_value_age()
    

    xlist = [0, 10, 11, 12, 15, 100]
    for x in xlist:
        print "test value() at x=%s:"%x, c.value(x)

    c.update_ages()
    print c._max_value_age

    #ylist = [0, 100, 200, 300, 400, 500, 333]
    ylist = [0, 10, 100, 200]
    for y in ylist:
        print "test age(direction='l') at y=%s:"%y, c.age(y, direction='l')
        print "test age(direction='r') at y=%s:"%y, c.age(y, direction='r')


    
    print
    print "curve with point data:"
    for x in c.age_list(update=True):
        print x, c.value(x)
    print "\n".join(c.dump_xml())

    c.extrapolate(0, 10, sample=5)

    print
    print "curve with point data (extrapolated):"
    for x in c.age_list(update=True):
        print x, c.value(x), c.age(c.value(x))
    print "\n".join(c.dump_xml())

    print
    print "setting curve to reference curve..."
    c.set_ref("curve.idref")
    #print c._point_dict
    print "dumping curve XML..."
    print "\n".join(c.dump_xml())

    cc = Curve(c.id(), True)

    print
    print "dumping reference curve XML..."
    print "\n".join(cc.dump_xml())
    
    #print "test age()", c.age2(300)

    c1 = Curve()
    c1.add_point(0, 1)
    c1.add_point(5, 2)
    c1.add_point(10, 3)

    c2 = Curve()
    c2.add_point(0, 4)
    c2.add_point(5, 5)
    c2.add_point(10, 6)

    print 'test add'
    c3 = c1 + c2
    c3.dump_csv()

    print 'test mul'
    c3 = c1 * c2
    c3.dump_csv()

    print 'test sub'
    c3 = c2 - c1
    c3.dump_csv()

    print 'test div'
    c3 = c1 / c2
    c3.dump_csv()

    c4 = Curve()
    c4.add_point(0, 1)
    c4.add_point(1, 1)
    print 'c4.is_flat() %s' % c4.is_flat()
    c4.dump_csv()
    c4.add_point(2, 2)
    c4.add_point(3, 2.3)
    c4.add_point(3, 2.0)
    c4.add_point(4, 2.2)
    c4.add_point(5, 2.0)
    c4.add_point(6, 2.1)
    print 'c4.is_flat() %s' % c4.is_flat()
    print 'c4.is_flat_to(1) %s' % c4.is_flat_to(1)    
    print 'c4.is_flat_to(2) %s' % c4.is_flat_to(2)    
    print 'c4.is_flat_from(1) %s' % c4.is_flat_from(1)    
    print 'c4.is_flat_from(2) %s' % c4.is_flat_from(2)    
    c4.dump_csv()
    tol = 0.3
    for age in c4.age_list():
        print c4.is_flat_to(age, tol=tol), c4.is_flat_from(age, tol=tol)
    #print c4._age_list
    
