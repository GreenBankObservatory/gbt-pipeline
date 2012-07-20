import pyfits
from Calibration import Calibration
from SdFitsIO import SdFitsIO
from pipeutils import Pipeutils
import numpy as np
from pylab import *

CREATE_PLOTS = True
DO_ALTHOUGH_NOT_STRICTLY_NECESSARY = True

# ASSUMES no NaN values in spectra

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
        tambients = [] # used for tsky computation for ta* and beyond
        elevations = [] # used for tsky computation for ta* and beyond
        
        for idx in rows:
            row = self.fd[ext].data[idx]
            if row.field('CAL') == 'T':
                calON = row
            else:
                calOFF = row
            
            if calOFF and calON:
                cref,tref,exposure,timestamp,tambient,elevation = self.sdf.getReferenceIntegration(calON, calOFF)
                
                # used these, so clear for the next iteration
                calOFF = None
                calON = None
                
                # collect raw spectra and tsys values for each integration
                #   these will be averaged to use for calibration
                crefs.append(cref)
                trefs.append(tref)
                exposures.append(exposure)
                timestamps.append(timestamp)
                tambients.append(tambient)
                elevations.append(elevation)
        
        avgCref,avgTref,avgTimestamp,avgTambient,avgElevation = \
            self.cal.getReferenceAverage(crefs, trefs, exposures, timestamps, tambients, elevations)
        
        print 'Average system Temperature for reference',avgTref
        
        if CREATE_PLOTS:
            plot(avgCref,',',label='tsys='+str(avgTref))
            legend()
            savefig('avgCref.png')
            clf()
        
        return avgCref,avgTref,avgTimestamp,avgTambient,avgElevation
        
    def CalibrateSdfitsIntegrations(self, scan, feed, window, pol, \
                          avgCref1, avgTref1, crefTime1, refTambient1, refElevation1, \
                          avgCref2, avgTref2, crefTime2, refTambient2, refElevation2, \
                          units):
    
        signalRows = self.rowList.get(scan, feed, window, pol)
        
        ext = signalRows['EXTENSION']
        rows = signalRows['ROW']
        
        if DO_ALTHOUGH_NOT_STRICTLY_NECESSARY:
            tas = []
            tsrcs = []
            tastars = []
            tmbs = []
            jys = []
            exposures = []
        
        if CREATE_PLOTS:
            ref_tsyss = []

        calON = None
        calOFF = None
        for idx in rows:
            row = self.fd[ext].data[idx]
            
            if row.field('CAL') == 'T':
                calON = row
            else:
                calOFF = row
            
            # ASSUMES noise diode is being fired during signal integrations
            if calOFF and calON:
                
                csig = self.cal.Csig(calON.field('DATA'), calOFF.field('DATA'))
                intTime = self.pu.dateToMjd( calOFF.field('DATE-OBS') )
                elevation = calOFF.field('ELEVATIO')
                obsfreq = calOFF.field('OBSFREQ')
                
                if DO_ALTHOUGH_NOT_STRICTLY_NECESSARY:
                    exposure = calON.field('EXPOSURE')+calOFF.field('EXPOSURE')
                    exposures.append(exposure)

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
                
                if DO_ALTHOUGH_NOT_STRICTLY_NECESSARY:
                    tas.append(ta)
        
                if CREATE_PLOTS:
                    ref_tsyss.append(avgTref1)

                if units=='tsrc' or units=='ta*' or units=='tmb' or units=='tb*' or units=='jy':
                    # ASSUMES a given opacity
                    #   the opacity needs to come from the command line or Ron's
                    #   model database.
                    opacity=0.032
                    opacity_el = self.cal.elevation_adjusted_opacity(opacity, elevation)

                    if crefTime2!=None and refTambient2!=None and refElevation2!=None:

                        # get Tsky for each ref, then interpolate bt/wn the 2
                        
                        # tsky for reference 1
                        opacity1 = self.cal.elevation_adjusted_opacity(opacity, refElevation1)
                        
                        crpix1 = calOFF.field('CRPIX1')
                        cdelt1 = calOFF.field('CDELT1')
                        crval1 = calOFF.field('CRVAL1')
                        tsky1 = []
                        for chan in range(len(ta)):
                            freq = (chan-crpix1)*cdelt1 + crval1
                            tsky_chan = self.cal.tsky(refTambient1, freq, opacity1)
                            tsky1.append(tsky_chan)
                        tsky1 = np.array(tsky1)
                        
                        # tsky for reference 2
                        opacity1 = self.cal.elevation_adjusted_opacity(opacity, refElevation2)
                        tsky2 = []
                        for chan in range(len(ta)):
                            freq = (chan-crpix1)*cdelt1 + crval1
                            tsky_chan = self.cal.tsky(refTambient1, freq, opacity1)
                            tsky2.append(tsky_chan)
                        tsky2 = np.array(tsky2)
    
                        tskyInterp = \
                            self.cal.interpolate_by_time(tsky1, tsky2,
                                                         crefTime1, crefTime2, intTime)
                        
                        # get tsky for the current integration
                        tambient_current = calOFF.field('TAMBIENT')
                        tsky_current = []
                        for chan in range(len(ta)):
                            freq = (chan-crpix1)*cdelt1 + crval1
                            tsky_chan = self.cal.tsky(tambient_current, freq, opacity_el)
                            tsky_current.append(tsky_chan)
                        tsky_current = np.array(tsky_current)
                        tsky_corr = self.cal.tsky_corr(tsky_current, tskyInterp)
                        
                        tsrc = ta-tsky_corr

                        if DO_ALTHOUGH_NOT_STRICTLY_NECESSARY:
                            tsrcs.append(tsrc)
                        
                        #if CREATE_PLOTS:
                        #    plot(tsky_current,label='current')
                        #    plot(tsky1,label='tsky1')
                        #    plot(tsky2,label='tsky2')
                        #    plot(tskyInterp,label='tskyInterp')
                        #    plot(tsky_corr,label='tsky_corr')
                        #    legend()
                        #    savefig('tsky.png')
                        #    clf()
                        #    print tsky_corr.mean()
                        #    import sys; sys.exit()
                    
                if units=='ta*':
                    # ASSUMES no beam scaling, no gain and a given opacity
                    #   the opacity needs to come from the command line or Ron's
                    #   model database.  Gain coefficients can optionally come
                    #   from the command line.  If not supplied, defaults are used.
                    tastar = self.cal.TaStar(tsrc, beam_scaling=1, opacity=opacity_el, \
                                             gain=None, elevation=elevation)
                    
                    if DO_ALTHOUGH_NOT_STRICTLY_NECESSARY:
                        tastars.append(tastar)
                    
                if units=='tmb':
                    # ASSUMES a reference value for etaB.  This should be made available
                    #   at the command line.  The assumed value is for KFPA only.
                    etaB_ref = 0.91
                    main_beam_efficiency = self.cal.main_beam_efficiency(etaB_ref, obsfreq)
                    tmb = tastar / main_beam_efficiency
                    
                    if DO_ALTHOUGH_NOT_STRICTLY_NECESSARY:
                        tmbs.append(tmb)
                        
                if units=='jy':
                    # ASSUMES a reference value for etaA.  This should be made available
                    #   at the command line.  The assumed value is for KFPA only.
                    etaA_ref = 0.71
                    aperture_efficiency = self.cal.aperture_efficiency(etaA_ref, obsfreq)
                    jy = tastar / (2.85 * aperture_efficiency)

                    if DO_ALTHOUGH_NOT_STRICTLY_NECESSARY:
                        jys.append(jy)
                    
                # used these, so clear for the next iteration
                calOFF = None
                calON = None

        if DO_ALTHOUGH_NOT_STRICTLY_NECESSARY:
            if units=='ta':
                tas = np.array(tas)
                calibrated_integrations = tas

            elif units=='tsrc':
                tsrcs = np.array(tsrcs)
                calibrated_integrations = tsrcs
                
            elif units=='ta*':
                tastars = np.array(tastars)
                calibrated_integrations = tastars

            elif units=='tmb':
                tmbs = np.array(tmbs)
                calibrated_integrations = tmbs

            elif units=='jy':
                jys = np.array(jys)
                calibrated_integrations = jys  
        
        if CREATE_PLOTS:
            ref_tsyss = np.array(ref_tsyss)
            exposures = np.array(exposures)
            weights = exposures / ref_tsyss**2
            averaged_integrations = np.average(calibrated_integrations,axis=0,weights=weights)
            plot(averaged_integrations,label=str(scan)+' tsys('+str(ref_tsyss.mean())[:5]+')')
            ylabel(units)
            xlabel('channel')
            legend(title='scan',loc='upper right')
            savefig('calibratedScans.png')

    def __del__(self):
            
        self.fd.close()
        print 'bye'
