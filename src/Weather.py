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
        self.last_requested_freq_hz = None
        self.last_zenith_opacity = None
        self.number_of_opacity_files = None
        self.opacity_coeffs = None
        self.L_BAND_ZENITH_TAU = .008
        
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
                coeffs.append((float(line.split('{{')[0]), \
                    [float(xx) for xx in line.split('{{')[1].split('}')[0].split(' ')], \
                    [float(xx) for xx in line.split('{{')[2].split('}')[0].split(' ')], \
                    [float(xx) for xx in line.split('{{')[3].split('}')[0].split(' ')]))
                   
        else:
            print "WARNING: Could not read coefficients for Tau in", opacity_coefficients_filename
            return False
    
        return coeffs

    def retrieve_zenith_opacity(self, integration_mjd_timestamp, freq_hz, log=None):

        freq_ghz = freq_hz/1e9
        
        # if less than 2 GHz, opacity coefficients are not available
        if freq_ghz < 2:
            return self.L_BAND_ZENITH_TAU

        # if the frequency is the same as the last requested and
        #  this time is within the same record (1 hr window) of the last
        #  recorded opacity coefficients, then just reuse the last
        #  zenith opacity value requested

        if self.last_requested_freq_hz and self.last_requested_freq_hz == freq_hz and \
                integration_mjd_timestamp >= self.last_integration_mjd_timestamp and \
                integration_mjd_timestamp < self.last_integration_mjd_timestamp + .04167:
            
            return self.last_zenith_opacity
        
        self.last_integration_mjd_timestamp = integration_mjd_timestamp
        self.last_requested_freq_hz = freq_hz
                
        # retrieve a list of opacity coefficients files, based on a given directory
        # and filename structure
        opacity_coefficients_filename = False
        opacity_files = glob.glob(\
          '/users/rmaddale/Weather/ArchiveCoeffs/CoeffsOpacityFreqList_avrg_*.txt')
        self.number_of_opacity_files = len(opacity_files)
        
        if 0 == self.number_of_opacity_files:
            if log:
                log.doMessage('WARN', 'WARNING: No opacity coefficients file')
            else:
                print 'WARNING: No opacity coefficients file'
            return False
            
        # sort the list of files so they are in chronological order
        opacity_files.sort()
        
        # the following will become True if integration_mjd_timestamp is older than available ranges
        # provided in the opacity coefficients files
        tooearly = False
        # check the date of each opacity coefficients file
        for idx, opacity_candidate_file in enumerate(opacity_files):
            dates = opacity_candidate_file.split('_')[-2:]
            opacity_file_timestamp = []
            for date in dates:
                opacity_file_timestamp.append(int(date.split('.')[0]))
            opacity_file_starttime = opacity_file_timestamp[0]
            opacity_file_stoptime = opacity_file_timestamp[1]

            # set tooearly = True when integration_mjd_timestamp is older than available ranges
            if idx == 0 and integration_mjd_timestamp < opacity_file_starttime:
                tooearly = True
                break
        
            if integration_mjd_timestamp >= opacity_file_starttime \
            and integration_mjd_timestamp < opacity_file_stoptime:
                opacity_coefficients_filename = opacity_candidate_file
                break

        if not opacity_coefficients_filename:
            if tooearly:
                if log:
                    log.doMessage('ERR', 'ERROR: Date is too early for opacities.')
                    log.doMessage('ERR', '  Try setting zenith tau at command line.')
                    log.doMessage('ERR', integration_mjd_timestamp, '<', opacity_file_starttime)
                else:
                    print 'ERROR: Date is too early for opacities.'
                    print '  Try setting zenith tau at command line.'
                    print integration_mjd_timestamp, '<', opacity_file_starttime
                sys.exit(9)
            else:
                # if the mjd in the index file comes after the date string in all of the
                # opacity coefficients files, then we can assume the current opacity
                # coefficients file will apply.  a date string is only added to the opacity
                # coefficients file when it is no longer the most current.
                opacity_coefficients_filename = \
                  '/users/rmaddale/Weather/ArchiveCoeffs/CoeffsOpacityFreqList_avrg.txt'
        
        # opacities coefficients filename
        if opacity_coefficients_filename and os.path.exists(opacity_coefficients_filename):
            if log:
                log.doMessage('DBG', 'Using coefficients from', opacity_coefficients_filename)
            else:
                print 'Using coefficients from', opacity_coefficients_filename
            self.opacity_coeffs = self._retrieve_opacity_coefficients(opacity_coefficients_filename)
        else:
            if log:
                log.doMessage('WARN', 'WARNING: No opacity coefficients file')
            else:
                print 'WARNING: No opacity coefficients file'
            return False

        for coeffs_line in self.opacity_coeffs:

            if integration_mjd_timestamp >= coeffs_line[0]:
                prev_time = coeffs_line[0]
                if (freq_ghz >= 2 and freq_ghz <= 22):
                    prev_coeffs = coeffs_line[1]
                elif (freq_ghz > 22 and freq_ghz <= 50):
                    prev_coeffs = coeffs_line[2]
                elif (freq_ghz > 50 and freq_ghz <= 116):
                    prev_coeffs = coeffs_line[3]
            elif integration_mjd_timestamp < coeffs_line[0]:
                next_time = coeffs_line[0]
                if (freq_ghz >= 2 and freq_ghz <= 22):
                    next_coeffs = coeffs_line[1]
                elif (freq_ghz > 22 and freq_ghz <= 50):
                    next_coeffs = coeffs_line[2]
                elif (freq_ghz > 50 and freq_ghz <= 116):
                    next_coeffs = coeffs_line[3]
                break

        time_corrected_coeffs = []
        for coeff in zip(prev_coeffs, next_coeffs):
            new_coeff = self.cal.interpolate_by_time(coeff[0], coeff[1],
                                                     prev_time, next_time,
                                                     integration_mjd_timestamp)
            time_corrected_coeffs.append(new_coeff)
        
        zenith_opacity = self.cal.zenith_opacity(time_corrected_coeffs, freq_ghz)
        self.last_zenith_opacity = zenith_opacity
        
        return zenith_opacity
