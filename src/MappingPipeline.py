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

import fitsio

from Integration import Integration
from Calibration import Calibration
from SdFitsIO import SdFits
from Pipeutils import Pipeutils
import numpy as np
import pylab
from Weather import Weather

import os
import sys

CREATE_PLOTS = True
AVERAGING_SPECTRA_FOR_SUMMARY = True


class MappingPipeline:
    
    def __init__(self, cl_params, rowList):

        self.cal = Calibration()
        self.pu = Pipeutils()
        self.weather = Weather()
        self.sdf = SdFits()

        self.cl = cl_params # store command line params locally

        self.infilename = cl_params.infilename


        try:
            self.infile = fitsio.FITS( cl_params.infilename )
        except ValueError,e:
            print 'Input',e
            sys.exit()
        
        self.outfile = None

        self.rowList = rowList

        if not cl_params.mapscans:
            self.cl.mapscans = rowList.scans()

        # command line options
        self.OPACITY  = cl_params.zenithtau
        self.ETAB_REF = cl_params.mainbeam_eff
        self.ETAA_REF = cl_params.aperture_eff
        self.SPILLOVER = cl_params.spillover
        self.GAINCOEFFS = cl_params.gaincoeffs
        self.CLOBBER = cl_params.clobber
        
        self.BUFFER_SIZE = 1000
        
    def determineSetup(self, sdfits_row_structure, ext):
        
        # ------------------ look ahead at first few rows to determine setup
        #  is the noise diode firing?
        #  are there signal and reference components?

        lookahead_cal_states = set([])
        lookahead_sig_states = set([])
        
        # fill the buffers
        for idx,rowNum in enumerate(sdfits_row_structure[:4]):
            columns = ('CAL','SIG')
            row = Integration(self.infile[ext][columns][rowNum])
            
            lookahead_cal_states.add(row['CAL'])
            lookahead_sig_states.add(row['SIG'])
                    
        cal_switching = False
        sigref = False

        if len(lookahead_cal_states) > 1:
            cal_switching = True
        
        if len(lookahead_sig_states) > 1:
            sigref = True

        return cal_switching, sigref
    
    def getReference(self, scan, feed, window, pol):
        
        referenceRows = self.rowList.get(scan, feed, window, pol)

        if not referenceRows:
            return None
        
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
        
        columns = tuple(self.infile[ext].colnames)
        
        for rowNum in rows:
            
            row = Integration(self.infile[ext][columns][rowNum])
        
            if row['CAL'] == 'T':
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
        
        print 'System Temperature for reference scan',scan,'with feed',feed,'window',window,'pol',pol,':',avgTref
        
        return avgCref,avgTref,avgTimestamp,avgTambient,avgElevation
        
    def create_output_sdfits(self, feed, window, pol):
        
        try:
            signalRows = self.rowList.get(self.cl.mapscans[0], feed, window, pol)
        except KeyError:
            return None
        
        rootname,extension = os.path.splitext(self.infilename)
        basename = os.path.basename(rootname)

        outfilename = basename + '_feed' + str(feed) \
            + '_if' + str(window) + '_pol' + str(pol) + '.fits'
        if False == self.CLOBBER and os.path.exists(outfilename):
            print 'WARNING:  Will not overwrite existing pipeline output.'
            print 'Consider using \'--clobber\' option to overwrite.'
            sys.exit()
        
        # create a new table
        self.outfile = fitsio.FITS(outfilename,'rw')

        ext = signalRows['EXTENSION']

        dtype = self.infile[ext][0].dtype
        
        input_header = fitsio.read_header(self.infilename, ext)
        self.outfile.create_table_hdu(dtype=dtype, header=input_header)
        
        return dtype

    def multi_tskys(self, crefTime2, refTambient2, refElevation2):
        
        if crefTime2!=None and refTambient2!=None and refElevation2!=None:
            return True
        else:
            return False
    
    def set_row_chunks(self,rows, WRITESIZE=100):

        nrows = len(rows)
        rowchunks = []
        startchunk = 0
        while nrows>0:
            if nrows > WRITESIZE:
                nrows = nrows - WRITESIZE
                rowchunks.append(rows[startchunk:startchunk+WRITESIZE])
                startchunk = startchunk+WRITESIZE
            else:
                rowchunks.append(rows[startchunk:])
                nrows = 0
        return rowchunks

    def getObsFreq(self, feed, window, pol):

        # get integration rows of input table
        signalRows = self.rowList.get(self.cl.mapscans[0], feed, window, pol)
        ext = signalRows['EXTENSION']
        rows = signalRows['ROW']
        columns = tuple(self.infile[ext].colnames)
        firstIntegration = Integration(self.infile[ext][columns][rows[0]])
        
        # integration observed frequency
        # we assume this center of band frequency is the same for all integrations
        #  in both the reference scans and the map scans
        obsfreqHz = firstIntegration['OBSFREQ']

        return obsfreqHz

    def getReferenceTsky(self, feed, window, pol, crefTime1, refTambient1, refElevation1, \
                         crefTime2, refTambient2, refElevation2):
        
        multiple_reference_scans_for_tsky = self.multi_tskys(crefTime2, refTambient2, refElevation2)
        
        obsfreqHz = self.getObsFreq(feed, window, pol)
        
        # tsky for reference 1
        if not self.OPACITY:
            ref1_zenith_opacity = self.weather.retrieve_zenith_opacity(crefTime1, obsfreqHz)
            if not ref1_zenith_opacity:
                print 'ERROR: Not able to retrieve reference 1 zenith opacity',
                print '  Please supply a zenith opacity or calibrate to Ta.'
                sys.exit(9)
        else:
            ref1_zenith_opacity = self.OPACITY
            
        opacity1 = self.cal.elevation_adjusted_opacity(ref1_zenith_opacity, refElevation1)
        
        # get tsky at center frequency
        tsky1 = self.cal.tsky(refTambient1, obsfreqHz, opacity1)
    
        tsky2 = None
        if multiple_reference_scans_for_tsky:

            # tsky for reference 2
            if not self.OPACITY:
                ref2_zenith_opacity = self.weather.retrieve_zenith_opacity(crefTime2, obsfreqHz)
                if not ref2_zenith_opacity:
                    print 'ERROR: Not able to retrieve reference 2 zenith opacity for',
                    print 'calibration to:',self.cl.units
                    print '  Please supply a zenith opacity or calibrate to Ta.'
                    sys.exit(9)
            else:
                ref2_zenith_opacity = self.OPACITY

            opacity2 = self.cal.elevation_adjusted_opacity(ref2_zenith_opacity, refElevation2)

            # get tsky at center frequency
            tsky2 = self.cal.tsky(refTambient2, obsfreqHz, opacity2)
            
        return tsky1,tsky2
    
    def nOutputRows(self, listOfRows, cal_switching, sigref):

        rows2write = len(listOfRows)
        
        if cal_switching:
            rows2write = rows2write / 2
        if sigref:
            rows2write = rows2write / 2
            
        return rows2write
        
    def calibrate_fs_sdfits_integrations(self, feed, window, pol, \
                                            beam_scaling):
        
        dtype = self.create_output_sdfits(feed, window, pol)
        if None == dtype:
            return
        else:
            print 'calibrating feed',feed,'window',window,'polarization',pol
        
        for scan in self.cl.mapscans:

            try:
                inputRows = self.rowList.get(scan, feed, window, pol)
            except:
                continue
            
            # get integration rows
            rows = inputRows['ROW']
            ext = inputRows['EXTENSION']
            
            columns = tuple(self.infile[ext].colnames)
            
            cal_switching, sigref = self.determineSetup(rows, ext)
            
            if not cal_switching and not sigref:
                print 'ERROR:  scan',scan,'does not have 2 signal states'
                print '    and 2 noise diode (cal) states'
            
            # break the input rows into chunks as buffers to write out
            #   so that we don't write out rows one at a time
            rowchunks = self.set_row_chunks(rows, self.BUFFER_SIZE)

            outputidx = 0
            
            for chunk in rowchunks:

                rows2write = self.nOutputRows(chunk, cal_switching, sigref)
                
                output_data = np.zeros(rows2write, dtype=dtype)
                
                sigrefState = [{'calON':None, 'calOFF':None, 'TP':None}, \
                               {'calON':None, 'calOFF':None, 'TP':None}]
               
                # now start at the beginning and calibrate all the integrations
                for idx,rowNum in enumerate(chunk):
                    
                    row = Integration(self.infile[ext][columns][rowNum])
                    
                    if row['SIG'] == 'T':
                        if row['CAL'] == 'T':
                            sigrefState[0]['calON'] = row
                            #print 'sig, calON', rowNum
                        else:
                            sigrefState[0]['calOFF'] = row
                            #print 'sig, calOFF', rowNum
                    else:
                        if row['CAL'] == 'T':
                            sigrefState[1]['calON'] = row
                            #print 'ref, calON', rowNum
                        else:
                            sigrefState[1]['calOFF'] = row
                            #print 'ref, calOFF', rowNum
                    
                    # we need 4 states to calibrate FS integrations
                    if sigrefState[0]['calON'] and sigrefState[0]['calOFF'] and \
                       sigrefState[1]['calON'] and sigrefState[1]['calOFF']:

                        # noise diode is being fired during signal integrations
                        sigrefState[0]['TP'] = \
                            self.cal.Cavg(sigrefState[0]['calON']['DATA'], sigrefState[0]['calOFF']['DATA'])
                        sigrefState[1]['TP'] = \
                            self.cal.Cavg(sigrefState[1]['calON']['DATA'], sigrefState[1]['calOFF']['DATA'])
                                                    
                    else:
                        continue  # read more rows until we have all 4 states

                    # integration timestamp and elevation
                    #  should be same for all states
                    intTime = self.pu.dateToMjd( sigrefState[0]['calOFF']['DATE-OBS'] )
                    elevation = sigrefState[0]['calOFF']['ELEVATIO'] 
                    
                    ta, tsys = self.cal.Ta_fs(sigrefState)
                    
                    if self.cl.units != 'ta':
                        
                        obsfreqHz = self.getObsFreq(feed, window, pol)
                        
                        # ASSUMES a given opacity
                        #   the opacity needs to come from the command line or Ron's
                        #   model database.
                        if not self.OPACITY:
                            intOpacity = self.weather.retrieve_zenith_opacity(intTime, obsfreqHz)
                            if not intOpacity:
                                print 'ERROR: Not able to retrieve integration zenith opacity for',
                                print 'calibration to:',self.cl.units
                                print '  Please supply a zenith opacity or calibrate to Ta.'
                                sys.exit(9)
                        else:
                            intOpacity = self.OPACITY
                            
                        opacity_el = self.cal.elevation_adjusted_opacity(intOpacity, elevation)
                            
                        # get tsky for the current integration
                        tambient_current = calOFF['TAMBIENT']
                                
                    if self.cl.units=='ta*' or self.cl.units=='tmb' or self.cl.units=='jy':
                        # ASSUMES GAIN COEFFICIENTS and a given opacity
                        #   the opacity needs to come from the command line or Ron's
                        #   model database.  Gain coefficients can optionally come
                        #   from the command line.
                        
                        gain = self.cal.gain(self.cal.GAIN_COEFFICIENTS, elevation)
                        
                        tastar = self.cal.TaStar(tsrc, beam_scaling, opacity=opacity_el, \
                                                 gain=gain, elevation=elevation,spillover=self.SPILLOVER, \
                                                 gaincoeffs=self.GAINCOEFFS)
                        
                        
                    if self.cl.units=='tmb':
                        # ASSUMES a reference value for etaB.  This should be made available
                        #   at the command line.  The assumed value is for KFPA only.
                        main_beam_efficiency = self.cal.main_beam_efficiency(self.ETAB_REF, obsfreqHz)
                        tmb = tastar / main_beam_efficiency
                        
                            
                    if self.cl.units=='jy':
                        # ASSUMES a reference value for etaA.  This should be made available
                        #   at the command line.  The assumed value is for KFPA only.
                        aperture_efficiency = self.cal.aperture_efficiency(self.ETAA_REF, obsfreqHz)
                        jy = tastar / (2.85 * aperture_efficiency)
    
                        
                    # used these, so clear for the next iteration
                    sigrefState = [{'calON':None, 'calOFF':None, 'TP':None}, \
                                   {'calON':None, 'calOFF':None, 'TP':None}]
                    
                    # --------------------------------  write data out to FITS file

                    if 'ta' == self.cl.units:
                        row['DATA'] = ta
                    elif 'tsrc' == self.cl.units:
                        row['DATA'] = tsrc
                    elif 'ta*' == self.cl.units:
                        row['DATA'] = tastar
                    elif 'tmb' == self.cl.units:
                        row['DATA'] = tmb
                    elif 'jy' == self.cl.units:
                        row['DATA'] = jy
                    else:
                        print 'ERROR: units not recognized.  Can not write data.'
                        sys.exit(9)
                        
                    row['TSYS'] = tsys


                    output_data[outputidx] = row.data
                    
                    outputidx = outputidx + 1
                    percent_done = '\r' + 'scan ' + str(scan) + ': ' + \
                        str( int((outputidx/float(rows2write))*100) ) + \
                        ' %   '
                    sys.stdout.write(percent_done)
                    sys.stdout.flush()
                    
                    # done looping over rows in a chunk
                
                # done looping over chunks
                
                self.outfile[-1].append(output_data)
                self.outfile.update_hdu_list()
                        
                # done looping over rows in a chunk
                
            # done looping over chunks

        sys.stdout.write('\n')
        self.outfile.close()
        
    def calibrate_ps_sdfits_integrations(self, feed, window, pol, \
                          avgCref1, avgTref1, crefTime1, refTambient1, refElevation1, \
                          avgCref2, avgTref2, crefTime2, refTambient2, refElevation2, \
                          beam_scaling):
        
        dtype = self.create_output_sdfits(feed, window, pol)
        if None == dtype:
            return
        else:
            print 'calibrating feed',feed,'window',window,'polarization',pol

        if self.cl.units != 'ta':
            tsky1,tsky2 = self.getReferenceTsky(feed, window, pol, crefTime1, refTambient1, refElevation1, \
                            crefTime2, refTambient2, refElevation2)
        
        for scan in self.cl.mapscans:
            
            try:
                signalRows = self.rowList.get(scan, feed, window, pol)
            except:
                continue
            
            # get integration rows
            rows = signalRows['ROW']
            ext = signalRows['EXTENSION']
            
            columns = tuple(self.infile[ext].colnames)
        
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
            
            # break the input rows into chunks as buffers to write out
            #   so that we don't write out rows one at a time
            rowchunks = self.set_row_chunks(rows, self.BUFFER_SIZE)

            outputidx = 0
            
            for chunk in rowchunks:
                
                rows2write = self.nOutputRows(chunk, cal_switching, sigref)
                
                output_data = np.zeros(rows2write, dtype=dtype)
                
                # now start at the beginning and calibrate all the integrations
                for idx,rowNum in enumerate(chunk):
                    
                    row = Integration(self.infile[ext][columns][rowNum])
                    
                    if row['CAL'] == 'T':
                        calON = row
                    else:
                        calOFF = row
                    
                    csig = None
                    
                    if cal_switching and calOFF and calON:
                        # noise diode is being fired during signal integrations
        
                        csig = self.cal.Cavg(calON['DATA'], calOFF['DATA'])
        
                        if AVERAGING_SPECTRA_FOR_SUMMARY:
                            exposure = calON['EXPOSURE']+calOFF['EXPOSURE']
                            exposures.append(exposure)
        
                    # if there is more than one row, this isn't the last one, this and the next are CAL=='F',
                    #    then the diode is not firing
                    elif not cal_switching:
                        csig = calOFF['DATA']
                    
                    # we are cal switching but we only have one cal state,
                    #   then read the next row
                    else:
                        continue
                    
                    if csig != None:
                        
                        intTime = self.pu.dateToMjd( calOFF['DATE-OBS'] ) # integration timestamp
                        elevation = calOFF['ELEVATIO'] # integration elevation
                                
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
        
                        if self.cl.units != 'ta':
                            
                            obsfreqHz = self.getObsFreq(feed, window, pol)
                            
                            if tsky1 and tsky2:
                                # get interpolated reference tsky value
                                tsky_ref =  self.cal.interpolate_by_time(tsky1, tsky2,
                                                crefTime1, crefTime2, intTime)
                            elif tsky1 and not tsky2:
                                tsky_ref =  tsky1
                            else:
                                print 'ERROR: no reference tsky value'
                                sys.exit()

                            # ASSUMES a given opacity
                            #   the opacity needs to come from the command line or Ron's
                            #   model database.
                            if not self.OPACITY:
                                intOpacity = self.weather.retrieve_zenith_opacity(intTime, obsfreqHz)
                                if not intOpacity:
                                    print 'ERROR: Not able to retrieve integration zenith opacity for',
                                    print 'calibration to:',self.cl.units
                                    print '  Please supply a zenith opacity or calibrate to Ta.'
                                    sys.exit(9)
                            else:
                                intOpacity = self.OPACITY
                                
                            opacity_el = self.cal.elevation_adjusted_opacity(intOpacity, elevation)
                                
                            # get tsky for the current integration
                            tambient_current = calOFF['TAMBIENT']
                            tsky_current = self.cal.tsky(tambient_current, obsfreqHz, opacity_el)
                           
                            tsky_corr = self.cal.tsky_corr(tsky_current, tsky_ref, self.SPILLOVER)
                                
                            tsrc = ta-tsky_corr
        
                            if AVERAGING_SPECTRA_FOR_SUMMARY:
                                tsrcs.append(tsrc)
                            
                        if self.cl.units=='ta*' or self.cl.units=='tmb' or self.cl.units=='jy':
                            # ASSUMES GAIN COEFFICIENTS and a given opacity
                            #   the opacity needs to come from the command line or Ron's
                            #   model database.  Gain coefficients can optionally come
                            #   from the command line.
                            
                            gain = self.cal.gain(self.cal.GAIN_COEFFICIENTS, elevation)
                            
                            tastar = self.cal.TaStar(tsrc, beam_scaling, opacity=opacity_el, \
                                                     gain=gain, elevation=elevation, spillover=self.SPILLOVER,\
                                                     gaincoeffs=self.GAINCOEFFS)
                            
                            if AVERAGING_SPECTRA_FOR_SUMMARY:
                                tastars.append(tastar)
                            
                        if self.cl.units=='tmb':
                            # ASSUMES a reference value for etaB.  This should be made available
                            #   at the command line.  The assumed value is for KFPA only.
                            main_beam_efficiency = self.cal.main_beam_efficiency(self.ETAB_REF, obsfreqHz)
                            tmb = tastar / main_beam_efficiency
                            
                            if AVERAGING_SPECTRA_FOR_SUMMARY:
                                tmbs.append(tmb)
                                
                        if self.cl.units=='jy':
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
    
                        if 'ta' == self.cl.units:
                            row['DATA'] = ta
                        elif 'tsrc' == self.cl.units:
                            row['DATA'] = tsrc
                        elif 'ta*' == self.cl.units:
                            row['DATA'] = tastar
                        elif 'tmb' == self.cl.units:
                            row['DATA'] = tmb
                        elif 'jy' == self.cl.units:
                            row['DATA'] = jy
                        else:
                            print 'ERROR: units not recognized.  Can not write data.'
                            sys.exit(9)
                            
                        row['TSYS'] = tsys

                    output_data[outputidx] = row.data
                        
                    outputidx = outputidx + 1
                    percent_done = '\r' + 'scan ' + str(scan) + ': ' + \
                        str( int((outputidx/float(rows2write))*100) ) + \
                        ' %   '
                    sys.stdout.write(percent_done)
                    sys.stdout.flush()
                    
                self.outfile[-1].append(output_data)
                self.outfile.update_hdu_list()
                        
                # done looping over a chunk
                
            # done looping over a scan
           
            # make some scan summary information for plotting
            
            if AVERAGING_SPECTRA_FOR_SUMMARY:
                if self.cl.units=='ta':
                    tas = np.array(tas)
                    calibrated_integrations = tas
    
                elif self.cl.units=='tsrc':
                    tsrcs = np.array(tsrcs)
                    calibrated_integrations = tsrcs
                    
                elif self.cl.units=='ta*':
                    tastars = np.array(tastars)
                    calibrated_integrations = tastars
                                                            
                elif self.cl.units=='tmb':
                    tmbs = np.array(tmbs)
                    calibrated_integrations = tmbs
    
                elif self.cl.units=='jy':
                    jys = np.array(jys)
                    calibrated_integrations = jys  
    
            if CREATE_PLOTS:
                ref_tsyss = np.array(ref_tsyss)
                exposures = np.array(exposures)
                weights = exposures / ref_tsyss**2
                averaged_integrations = np.average(calibrated_integrations,axis=0,weights=weights)
                pylab.plot(averaged_integrations,label=str(scan)+' tsys('+str(ref_tsyss.mean())[:5]+')')
                pylab.ylabel(self.cl.units)
                pylab.xlabel('channel')
                pylab.legend(title='scan',loc='upper right')
                pylab.savefig('calibratedScans_f'+str(feed)+'_w'+str(window)+'_p'+str(pol)+'.png')
                pylab.clf()
        
        # done with scans
        sys.stdout.write('\n')
        self.outfile.close()
        
    def CalibrateSdfitsIntegrations(self, feed, window, pol, \
                          avgCref1=None, avgTref1=None, crefTime1=None, refTambient1=None, refElevation1=None, \
                          avgCref2=None, avgTref2=None, crefTime2=None, refTambient2=None, refElevation2=None, \
                          beam_scaling=None):
        
        if avgCref1 != None:
            self.calibrate_ps_sdfits_integrations(feed, window, pol, \
                          avgCref1, avgTref1, crefTime1, refTambient1, refElevation1, \
                          avgCref2, avgTref2, crefTime2, refTambient2, refElevation2, \
                          beam_scaling)
        else:
            self.calibrate_fs_sdfits_integrations(feed, window, pol, \
                          beam_scaling)
            
    def __del__(self):
            
        print 'bye'
