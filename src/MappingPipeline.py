import pyfits
from Calibration import Calibration
from SdFitsIO import SdFitsIO
from pipeutils import Pipeutils
import numpy as np
from pylab import *

class MappingPipeline:
    
    def __init__(self, filename):

        self.cal = Calibration()
        self.sdf = SdFitsIO()
        self.pu = Pipeutils()
        
        self.FITSFILE = filename+'fits'
        self.INDEXFILE = filename+'index'
    
        self.fd = pyfits.open( self.FITSFILE, memmap=1, mode='readonly' )
        self.rowList = self.sdf.parseSdfitsIndex( self.INDEXFILE )
        
    def getReference(self, scan, feed, window, pol):
        
        referenceRows = self.rowList.get(scan, feed, window, pol)
        ext = referenceRows['EXTENSION']
        rows = referenceRows['ROW']
    
        crefs = []
        trefs = []
        calON = None
        calOFF = None
        exposures = [] # used for weighting the average of reference integrations
        timestamps = [] # will get an average to use for interpolation bt/wn references
        
        for idx in rows:
            row = self.fd[ext].data[idx]
            if row.field('CAL') == 'T':
                calON = row
            else:
                calOFF = row
            
            if calOFF and calON:
                cref,tref,exposure,timestamp = self.sdf.getReferenceIntegration(calON, calOFF)
                
                # used these, so clear for the next iteration
                calOFF = None
                calON = None
                
                # collect raw spectra and tsys values for each integration
                #   these will be averaged to use for calibration
                crefs.append(cref)
                trefs.append(tref)
                exposures.append(exposure)
                timestamps.append(timestamp)
        
        avgCref,avgTref,avgTimestamp = self.cal.getReferenceAverage(crefs, trefs, exposures, timestamps)
        
        print 'Average system Temperature for reference',avgTref
        plot(avgCref,',')
        savefig('avgCref.png')
        clf()
        
        return avgCref,avgTref,avgTimestamp
        
    def CalibrateSdfitsScan(self, scan, feed, window, pol, \
                          avgCref1, crefTime1, avgTref1, \
                          avgCref2, crefTime2, avgTref2, units):
        
        signalRows = self.rowList.get(scan, feed, window, pol)
    
        ext = signalRows['EXTENSION']
        rows = signalRows['ROW']
        
        tas = []
        tastars = []
        ref_tsyss = []
        calON = None
        calOFF = None
        for idx in rows:
            row = self.fd[ext].data[idx]
            
            if row.field('CAL') == 'T':
                calON = row
            else:
                calOFF = row
            
            if calOFF and calON:
                
                csig = self.cal.Csig(calON.field('DATA'), calOFF.field('DATA'))
                intTime = self.pu.dateToMjd( calOFF.field('DATE-OBS') )
                elevation = calOFF.field('ELEVATIO')

                # used these, so clear for the next iteration
                calOFF = None
                calON = None

                if avgCref2!=None and crefTime2!=None:
                    crefInterp = \
                        self.cal.interpolate_by_time(avgCref1, avgCref2,
                                                     crefTime1, crefTime2, intTime)
                    
                    avgTref = \
                        self.cal.interpolate_by_time(avgTref1, avgTref2,
                                                     crefTime1, crefTime2, intTime)
    
                    ta = self.cal.Ta(avgTref, csig, crefInterp )
                else:
                    ta = self.cal.Ta(avgTref1, csig, avgCref1 )
                    
                tas.append(ta)
                ref_tsyss.append(avgTref1)

                if units=='ta*' or units=='tmb' or units=='tb*' or units=='jy':
                    tastar = self.cal.TaStar(ta, beam_scaling=1, opacity=0.032, gain=None, elevation=elevation)
                    tastars.append(tastar)

        if units=='ta':
            tas = np.array(tas)
            calibrated_integrations = tas
            
        if units=='ta*':
            tastars = np.array(tastars)
            calibrated_integrations = tastars
                    
        ref_tsyss = np.array(ref_tsyss)
        plot(calibrated_integrations.mean(0),label=str(scan)+' tsys('+str(ref_tsyss.mean())[:5]+')')  # look into adding weights
        ylabel(units)
        xlabel('channel')
        legend(title='scan',loc='upper right')
        savefig('calibratedScans.png')

    def __del__(self):
            
        self.fd.close()
        print 'bye'
