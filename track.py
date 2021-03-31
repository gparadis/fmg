class Track:
    """ForestModel track element data"""
    def __init__(self):
        self.treatments = {}
    def addTreatment(self, treatment):
        self.treatments[treatment.label] = treatment

      
if __name__ == "__main__":
    pass # add test code here
            
