from nose.tools import *
import numpy as np
import fitsio

from Integration import Integration

class test_Integration:

    def setup(self):
        ff = fitsio.FITS('/home/gbtpipeline/reference-data/TKFPA_29.raw.acs.fits')
        columns = tuple(ff[1].colnames)
        self.row = Integration( ff[1][columns][0] )
        
    def test_get(self):
        eq_( self.row['CAL'], 'T' )
        eq_( self.row['SIG'], 'T' )
        eq_( self.row['OBJECT'], 'W51-OFF' )
        eq_( np.all(self.row['DATA']), True )
        eq_( np.any(np.isnan(self.row['DATA'])), False )

    def test_set(self):
        self.row['SIG'] = 'A'
        eq_( self.row['SIG'], 'A' )
