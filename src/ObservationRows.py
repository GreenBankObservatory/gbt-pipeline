from collections import OrderedDict
from collections import namedtuple
import sys

class ObservationRows:
    def __init__(self):
        self.rows = OrderedDict()
        self.Key = namedtuple('key', 'scan, feed, window, polarization')
        
    def addRow(self, scan, feed, window, polarization,
                       fitsExtension, rowOfFitsFile, typeOfScan):
        
        key = self.Key(scan,feed,window,polarization)
        #key = (scan,feed,window,polarization)
        if key in self.rows:
            self.rows[key]['ROW'].append(rowOfFitsFile)
        else:
            self.rows[key] = {'EXTENSION': fitsExtension,
                              'ROW': [rowOfFitsFile],
                              'TYPE': typeOfScan }
    def get(self,scan,feed,window,polarization):
        try:
            key = (scan,feed,window,polarization)
            return self.rows[key]
        except(KeyError):
            raise
        
    def scans(self):
        return list(set([xx.scan for xx in self.rows.keys()]))

    def feeds(self):
        return list(set([xx.feed for xx in self.rows.keys()]))
    
    def windows(self):
        return list(set([xx.window for xx in self.rows.keys()]))

    def pols(self):
        return list(set([xx.polarization for xx in self.rows.keys()]))
    
