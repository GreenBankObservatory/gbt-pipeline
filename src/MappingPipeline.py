import pyfits
from Calibration import Calibration
from SdFitsIO import SdFitsReader
from pipeutils import Pipeutils
import numpy as np
from pylab import *
from Weather import Weather

CREATE_PLOTS = True
AVERAGING_SPECTRA_FOR_SUMMARY = True

class MappingPipeline:
    
    def __init__(self, filename):

        self.cal = Calibration()
        self.pu = Pipeutils()
        self.weather = Weather()
        
        self.sdfreader = SdFitsReader()


        self.fileroot = filename
        
        self.FITSFILE = filename+'fits'
        self.INDEXFILE = filename+'index'
    
        self.infile = pyfits.open( self.FITSFILE, memmap=1 )
        self.outfile = None

        self.rowList = self.sdfreader.parseSdfitsIndex( self.INDEXFILE )
        
        # constants
        self.OPACITY  = None
        self.ETAB_REF = 0.91   # KFPA
        self.ETAA_REF = 0.71   # KFPA
               
    def determineSetup(self, sdfits_row_structure, ext):
        
        # ------------------ look ahead at first few rows to determine setup
        #  is the noise diode firing?
        #  are there signal and reference components?

        lookahead_cal_states = set([])
        lookahead_sig_states = set([])
        
        # fill the buffers
        for idx,rowNum in enumerate(sdfits_row_structure[:4]):
            row = self.infile[ext].data[rowNum]
            lookahead_cal_states.add(row.field('CAL'))
            lookahead_sig_states.add(row.field('SIG'))
        
        cal_switching = False
        sigref = False

        if len(lookahead_cal_states) > 1:
            cal_switching = True
        
        if len(lookahead_sig_states) > 1:
            sigref = True
            
        return cal_switching, sigref
    
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
            
            row = self.infile[ext].data[idx]
            if row.field('CAL') == 'T':
                calON = row
            else:
                calOFF = row
            
            if calOFF and calON:
                cref,tref,exposure,timestamp,tambient,elevation = self.sdfreader.getReferenceIntegration(calON, calOFF)
                
#-----------------
                # comment if using idl Tsys
                #ltref = len(tref)
                #lo = int(.1*ltref)
                #hi = int(.9*ltref)
                #print tref[lo:hi].mean()
                #print tref,',',
#^^^^^^^^^^^^^^^^^
                
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
        
    def CalibrateSdfitsIntegrations(self, mapscans, feed, window, pol, \
                          avgCref1, avgTref1, crefTime1, refTambient1, refElevation1, \
                          avgCref2, avgTref2, crefTime2, refTambient2, refElevation2, \
                          beam_scaling, units):
    
        outfilename = self.fileroot + 'feed' + str(feed) + '_if' + str(window) + '_pol' + str(pol) + '.fits'
        
        for scan in mapscans:
            
            signalRows = self.rowList.get(scan, feed, window, pol)
            
            if crefTime2!=None and refTambient2!=None and refElevation2!=None:
                multiple_reference_scans_for_tsky = True
            else:
                multiple_reference_scans_for_tsky = False
                
            ext = signalRows['EXTENSION']
            rows = signalRows['ROW']
            
            if AVERAGING_SPECTRA_FOR_SUMMARY:
                tas = []
                tsrcs = []
                tastars = []
                tmbs = []
                jys = []
                exposures = []
            
            if CREATE_PLOTS:
                ref_tsyss = []
    
            cal_switching, sigref = self.determineSetup(rows, ext)
            
            calON = None
            calOFF = None
            
            
            nrows = len(rows)
            WRITESIZE = 100
            writeNrows = []
            rowchunks = []
            startchunk = 0
            while nrows>0:
                if nrows > WRITESIZE:
                    nrows = nrows - WRITESIZE
                    writeNrows.append( WRITESIZE )
                    rowchunks.append(rows[startchunk:startchunk+WRITESIZE])
                    startchunk = startchunk+WRITESIZE
                else:
                    writeNrows.append( nrows )
                    rowchunks.append(rows[startchunk:])
                    nrows = 0
                            
            for chunk in rowchunks:
                
                rows2write = len(chunk)
                if cal_switching:
                    rows2write / 2
                if sigref:
                    rows2write / 2
                table = pyfits.new_table(self.infile[ext].columns, nrows=rows2write, fill=True)
            
                # now start at the beginning and calibrate all the integrations
                for idx,rowNum in enumerate(chunk):
        
                    row = self.infile[ext].data[rowNum]
                    
                    if row.field('CAL') == 'T':
                        calON = row
                    else:
                        calOFF = row
                    
                    csig = None
                    
                    if cal_switching and calOFF and calON:
                        # noise diode is being fired during signal integrations
        
                        calONdata = self.pu.masked_array(calON.field('DATA'))
                        calOFFdata = self.pu.masked_array(calOFF.field('DATA'))
                        
                        csig = self.cal.Csig(calONdata, calOFFdata)
        
                        if AVERAGING_SPECTRA_FOR_SUMMARY:
                            exposure = calON.field('EXPOSURE')+calOFF.field('EXPOSURE')
                            exposures.append(exposure)
        
                    # if there is more than one row, this isn't the last one, this and the next are CAL=='F',
                    #    then the diode is not firing
                    elif not cal_switching:
                        csig = self.pu.masked_array(calOFF.field('DATA'))
                    
                    # we are cal switching but we only have one cal state,
                    #   then read the next row
                    else:
                        continue
                    
                    if csig != None:
                        
                        index = idx
                        if cal_switching:
                            index = index / 2
                        if sigref:
                            index = index / 2
                        
                        table.data[index] = row # output
                        
                        intTime = self.pu.dateToMjd( calOFF.field('DATE-OBS') ) # integration timestamp
                        elevation = calOFF.field('ELEVATIO') # integration elevation
                        obsfreqHz = calOFF.field('OBSFREQ')  # integration observed frequency
        
                        if avgCref2!=None and crefTime2!=None:
                            crefInterp = \
                                self.cal.interpolate_by_time(avgCref1, avgCref2,
                                                             crefTime1, crefTime2, intTime)
                            
                            avgTrefInterp = \
                                self.cal.interpolate_by_time(avgTref1, avgTref2,
                                                             crefTime1, crefTime2, intTime)
            
                            ta = self.cal.Ta(avgTrefInterp, csig, crefInterp )
                            tsys = avgTrefInterp
                        else:
                            ta = self.cal.Ta(avgTref1, csig, avgCref1 )
                            tsys = avgTref1
                                            
                        if AVERAGING_SPECTRA_FOR_SUMMARY:
                            tas.append(ta)
                
                        if CREATE_PLOTS:
                            ref_tsyss.append(avgTref1)
        
                        if units=='tsrc' or units=='ta*' or units=='tmb' or units=='jy':
                            # ASSUMES a given opacity
                            #   the opacity needs to come from the command line or Ron's
                            #   model database.
                            if not self.OPACITY:
                                intOpacity = self.weather.retrieve_zenith_opacity(intTime, obsfreqHz)
                                if not intOpacity:
                                    print 'ERROR: Not able to retrieve integration zenith opacity for',
                                    print 'calibration to:',units
                                    print '  Please supply a zenith opacity or calibrate to Ta.'
                                    sys.exit(9)
                            else:
                                intOpacity = self.OPACITY
                                
                            opacity_el = self.cal.elevation_adjusted_opacity(intOpacity, elevation)
        
                                
                            # tsky for reference 1
                            if not self.OPACITY:
                                ref1_zenith_opacity = self.weather.retrieve_zenith_opacity(crefTime1, obsfreqHz)
                                if not ref1_zenith_opacity:
                                    print 'ERROR: Not able to retrieve reference 1 zenith opacity for',
                                    print 'calibration to:',units
                                    print '  Please supply a zenith opacity or calibrate to Ta.'
                                    sys.exit(9)
                            else:
                                ref1_zenith_opacity = self.OPACITY
                                
                            opacity1 = self.cal.elevation_adjusted_opacity(ref1_zenith_opacity, refElevation1)
                            
                            crpix1 = calOFF.field('CRPIX1')
                            cdelt1 = calOFF.field('CDELT1')
                            crval1 = calOFF.field('CRVAL1')
                            tsky1 = []
                            for chan in range(len(ta)):
                                freqHz = (chan-crpix1)*cdelt1 + crval1
                                tsky_chan = self.cal.tsky(refTambient1, freqHz, opacity1)
                                tsky1.append(tsky_chan)
                            tsky1 = np.array(tsky1)
                                
                            if multiple_reference_scans_for_tsky:
        
                                # tsky for reference 2
                                if not self.OPACITY:
                                    ref2_zenith_opacity = self.weather.retrieve_zenith_opacity(crefTime2, obsfreqHz)
                                    if not ref2_zenith_opacity:
                                        print 'ERROR: Not able to retrieve reference 2 zenith opacity for',
                                        print 'calibration to:',units
                                        print '  Please supply a zenith opacity or calibrate to Ta.'
                                        sys.exit(9)
                                else:
                                    ref2_zenith_opacity = self.OPACITY
                
                                opacity2 = self.cal.elevation_adjusted_opacity(ref2_zenith_opacity, refElevation2)
        
                                tsky2 = []
                                for chan in range(len(ta)):
                                    freqHz = (chan-crpix1)*cdelt1 + crval1
                                    tsky_chan = self.cal.tsky(refTambient2, freqHz, opacity2)
                                    tsky2.append(tsky_chan)
                                tsky2 = np.array(tsky2)
            
                                # get Tsky for each ref, then interpolate bt/wn the 2
                                tskyInterp = \
                                    self.cal.interpolate_by_time(tsky1, tsky2,
                                                                 crefTime1, crefTime2, intTime)
                                
                            # get tsky for the current integration
                            tambient_current = calOFF.field('TAMBIENT')
                            tsky_current = []
                            for chan in range(len(ta)):
                                freqHz = (chan-crpix1)*cdelt1 + crval1
                                tsky_chan = self.cal.tsky(tambient_current, freqHz, opacity_el)
                                tsky_current.append(tsky_chan)
                            tsky_current = np.array(tsky_current)
                                
                    
                            if multiple_reference_scans_for_tsky:
                                tsky_corr = self.cal.tsky_corr(tsky_current, tskyInterp)
                            
                            else:
                                tsky_corr = self.cal.tsky_corr(tsky_current, tsky1)
                                
                            tsrc = ta-tsky_corr
        
                            if AVERAGING_SPECTRA_FOR_SUMMARY:
                                tsrcs.append(tsrc)
                            
                        if units=='ta*' or units=='tmb' or units=='jy':
                            # ASSUMES GAIN COEFFICIENTS and a given opacity
                            #   the opacity needs to come from the command line or Ron's
                            #   model database.  Gain coefficients can optionally come
                            #   from the command line.
                            
                            gain = self.cal.gain(self.cal.GAIN_COEFFICIENTS, elevation)
                            
                            tastar = self.cal.TaStar(tsrc, beam_scaling, opacity=opacity_el, \
                                                     gain=gain, elevation=elevation)
                            
                            if AVERAGING_SPECTRA_FOR_SUMMARY:
                                tastars.append(tastar)
                            
                        if units=='tmb':
                            # ASSUMES a reference value for etaB.  This should be made available
                            #   at the command line.  The assumed value is for KFPA only.
                            main_beam_efficiency = self.cal.main_beam_efficiency(self.ETAB_REF, obsfreqHz)
                            tmb = tastar / main_beam_efficiency
                            
                            if AVERAGING_SPECTRA_FOR_SUMMARY:
                                tmbs.append(tmb)
                                
                        if units=='jy':
                            # ASSUMES a reference value for etaA.  This should be made available
                            #   at the command line.  The assumed value is for KFPA only.
                            aperture_efficiency = self.cal.aperture_efficiency(self.ETAA_REF, obsfreqHz)
                            jy = tastar / (2.85 * aperture_efficiency)
        
                            if AVERAGING_SPECTRA_FOR_SUMMARY:
                                jys.append(jy)
                            
                        # used these, so clear for the next iteration
                        calOFF = None
                        calON = None
                        
                        # --------------------------------  write data out to FITS file
    
        
                        if 'ta' == units:
                            table.data[index].setfield('DATA',ta)
                        elif 'tsrc' == units:
                            table.data[index].setfield('DATA',tsrc)
                        elif 'ta*' == units:
                            table.data[index].setfield('DATA',tastar)
                        elif 'tmb' == units:
                            table.data[index].setfield('DATA',tmb)
                        elif 'jy' == units:
                            table.data[index].setfield('DATA',jy)
                        else:
                            print 'ERROR: units not recognized.  Can not write data.'
                            sys.exit(9)
                            
                        table.data[index].setfield('TSYS',tsys)
                
                pyfits.append(outfilename, table.data, table.header)
                        
                # done looping over rows            
           
            # make some scan summary information for plotting
            
            if AVERAGING_SPECTRA_FOR_SUMMARY:
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
            
        self.infile.close()
        print 'bye'
