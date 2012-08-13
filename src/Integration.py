from pipeutils import Pipeutils

class Integration:

    def __init__(self, row):
        self.pu = Pipeutils()
        self.data = row
        
    def __getitem__(self, key):
        if key == 'DATA':
            return self.pu.masked_array(self.data[key][0])
        else:
            return self.data[key][0]
    
    def __setitem__(self, key, value):
        self.data[key] = value
