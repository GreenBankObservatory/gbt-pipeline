import pyfits
from Calibration import Calibration
from SdFitsIO import SdFitsIO
import numpy as np
from pylab import *

if __name__ == '__main__':
    
    cal = Calibration()
    
    # -------------------------------------------------------- gather data
    FILENAME = '/media/980d0181-4160-4bbf-8c3d-3d370f24fefd/data/TKFPA_29/TKFPA_29.raw.acs.'
    FITSFILE = FILENAME+'fits'
    INDEXFILE = FILENAME+'index'

    fd = pyfits.open( FITSFILE, memmap=1, mode='readonly' )
    
    sdf = SdFitsIO()
    rowList = sdf.parseSdfitsIndex( INDEXFILE )
    
    # -------------- identify reference
    scan=13
    feed=0
    window=0
    pol=0
    
    referenceRows = rowList.get(scan, feed, window, pol)
    ext = referenceRows['EXTENSION']
    rows = referenceRows['ROW']

    calON = None
    calOFF = None

    crefs = []
    trefs = []
    exposures = [] # used for weighting the average of reference integrations
    for idx in rows:
        row = fd[ext].data[idx]
        if row.field('CAL') == 'T':
            calON = row
        else:
            calOFF = row
        
        if calOFF and calON:
            cref,tref,exposure = sdf.getReferenceIntegration(calON, calOFF)
            
            # used these, so clear for the next iteration
            calOFF = None
            calON = None
            
            # collect raw spectra and tsys values for each integration
            #   these will be averaged to use for calibration
            crefs.append(cref)
            trefs.append(tref)
            exposures.append(exposure)
    
    avgCref,avgTref = cal.getReferenceAverage(crefs, trefs, exposures)
    print 'Average system Temperature for reference',avgTref
    plot(avgCref,',')
    savefig('avgCref.png')
    clf()
    
    # ------------------------------------ map integrations
    
    # -------------- identify signal
    scan=14
    feed=0
    window=0
    pol=0
    signalRows = rowList.get(scan, feed, window, pol)

    ext = signalRows['EXTENSION']
    rows = signalRows['ROW']
    
    tas = []
    for idx in rows:
        row = fd[ext].data[idx]
        
        if row.field('CAL') == 'T':
            calON = row
        else:
            calOFF = row
        
        if calOFF and calON:
            
            csig = cal.Csig(calON.field('DATA'), calOFF.field('DATA'))
            # used these, so clear for the next iteration
            calOFF = None
            calON = None
            
            ta = cal.Ta(avgTref,csig,avgCref)
            tas.append(ta)
            
    tas = np.array(tas)
    
    plot(tas.mean(0))  # look into adding weights
    savefig('avgTa.png')
    
    fd.close()
