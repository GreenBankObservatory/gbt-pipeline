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

import sys
import os
import glob

from Calibration import Calibration


class Weather:

    def __init__(self):

        self.cal = Calibration()
        self.last_integration_mjd_timestamp = None
        self.last_requested_freq_ghz = None
        self.zenith_opacity = None
        self.opacity_coeffs = None
        self.L_BAND_ZENITH_TAU = .008
        self.frequency_range = None
        self.time_range = None
        self.db_time_range = None
        self.log = None

    def _opacity_database(self, timestamp):
        # retrieve a list of opacity coefficients files, based on a given directory
        # and filename structure
        opacity_coefficients_filename = False
        opacity_files = glob.glob('/home/gbtpipeline/weather/CoeffsOpacityFreqList_avrg_*.txt')

        if 0 == len(opacity_files):
            return False, False

        # sort the list of files so they are in chronological order
        opacity_files.sort()

        # check the date of each opacity coefficients file
        for idx, opacity_candidate_file in enumerate(opacity_files):
            dates = opacity_candidate_file.split('_')[-2:]
            opacity_file_timestamp = []
            for date in dates:
                opacity_file_timestamp.append(int(date.split('.')[0]))
            opacity_file_starttime = opacity_file_timestamp[0]
            opacity_file_stoptime = opacity_file_timestamp[1]

            # when timestamp is older than available ranges
            if idx == 0 and timestamp < opacity_file_starttime:
                if self.log:
                    self.log.doMessage('ERR', 'ERROR: Date is too early for opacities.')
                    self.log.doMessage('ERR', '  Try setting zenith tau at command line.')
                    self.log.doMessage('ERR', timestamp, '<', opacity_file_starttime)
                else:
                    print 'ERROR: Date is too early for opacities.'
                    print '  Try setting zenith tau at command line.'
                    print timestamp, '<', opacity_file_starttime
                sys.exit(9)
                break

            if (opacity_file_starttime <= timestamp < opacity_file_stoptime):
                opacity_coefficients_filename = opacity_candidate_file
                opacity_db_range = (opacity_file_starttime, opacity_file_stoptime)
                break

        # uses most recent info
        if not opacity_coefficients_filename:
            # if the mjd in the index file comes after the date string in all of the
            # opacity coefficients files, then we can assume the current opacity
            # coefficients file will apply.  a date string is only added to the opacity
            # coefficients file when it is no longer the most current.
            opacity_coefficients_filename = '/home/gbtpipeline/weather/CoeffsOpacityFreqList_avrg.txt'
            opacity_db_range = 'LATEST'

        # opacities coefficients filename
        if opacity_coefficients_filename and os.path.exists(opacity_coefficients_filename):
            if self.log:
                self.log.doMessage('DBG', 'Using coefficients from', opacity_coefficients_filename)
            else:
                print 'Using coefficients from', opacity_coefficients_filename
            coeffs = self._retrieve_opacity_coefficients(opacity_coefficients_filename)
            return coeffs, opacity_db_range
        else:
            if self.log:
                self.log.doMessage('ERR', 'No opacity coefficients file')
            else:
                print 'ERROR: No opacity coefficients file'
            return False, False

    def _retrieve_opacity_coefficients(self, opacity_coefficients_filename):
        """Return opacities (taus) derived from a list of coeffients

        These coefficients are produced from Ron Madalenna's getForecastValues script

        Keywords:
        infilename -- input file name needed for project name
        mjd -- date for data
        freq -- list of frequencies for which we seek an opacity

        Returns:
        a list of opacity coefficients for the time range of the dataset

        """
        opacity_file = open(opacity_coefficients_filename, 'r')

        coeffs = []
        if opacity_file:
            for line in opacity_file:
                # find the most recent forecast and parse out the coefficients for
                # each band
                # coeffs[0] is the mjd timestamp
                # coeffs[1] are the coefficients for 2-22 GHz
                # coeffs[2] are the coefficients for 22-50 GHz
                # coeffs[3] are the coefficients for 70-116 GHz
                coeffs.append((float(line.split('{{')[0]),
                               [float(xx) for xx in line.split('{{')[1].split('}')[0].split(' ')],
                               [float(xx) for xx in line.split('{{')[2].split('}')[0].split(' ')],
                               [float(xx) for xx in line.split('{{')[3].split('}')[0].split(' ')]))

        else:
            print "WARNING: Could not read coefficients for Tau in", opacity_coefficients_filename
            return False

        return coeffs

    def retrieve_zenith_opacity(self, integration_mjd_timestamp, freq_hz, log=None):

        self.log = log

        freq_ghz = freq_hz/1e9

        # if less than 2 GHz, opacity coefficients are not available
        if freq_ghz < 2:
            return self.L_BAND_ZENITH_TAU

        # if the frequency is in the same range and
        # the time is within the same record (1 hr window) of the last
        # recorded opacity coefficients, then just reuse the last
        # zenith opacity value requested
        if ((self.frequency_range and
            (self.frequency_range[0] <= freq_ghz <= self.frequency_range[1])) and
            (self.time_range and
             (self.time_range[0] <= integration_mjd_timestamp <= self.time_range[1]))):

            return self.zenith_opacity

        self.last_integration_mjd_timestamp = integration_mjd_timestamp
        self.last_requested_freq_ghz = freq_ghz

        # if we don't have a db time range OR
        # we do have a time range AND
        #   the range is 'LATEST' AND
        #      timestamp is not w/in the same hour as the last set of coeffs, OR
        #   the range has values AND
        #      our new timestamp is not in the range
        # THEN
        # get another set of coefficients from a different file
        if ((not self.db_time_range) or
            (self.db_time_range == 'LATEST' and
             not (self.time_range[0] <= integration_mjd_timestamp < self.time_range[1])) or
            (self.db_time_range and
             not (self.db_time_range[0] <= integration_mjd_timestamp < self.db_time_range[1]))):

            log.doMessage('DBG', '-----------------------------------------------------')
            log.doMessage('DBG', 'Time or Frequency out of range. Determine new opacity')
            log.doMessage('DBG', '-----------------------------------------------------')
            log.doMessage('DBG', 'opacity', self.zenith_opacity)
            log.doMessage('DBG', 'timestamp', integration_mjd_timestamp, 'prev.', self.last_integration_mjd_timestamp)
            log.doMessage('DBG', 'freq', freq_ghz, 'prev.', self.last_requested_freq_ghz)
            log.doMessage('DBG', 'freq range', self.frequency_range)
            if bool(self.frequency_range):
                log.doMessage('DBG', '   freq in range == ', bool(self.frequency_range[0] <= freq_ghz <= self.frequency_range[1]))
            log.doMessage('DBG', 'time range', self.time_range)
            if bool(self.time_range):
                log.doMessage('DBG', '   time in range ==', bool(self.time_range and (self.time_range[0] <= integration_mjd_timestamp <= self.time_range[1])))
            log.doMessage('DBG', 'DB time range', self.db_time_range)
            if bool(self.db_time_range):
                log.doMessage('DBG', '   time in DB range ==', bool(self.db_time_range and (self.db_time_range[0] <= integration_mjd_timestamp <= self.db_time_range[1])))

            self.opacity_coeffs, self.db_time_range = self._opacity_database(integration_mjd_timestamp)
            if (not self.opacity_coeffs) or (not self.db_time_range):
                return False

            log.doMessage('DBG', 'DB time range:', self.db_time_range)

        for coeffs_line in self.opacity_coeffs:
            if (2 <= freq_ghz <= 22):
                self.frequency_range = (2, 22)
                coefficients_index = 1

            elif (22 < freq_ghz <= 50):
                self.frequency_range = (22, 50)
                coefficients_index = 2

            elif (50 < freq_ghz <= 116):
                self.frequency_range = (50, 116)
                coefficients_index = 3

            if integration_mjd_timestamp >= coeffs_line[0]:
                prev_time = coeffs_line[0]
                prev_coeffs = coeffs_line[coefficients_index]

            elif integration_mjd_timestamp < coeffs_line[0]:
                next_time = coeffs_line[0]
                next_coeffs = coeffs_line[coefficients_index]
                break

        self.time_range = (prev_time, next_time)
        log.doMessage('DBG', 'Coefficient entry time range:', self.time_range)

        time_corrected_coeffs = []
        for coeff in zip(prev_coeffs, next_coeffs):
            new_coeff = self.cal.interpolate_by_time(coeff[0], coeff[1],
                                                     prev_time, next_time,
                                                     integration_mjd_timestamp)
            time_corrected_coeffs.append(new_coeff)

        self.zenith_opacity = self.cal.zenith_opacity(time_corrected_coeffs, freq_ghz)
        log.doMessage('DBG', 'Zenith opacity:', self.zenith_opacity)

        return self.zenith_opacity
