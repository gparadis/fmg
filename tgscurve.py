class TgsCurve:
    #_code_tgs = ""
    #_age_explo = 0
    #_scaling_factor = 1.0
    
    
    def __init__(self, id, age_explo=0, scaling_factor=1.0):
        self._id = id
        self._age_explo = age_explo
        self._scaling_factor = scaling_factor
        self._point_dict = {}

    def force_unimodal(self):
        keys = self._point_dict.keys()
        keys.sort()
        #print "TgsCurve.force_unimodal()", self.id(), keys
        
        found_decline = False
        deleting = False
        x1 = -9999
        for x2 in keys:
            if deleting:
                del self._point_dict[x2]
                if x1 in self._point_dict:
                    del self._point_dict[x1]
            y1 = self.value(x1)
            y2 = self.value(x2)
            if not found_decline and y2 < y1:
                found_decline = True
            elif found_decline and y2 > y1:
                deleting = True
                #print "TgsCurve.force_unimodal()", self.id(), x2, "\n", keys, self._point_dict.keys() # debug
                #del self._point_dict[x2]
            x1 = x2
            #print self.id(), x2, y2, found_decline
            

    def add_point(self, age, vol):
        self._point_dict[age] = vol

    def set_point_dict(self, point_dict):
        self._point_dict = point_dict

    def point_dict(self):
        return self._point_dict

    def age_list(self):
        keys = self._point_dict.keys()
        keys.sort()
        return keys

    def set_scaling_factor(self, scaling_factor):
        self._scaling_factor = scaling_factor

    def scaling_factor(self):
        return self._scaling_factor

    def code_tgs(self):
        return self._id

    def set_id(self, id):
        self._id = id

    def id(self):
        return self._id

    def value(self, age):
        """
        Evaluate curve at age.
        """
        if not self._point_dict: return 0.0

        result = 0.0
        x_list = self._point_dict.keys()
        x_list.sort()
        x_min = x_list[0]
        i_max = len(x_list)-1
        x_max = x_list[len(x_list)-1]
        if age in self._point_dict:
            result = self._point_dict[age]
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
                    y1 = self._point_dict[x1]
                    x2 = x
                    y2 = self._point_dict[x2]
                    break
                x_last = x
            f = ((float(age) - float(x1)) / (float(x2) - float(x1)))
            result = float(y1) + ((float(y2) - float(y1)) * f) 
        elif age < x_min:
            # extrapolate
            result = float(self._point_dict[x_min])
        elif age > x_max: 
            # extrapolate
            result = float(self._point_dict[x_max])
        return max(0.0, result)
