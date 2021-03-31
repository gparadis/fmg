class AttributeDescriptor:
    """
    Encapsulates attribute metadata.
    """
    
    _id_default = ""
    _attribute_code_default = ""
    _is_total_default = False
    _is_residual_default = False
    _is_percent_default = False
    _is_value_default = False
    _is_volume_default = False
    _is_basalarea_default = False
    _is_dbh_default = False
    _is_stemvol_default = False
    _is_stemsperha_default = False
    _force_reference_default = False
    _species_code_default = ""
    _product_code_default = ""
    _extrapolate_steps_left_default = 0
    _extrapolate_steps_right_default = 0
    _description_default = ""

    def __init__(self,
                 id,
                 type_code,
                 attribute_code=_attribute_code_default,
                 is_total=_is_total_default,
                 is_residual=_is_residual_default,
                 is_percent=_is_percent_default,
                 is_value=_is_value_default,
                 is_volume=_is_volume_default,
                 is_basalarea=_is_basalarea_default,  
                 is_dbh=_is_dbh_default,
                 is_stemvol=_is_stemvol_default,
                 is_stemsperha=_is_stemsperha_default,
                 force_reference = _force_reference_default,
                 species_code=_species_code_default,
                 product_code=_product_code_default,
                 extrapolate_steps_left=_extrapolate_steps_left_default,
                 extrapolate_steps_right=_extrapolate_steps_right_default,
                 description=_description_default):
        self._id = id
        self._type_code = type_code
        self._attribute_code = attribute_code
        self._is_total = is_total
        self._is_residual = is_residual
        self._is_percent = is_percent
        self._is_value = is_value
        self._is_volume = is_volume
        self._is_basalarea = is_basalarea
        self._is_dbh = is_dbh
        self._is_stemvol = is_stemvol
        self._is_stemsperha = is_stemsperha
        self._force_reference = force_reference
        self._species_code = species_code
        self._product_code = product_code
        self._extrapolate_steps_left = extrapolate_steps_left
        self._extrapolate_steps_right = extrapolate_steps_right
        self._description = description

    def set_force_reference(self, val):
        self._force_reference = val

    def force_reference(self):
        return self._force_reference
        
    def label(self):
        if self._type_code == "feature":
            label = "feature."
        elif self._type_code == "product":
            label = "product."
        else:
            label = "%f."
        if self.is_total(): label += "total."
        if self.is_basalarea(): label += "ba."
        if self.is_residual(): label += "resid."
        if self.is_value(): label += "value."
        if self.is_volume(): label += "volume."
        if self.is_dbh(): label += "dbh."
        if self.is_stemvol(): label += "stemvol."
        if self.is_stemsperha(): label += "stemsperha."
        if self._type_code == "feature":
            label += "%m."
        if self.species_code(): label += "%s." % self.species_code()
        if self.product_code(): label += "%s." % self.product_code()
        if self.attribute_code() : label += "%s." % self.attribute_code()
        if self.is_percent(): label += "percent."
        if label.endswith("."): label = label[:-1]
        return label
        
    def id(self):
        return self._id

    def attribute_code(self):
        return self._attribute_code

    def is_residual(self):
        return self._is_residual

    def is_total(self):
        return self._is_total

    def is_percent(self):
        return self._is_percent

    def is_value(self):
        return self._is_value

    def is_volume(self):
        return self._is_volume

    def is_basalarea(self):
        return self._is_basalarea

    def is_dbh(self):
        return self._is_dbh

    def is_stemvol(self):
        return self._is_stemvol

    def is_stemsperha(self):
        return self._is_stemsperha

    def species_code(self):
        return self._species_code

    def product_code(self):
        return self._product_code

    def extrapolate_steps_left(self):
        return self._extrapolate_steps_left

    def extrapolate_steps_right(self):
        return self._extrapolate_steps_right

    def description(self):
        return self._product_code
