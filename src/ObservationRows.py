# Copyright (C) 2007 Associated Universities, Inc. Washington DC, USA.
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# 
# Correspondence concerning GBT software should be addressed as follows:
#       GBT Operations
#       National Radio Astronomy Observatory
#       P. O. Box 2
#       Green Bank, WV 24944-0002 USA

# $Id$

from collections import OrderedDict
from collections import namedtuple

class ObservationRows:
    def __init__(self):
        self.rows = OrderedDict()
        self.Key = namedtuple('key', 'scan, feed, window, polarization')
        
    def addRow(self, scan, feed, window, polarization,
                       fitsExtension, rowOfFitsFile, typeOfScan):
        
        key = self.Key(scan, feed, window, polarization)
        #key = (scan, feed, window, polarization)
        if key in self.rows:
            self.rows[key]['ROW'].append(rowOfFitsFile)
        else:
            self.rows[key] = {'EXTENSION': fitsExtension,
                              'ROW': [rowOfFitsFile],
                              'TYPE': typeOfScan }
            
    def get(self, scan, feed, window, polarization):
        try:
            key = (scan, feed, window, polarization)
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
    
