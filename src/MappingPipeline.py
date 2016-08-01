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
from Weather import Weather
from PipeLogging import Logging
from settings import *

import numpy as np

import os
import sys

if CREATE_PLOTS:
    import pylab


class MappingPipeline:

    def __init__(self, cl_params, row_list, feed, window, pol, term):

        self.term = term
        self.log = None

        self.pu = Pipeutils()
        self.cal = Calibration(cl_params.smoothing_kernel)
        self.weather = Weather()
        self.sdf = SdFits()

        self.cl = cl_params  # store command line params locally

        self.infilename = cl_params.infilename

        try:
            self.infile = fitsio.FITS(cl_params.infilename)
        except ValueError, eee:
            self.log.doMessage('ERR', 'Input', eee)
            sys.exit()

        self.outfile = None
        self.outfilename = None

        self.row_list = row_list
        self.CLOBBER = cl_params.clobber

        try:
            self.create_output_sdfits(feed, window, pol)
        except KeyError:
            raise

        if not cl_params.mapscans:
            self.cl.mapscans = row_list.scans()

        # command line options
        self.OPACITY = cl_params.zenithtau
        self.ETAB_REF = cl_params.mainbeam_eff
        self.ETAA_REF = cl_params.aperture_eff
        self.SPILLOVER = cl_params.spillover

        self.BUFFER_SIZE = 1000

    def get_beam_scale(self, receiver, beam_scaling, feed, pol):

        if beam_scaling == 1:
            return beam_scaling

        if receiver == 'RcvrArray18_26':

            if len(beam_scaling) != 14:
                self.log.doMessage('ERR', 'You need to supply 14 beam '
                                   'scaling factors for the KFPA receiver.  The '
                                   'format is a comma-separated list of values '
                                   'orded by feed and polarization: '
                                   '0L,0R,1L,1R,2L,2R,etc.')
                sys.exit(9)
            else:
                beam_scaling = np.array(beam_scaling)
                beam_scaling = beam_scaling.reshape((7, 2))
                return beam_scaling[feed][pol]

        elif receiver == 'Rcvr18_26':
            if len(beam_scaling) != 4:
                self.log.doMessage('ERR', 'You need to supply 4 beam '
                                   'scaling factors for the K-band receiver.  The '
                                   'format is a comma-separated list of values '
                                   'orded by feed and polarization: '
                                   '0L,0R,1L,1R')
                sys.exit(9)
            else:
                beam_scaling = np.array(beam_scaling)
                beam_scaling = beam_scaling.reshape((2, 2))
                return beam_scaling[feed][pol]
            

        else:
            self.log.doMessage('ERR', 'Beam scaling factors not known for '
                               'receiver:', receiver)
            os.unlink(self.outfilename)
            sys.exit(9)

    def determineSetup(self, sdfits_row_structure, ext):

        # ------------------ look ahead at first few rows to determine setup
        #  is the noise diode firing?
        #  are there signal and reference components?

        lookahead_cal_states = set([])
        lookahead_sig_states = set([])

        # fill the buffers
        for rowNum in sdfits_row_structure[:4]:
            columns = ('CAL', 'SIG')
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

    def getReference(self, scan, feed, window, pol, beam_scaling):

        referenceRows = self.row_list.get(scan, feed, window, pol)

        if not referenceRows:
            return None

        ext = referenceRows['EXTENSION']
        rows = referenceRows['ROW']

        crefs = []  # each element will be an average of noise diode on & off pairs
        tsyss = []  # each element corresponds to the combined noise diode on & off, see Calibration().tsys()
        cal_on = None  # to hold the integration with noise diode ON
        cal_off = None  # to hold the integration with noise diode OFF
        exposures = []   # each element is total exposure, used for weighting the average of reference integrations
        timestamps = []  # each element is an average to use for interpolation bt/wn references
        tambients = []   # from the cal_off integration, used for tsky computation for ta* and beyond
        elevations = []  # from the call_off integration, used for tsky computation for ta* and beyond

        columns = tuple(self.infile[ext].get_colnames())

        for rowNum in rows:

            row = Integration(self.infile[ext][columns][rowNum])

            if row['CAL'] == 'T':
                cal_on = row
            else:
                cal_off = row

            if cal_off and cal_on:

                # look for "bad" spectra: all NaNs or all zeros
                if np.all(np.isnan(cal_off.data['DATA'])) or \
                   np.all(np.isnan(cal_on.data['DATA'])) or \
                   0 == cal_off.data['DATA'].ptp() or \
                   0 == cal_on.data['DATA'].ptp():
                    self.log.doMessage('DBG', 'Bad integration. '
                                       'Skipping row', rowNum, 'from input data.')
                    continue

                receiver = cal_off['FRONTEND'].strip()

                beam_scale = self.get_beam_scale(receiver, beam_scaling, feed, pol)
                cref, tsys, exposure, timestamp, tambient, elevation = self.sdf.getReferenceIntegration(cal_on, cal_off, beam_scale)

                # used these, so clear for the next iteration
                cal_off = None
                cal_on = None

                # collect raw spectra and tsys values for each integration
                #   these will be averaged to use for calibration
                crefs.append(cref)
                tsyss.append(tsys)
                exposures.append(exposure)
                timestamps.append(timestamp)
                tambients.append(tambient)
                elevations.append(elevation)

        avgCref, avgTsys, avgTimestamp, avgTambient, avgElevation, sumExposure = \
            self.cal.getReferenceAverage(crefs, tsyss, exposures, timestamps, tambients, elevations)

        self.log.doMessage('INFO', 'Tsys for scan {scan} feed {feed} '
                           'window {window} pol {pol}: '
                           '{tsys:.1f}'.format(scan=scan, feed=feed,
                                               window=window, pol=pol,
                                               tsys=avgTsys))

        return avgCref, avgTsys, avgTimestamp, avgTambient, avgElevation, sumExposure

    def get_dtype(self, feed, window, pol):

        try:
            signalRows = self.row_list.get(self.cl.mapscans[0], feed, window, pol)
            ext = signalRows['EXTENSION']
        except KeyError:
            raise
        dtype = self.infile[ext][0].dtype

        return dtype

    def create_output_sdfits(self, feed, window, pol):

        try:
            signalRows = self.row_list.get(self.cl.mapscans[0], feed, window, pol)
            ext = signalRows['EXTENSION']
            rows = signalRows['ROW']
            columns = tuple(self.infile[ext].get_colnames())
            firstIntegration = Integration(self.infile[ext][columns][rows[0]])
            targetname = firstIntegration['OBJECT'].replace(" ", "")

        except KeyError:
            print('WARNING: Can not find data for scan {scan} window {win} feed {feed} polarization {pol}'.format(scan=self.cl.mapscans[0], win=window, feed=feed, pol=pol))
            raise

        self.outfilename = targetname + '_scan_' + str(self.cl.mapscans[0]) + '_' + str(self.cl.mapscans[-1]) + '_window' + str(window) + '_feed' + str(feed) + '_pol' + str(pol) + '.fits'

        self.log = Logging(self.cl, self.outfilename.rstrip('.fits'))

        if self.CLOBBER is False and os.path.exists(self.outfilename):
            self.log.doMessage('WARN', ' Will not overwrite existing pipeline output.\nConsider using \'--clobber\' option to overwrite.')
            sys.exit()

        # create a new table
        old_stdout = sys.stdout
        from cStringIO import StringIO
        sys.stdout = StringIO()
        # redirect stdout to not get clobber file warnings
        self.outfile = fitsio.FITS(self.outfilename, 'rw', clobber=True)
        sys.stdout = old_stdout

        dtype = self.infile[ext][0].dtype

        input_header = fitsio.read_header(self.infilename, ext)
        self.outfile.create_table_hdu(dtype=dtype, extname=input_header['EXTNAME'])
        self.outfile[-1].write_keys(input_header)
        self.outfile[-1]._update_info()
        self.outfile.update_hdu_list()

        # copy primary header from input to output file
        primary_header = fitsio.read_header(self.infilename, 0)
        self.outfile[0].write_keys(primary_header)

        self.outfile[0].write_key('PIPE_VER', PIPELINE_VERSION, comment="GBT Pipeline Version")

        return dtype

    def multi_tskys(self, crefTime2, refTambient2, refElevation2):

        if (crefTime2 is not None) and (refTambient2 is not None) and (refElevation2 is not None):
            return True
        else:
            return False

    def set_row_chunks(self, rows, WRITESIZE=100):

        nrows = len(rows)
        rowchunks = []
        startchunk = 0
        while nrows > 0:
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
        signalRows = self.row_list.get(self.cl.mapscans[0], feed, window, pol)
        ext = signalRows['EXTENSION']
        rows = signalRows['ROW']
        columns = tuple(self.infile[ext].get_colnames())
        firstIntegration = Integration(self.infile[ext][columns][rows[0]])

        # integration observed frequency
        # we assume this center of band frequency is the same for all integrations
        #  in both the reference scans and the map scans
        obsfreqHz = firstIntegration['OBSFREQ']

        return obsfreqHz

    def getReferenceTsky(self, feed, window, pol, crefTime1, refTambient1, refElevation1,
                         crefTime2, refTambient2, refElevation2):

        multiple_reference_scans_for_tsky = self.multi_tskys(crefTime2, refTambient2, refElevation2)

        obsfreqHz = self.getObsFreq(feed, window, pol)

        # tsky for reference 1
        if not self.OPACITY:
            self.log.doMessage('DBG', 'Getting opacity for reference Tsky: 1st reference')
            ref1_zenith_opacity = self.weather.retrieve_zenith_opacity(crefTime1, obsfreqHz, self.log)
            if not ref1_zenith_opacity:
                self.log.doMessage('ERR', 'Not able to retrieve reference 1 zenith opacity\n  Please supply a zenith opacity or calibrate to Ta.')
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
                self.log.doMessage('DBG', 'Getting opacity for reference Tsky: 2nd reference')
                ref2_zenith_opacity = self.weather.retrieve_zenith_opacity(crefTime2, obsfreqHz, self.log)
                if not ref2_zenith_opacity:
                    self.log.doMessage('ERR', 'Not able to retrieve reference 2 zenith opacity for calibration to:', self.cl.units, '\n  Please supply a zenith opacity or calibrate to Ta.')
                    sys.exit(9)
            else:
                ref2_zenith_opacity = self.OPACITY

            opacity2 = self.cal.elevation_adjusted_opacity(ref2_zenith_opacity, refElevation2)

            # get tsky at center frequency
            tsky2 = self.cal.tsky(refTambient2, obsfreqHz, opacity2)

        return tsky1, tsky2

    def nOutputRows(self, listOfRows, cal_switching, sigref):

        rows2write = len(listOfRows)

        if cal_switching:
            rows2write = rows2write / 2
        if sigref:
            rows2write = rows2write / 2

        return rows2write

    def calibrate_fs_sdfits_integrations(self, feed, window, pol, beam_scaling):

        dtype = self.get_dtype(feed, window, pol)
        if dtype is None:
            return

        for scan in self.cl.mapscans:

            try:
                inputRows = self.row_list.get(scan, feed, window, pol)
            except:
                continue

            # get integration rows
            rows = inputRows['ROW']
            ext = inputRows['EXTENSION']

            columns = tuple(self.infile[ext].get_colnames())

            cal_switching, sigref = self.determineSetup(rows, ext)

            if not cal_switching or not sigref:
                self.log.doMessage('ERR', 'Expected frequency-switched scan', scan, 'does not have 2 signal states and 2 noise diode (cal) states')
                self.outfile.close()
                # if this is the first scan, remove the output file because the table will be empty
                if scan == self.cl.mapscans[0]:
                    os.unlink(self.outfilename)
                sys.exit()

            # break the input rows into chunks as buffers to write out
            #   so that we don't write out rows one at a time
            rowchunks = self.set_row_chunks(rows, self.BUFFER_SIZE)

            for chunk in rowchunks:

                outputidx = 0

                rows2write = self.nOutputRows(chunk, cal_switching, sigref)

                output_data = np.zeros(rows2write, dtype=dtype)

                sigrefState = [{'cal_on': None, 'cal_off': None, 'TP': None, 'rownum': None},
                               {'cal_on': None, 'cal_off': None, 'TP': None, 'rownum': None}]

                # now start at the beginning and calibrate all the integrations
                for rowNum in chunk:

                    row = Integration(self.infile[ext][columns][rowNum])

                    if row['SIG'] == 'T':
                        if row['CAL'] == 'T':
                            sigrefState[0]['cal_on'] = row
                        else:
                            sigrefState[0]['cal_off'] = row

                        sigrefState[0]['rownum'] = rowNum
                        obsfreqHz = row['OBSFREQ']

                    else:
                        if row['CAL'] == 'T':
                            sigrefState[1]['cal_on'] = row
                        else:
                            sigrefState[1]['cal_off'] = row

                        sigrefState[1]['rownum'] = rowNum

                    # we need 4 states to calibrate FS integrations
                    if sigrefState[0]['cal_on'] and sigrefState[0]['cal_off'] and \
                       sigrefState[1]['cal_on'] and sigrefState[1]['cal_off']:

                        if (np.all(np.isnan(sigrefState[0]['cal_on']['DATA'].data)) or
                            np.all(np.isnan(sigrefState[0]['cal_off']['DATA'].data)) or
                            np.all(np.isnan(sigrefState[1]['cal_on']['DATA'].data)) or
                            np.all(np.isnan(sigrefState[1]['cal_off']['DATA'].data)) or
                            (0 == sigrefState[0]['cal_off']['DATA'].ptp() and
                             0 == sigrefState[0]['cal_on']['DATA'].ptp()) or
                            (0 == sigrefState[1]['cal_off']['DATA'].ptp() and
                             0 == sigrefState[1]['cal_on']['DATA'].ptp())):

                            self.log.doMessage('DBG', 'Bad integration. '
                                               'Writing nan values to output.  Input rows',
                                               sigrefState[0]['rownum'],
                                               sigrefState[1]['rownum'])

                            # create an output row with 'nan' data and real metadata
                            output_data[outputidx] = row.data

                            #
                            # we can probably replace the following line with a more pythonic
                            #
                            # for xx in output_data[outputidx]['DATA']:
                            #     xx = float('nan')
                            #
                            for xx in range(len(output_data[outputidx]['DATA'])):
                                output_data[outputidx]['DATA'][xx] = float('nan')

                            outputidx = outputidx + 1

                            self.show_progress(outputidx, rows2write)

                            # used these, so clear for the next iteration
                            sigrefState = [{'cal_on': None, 'cal_off': None, 'TP': None, 'rownum': None, 'EXPOSURE': None},
                                           {'cal_on': None, 'cal_off': None, 'TP': None, 'rownum': None, 'EXPOSURE': None}]
                            continue

                        # noise diode is being fired during signal integrations
                        sigrefState[0]['TP'], sigrefState[0]['EXPOSURE'] = self.cal.total_power(sigrefState[0]['cal_on']['DATA'],
                                                                                                sigrefState[0]['cal_off']['DATA'],
                                                                                                sigrefState[0]['cal_on']['EXPOSURE'],
                                                                                                sigrefState[0]['cal_off']['EXPOSURE'])
                        sigrefState[1]['TP'], sigrefState[1]['EXPOSURE'] = self.cal.total_power(sigrefState[1]['cal_on']['DATA'],
                                                                                                sigrefState[1]['cal_off']['DATA'],
                                                                                                sigrefState[1]['cal_on']['EXPOSURE'],
                                                                                                sigrefState[1]['cal_off']['EXPOSURE'])

                    else:
                        continue  # read more rows until we have all 4 states

                    # integration timestamp and elevation
                    #  should be same for all states
                    intTime = self.pu.dateToMjd(sigrefState[0]['cal_off']['DATE-OBS'])
                    elevation = sigrefState[0]['cal_off']['ELEVATIO']
                    receiver = sigrefState[0]['cal_off']['FRONTEND'].strip()

                    beam_scale = self.get_beam_scale(receiver, beam_scaling, feed, pol)
                    ta, tsys, exposure = self.cal.ta_fs(sigrefState, beam_scale)

                    if self.cl.units != 'ta':

                        if not self.OPACITY:
                            intOpacity = self.weather.retrieve_zenith_opacity(intTime, obsfreqHz, self.log)
                            if not intOpacity:
                                self.log.doMessage('ERR', 'Not able to retrieve integration '
                                                   'zenith opacity for calibration to:', self.cl.units,
                                                   '\n  Please supply a zenith opacity or calibrate to Ta.')
                                sys.exit(9)
                        else:
                            intOpacity = self.OPACITY

                        opacity_el = self.cal.elevation_adjusted_opacity(intOpacity, elevation)

                    if (self.cl.units == 'ta*') or (self.cl.units == 'tmb') or (self.cl.units == 'jy'):
                        tastar = self.cal.ta_star(ta, opacity=opacity_el, spillover=self.SPILLOVER)

                    if self.cl.units == 'tmb':
                        main_beam_efficiency = self.cal.main_beam_efficiency(self.ETAB_REF, obsfreqHz)
                        tmb = tastar / main_beam_efficiency

                    if self.cl.units == 'jy':
                        aperture_efficiency = self.cal.aperture_efficiency(self.ETAA_REF, obsfreqHz)
                        jy = tastar / (2.85 * aperture_efficiency)

                    # used these, so clear for the next iteration
                    sigrefState = [{'cal_on': None, 'cal_off': None, 'TP': None},
                                   {'cal_on': None, 'cal_off': None, 'TP': None}]

                    # --------------------------------  write data out to FITS file

                    if 'ta' == self.cl.units:
                        row['DATA'] = ta
                    elif 'ta*' == self.cl.units:
                        row['DATA'] = tastar
                    elif 'tmb' == self.cl.units:
                        row['DATA'] = tmb
                    elif 'jy' == self.cl.units:
                        row['DATA'] = jy
                    else:
                        self.log.doMessage('ERR', 'units not recognized.  Can not write data.')
                        sys.exit(9)

                    row['TSYS'] = tsys
                    row['TUNIT7'] = self.cl.units.title()  # .title() makes first letter upper
                    row['EXPOSURE'] = exposure
                    row['OBSFREQ'] = obsfreqHz
                    row['CRVAL1'] = obsfreqHz

                    output_data[outputidx] = row.data

                    outputidx = outputidx + 1

                    self.show_progress(outputidx, rows2write)

                    # done looping over rows in a chunk

                # done looping over chunks
                self.outfile[-1].append(output_data)
                self.outfile.update_hdu_list()

                # done looping over rows in a chunk

            # done looping over chunks

        self.outfile.close()

    def calibrate_ps_sdfits_integrations(self, feed, window, pol,
                                         avgCref1, avgTsys1, crefTime1, refTambient1,
                                         refElevation1, refExposure1,
                                         avgCref2, avgTsys2, crefTime2, refTambient2,
                                         refElevation2, refExposure2):

        dtype = self.get_dtype(feed, window, pol)
        if dtype is None:
            return
        else:
            self.log.doMessage('DBG', 'calibrating feed', feed, 'window', window, 'polarization', pol)

        if self.cl.units != 'ta' and self.cl.tsky:
            tsky1, tsky2 = self.getReferenceTsky(feed, window, pol, crefTime1, refTambient1, refElevation1,
                                                 crefTime2, refTambient2, refElevation2)

        for scan in self.cl.mapscans:

            try:
                signalRows = self.row_list.get(scan, feed, window, pol)
            except:
                self.log.doMessage('WARN', '{t.bold}WARNING{t.normal}: '
                                   'Scan {scan} not found.'.format(scan=scan, t=self.term))
                continue

            # get integration rows
            rows = signalRows['ROW']
            ext = signalRows['EXTENSION']

            columns = tuple(self.infile[ext].get_colnames())

            if CREATE_PLOTS:
                tas = []
                tsrcs = []
                tastars = []
                tmbs = []
                jys = []
                exposures = []

            if CREATE_PLOTS:
                ref_tsyss = []

            cal_switching, sigref = self.determineSetup(rows, ext)

            cal_on = None
            cal_off = None

            # break the input rows into chunks as buffers to write out
            #   so that we don't write out rows one at a time
            rowchunks = self.set_row_chunks(rows, self.BUFFER_SIZE)

            outputidx = 0

            for chunk in rowchunks:

                rows2write = self.nOutputRows(chunk, cal_switching, sigref)

                output_data = np.zeros(rows2write, dtype=dtype)

                # now start at the beginning and calibrate all the integrations
                for rowNum in chunk:

                    row = Integration(self.infile[ext][columns][rowNum])

                    if row['CAL'] == 'T':
                        cal_on = row
                    else:
                        cal_off = row

                    csig = None

                    if cal_switching and cal_off and cal_on:
                        # noise diode is being fired during signal integrations

                        csig, sig_exposure = self.cal.total_power(cal_on['DATA'], cal_off['DATA'],
                                                                  cal_on['EXPOSURE'], cal_off['EXPOSURE'])

                        if CREATE_PLOTS:
                            exposures.append(sig_exposure)

                    # if there is more than one row, this isn't the last one, this and the next are CAL=='F',
                    #    then the diode is not firing
                    elif not cal_switching:
                        csig, sig_exposure = cal_off['DATA'], cal_off['EXPOSURE']

                    # we are cal switching but we only have one cal state,
                    #   then read the next row
                    else:
                        continue

                    if csig is not None:

                        intTime = self.pu.dateToMjd(cal_off['DATE-OBS'])  # integration timestamp
                        elevation = cal_off['ELEVATIO']  # integration elevation
                        receiver = cal_off['FRONTEND'].strip()

                        if (avgCref2 is not None) and (crefTime2 is not None):
                            crefInterp = \
                                self.cal.interpolate_by_time(avgCref1, avgCref2,
                                                             crefTime1, crefTime2, intTime)

                            avgTsysInterp = \
                                self.cal.interpolate_by_time(avgTsys1, avgTsys2,
                                                             crefTime1, crefTime2, intTime)
                            if refExposure2:
                                refExposure = (refExposure1+refExposure2)/2.
                            else:
                                refExposure = refExposure1
                            ta, exposure = self.cal.antenna_temp(avgTsysInterp, csig, crefInterp,
                                                                 sig_exposure, refExposure)
                            tsys = avgTsysInterp
                        else:
                            if refExposure2:
                                refExposure = (refExposure1+refExposure2)/2.
                            else:
                                refExposure = refExposure1

                            ta, exposure = self.cal.antenna_temp(avgTsys1, csig, avgCref1,
                                                                 sig_exposure, refExposure)

                            tsys = avgTsys1

                        if CREATE_PLOTS:
                            tas.append(ta)

                        if CREATE_PLOTS:
                            ref_tsyss.append(avgTsys1)

                        if self.cl.units != 'ta':

                            obsfreqHz = self.getObsFreq(feed, window, pol)

                            if self.cl.tsky:
                                if tsky1 and tsky2:
                                    # get interpolated reference tsky value
                                    tsky_ref = self.cal.interpolate_by_time(tsky1, tsky2,
                                                                            crefTime1, crefTime2, intTime)
                                elif tsky1 and not tsky2:
                                    tsky_ref = tsky1
                                else:
                                    self.log.doMessage('ERR', 'no reference tsky value')
                                    sys.exit()

                            # ASSUMES a given opacity
                            #   the opacity needs to come from the command line or Ron's
                            #   model database.
                            if not self.OPACITY:
                                intOpacity = self.weather.retrieve_zenith_opacity(intTime, obsfreqHz, self.log)
                                if not intOpacity:
                                    self.log.doMessage('ERR', 'Not able to retrieve integration zenith opacity for calibration to:', self.cl.units, '\n  Please supply a zenith opacity or calibrate to Ta.')
                                    sys.exit(9)
                                else:
                                    if 0 == outputidx:
                                        self.log.doMessage('DBG', ('Zenith opacity, win {win} feed {feed} pol {pol} '
                                                                   'scan {scan} freq {freq} time {time}:'.format(win=window, scan=scan, freq=obsfreqHz,
                                                                                                                 feed=feed, pol=pol, time=intTime)), intOpacity)
                            else:
                                intOpacity = self.OPACITY

                            opacity_el = self.cal.elevation_adjusted_opacity(intOpacity, elevation)

                            tsrc = ta

                            if self.cl.tsky:
                                # get tsky for the current integration
                                tambient_current = cal_off['TAMBIENT']
                                tsky_current = self.cal.tsky(tambient_current, obsfreqHz, opacity_el)

                                tsky_correction = self.cal.tsky_correction(tsky_current, tsky_ref, self.SPILLOVER)

                                tsrc -= tsky_correction

                            if CREATE_PLOTS:
                                tsrcs.append(tsrc)

                        if (self.cl.units == 'ta*') or (self.cl.units == 'tmb') or (self.cl.units == 'jy'):
                            # ASSUMES GAIN COEFFICIENTS and a given opacity
                            #   the opacity needs to come from the command line or Ron's
                            #   model database.  Gain coefficients can optionally come
                            #   from the command line.

                            tastar = self.cal.ta_star(tsrc, opacity=opacity_el, spillover=self.SPILLOVER)

                            if CREATE_PLOTS:
                                tastars.append(tastar)

                        if self.cl.units == 'tmb':
                            # ASSUMES a reference value for etaB.  This should be made available
                            #   at the command line.  The assumed value is for KFPA only.
                            main_beam_efficiency = self.cal.main_beam_efficiency(self.ETAB_REF, obsfreqHz)
                            tmb = tastar / main_beam_efficiency

                            if CREATE_PLOTS:
                                tmbs.append(tmb)

                        if self.cl.units == 'jy':
                            # ASSUMES a reference value for etaA.  This should be made available
                            #   at the command line.  The assumed value is for KFPA only.
                            aperture_efficiency = self.cal.aperture_efficiency(self.ETAA_REF, obsfreqHz)
                            jy = tastar / (2.85 * aperture_efficiency)

                            if CREATE_PLOTS:
                                jys.append(jy)

                        # used these, so clear for the next iteration
                        cal_off = None
                        cal_on = None

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
                            self.log.doMessage('ERR', 'units not recognized.  Can not write data.')
                            sys.exit(9)

                        row['TSYS'] = tsys
                        row['TUNIT7'] = self.cl.units.title()
                        row['EXPOSURE'] = exposure

                    output_data[outputidx] = row.data

                    outputidx = outputidx + 1

                    self.show_progress(outputidx, rows2write)

                # done looping over a chunk

                self.outfile[-1].append(output_data)
                self.outfile.update_hdu_list()

            # done looping over a scan

            # make some scan summary information for plotting

            if CREATE_PLOTS:
                if self.cl.units == 'ta':
                    tas = np.array(tas)
                    calibrated_integrations = tas

                elif self.cl.units == 'tsrc':
                    tsrcs = np.array(tsrcs)
                    calibrated_integrations = tsrcs

                elif self.cl.units == 'ta*':
                    tastars = np.array(tastars)
                    calibrated_integrations = tastars

                elif self.cl.units == 'tmb':
                    tmbs = np.array(tmbs)
                    calibrated_integrations = tmbs

                elif self.cl.units == 'jy':
                    jys = np.array(jys)
                    calibrated_integrations = jys

            if CREATE_PLOTS:
                ref_tsyss = np.array(ref_tsyss)
                exposures = np.array(exposures)
                averaged_integrations = self.cal.average_spectra(calibrated_integrations, ref_tsyss, exposures)
                pylab.plot(averaged_integrations, label=str(scan)+' tsys('+str(ref_tsyss.mean())[:5]+')')

        if CREATE_PLOTS:
            pylab.ylabel(self.cl.units)
            pylab.xlabel('channel')
            pylab.legend(title='scan', loc='upper right')
            pylab.savefig('calibratedScans_f'+str(feed)+'_w'+str(window)+'_p'+str(pol)+'.png')
            pylab.clf()

        # done with scans
        self.outfile.close()

    def show_progress(self, outputidx, rows2write):
        percent_done = int((outputidx/float(rows2write))*100)
        if percent_done % 25 == 0:
            sys.stdout.write('.')

        sys.stdout.flush()

    def calibrate_sdfits_integrations(self, feed, window, pol,
                                      avgCref1=None, avgTsys1=None, crefTime1=None, refTambient1=None,
                                      refElevation1=None, refExposure1=None,
                                      avgCref2=None, avgTsys2=None, crefTime2=None, refTambient2=None,
                                      refElevation2=None, refExposure2=None, beam_scaling=None):

        if avgCref1 is not None:
            self.calibrate_ps_sdfits_integrations(feed, window, pol,
                                                  avgCref1, avgTsys1, crefTime1, refTambient1,
                                                  refElevation1, refExposure1,
                                                  avgCref2, avgTsys2, crefTime2, refTambient2,
                                                  refElevation2, refExposure2)
        else:
            self.calibrate_fs_sdfits_integrations(feed, window, pol, beam_scaling)

    def __del__(self):
        pass
