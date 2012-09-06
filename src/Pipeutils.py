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

import numpy as np

class Pipeutils:
    
    def __init__(self, log = None):
        
        self.log = log

    def gd2jd(self, day, month, year, hour, minute, second):
        """Converts a gregorian date to julian date.
    
        Keyword arguments:
        day -- 2 digit day string
        month -- 2 digit month string
        year -- 4 digit year string
        hour -- 2 digit hour string
        minute -- 2 digit minute string
        second -- N digit second string
    
        Returns:
        a floating point value which is the julian date
        """
    
        dd = int(day)
        mm = int(month)
        yyyy = int(year)
        hh = float(hour)
        minute = float(minute)
        sec = float(second)
    
        UT = hh+minute/60+sec/3600
    
        if (100*yyyy+mm-190002.5)>0:
            sig = 1
        else:
            sig=-1
    
        JD = 367*yyyy - int(7*(yyyy+int((mm+9)/12))/4) + int(275*mm/9) + dd + 1721013.5 + UT/24 - 0.5*sig +0.5
    
        return JD
    
    def dateToMjd(self, dateString):
        """Convert a FITS DATE string to Modified Julian Date
    
        Keyword arguments:
        dateString -- a FITS format date string, ie. '2009-02-10T21:09:00.08'
    
        Returns:
        floating point Modified Julian Date
    
        """
    
        year  = dateString[:4]
        month = dateString[5:7]
        day   = dateString[8:10]
        hour  = dateString[11:13]
        minute= dateString[14:16]
        second= dateString[17:]
    
        # now convert from julian day to mjd
        jd = self.gd2jd(day, month, year, hour, minute, second)
        mjd = jd - 2400000.5
        return mjd
    
    def hz2wavelength(self, f):
        """Simple frequency (Hz) to wavelength conversion
        
        Keywords:
        f -- input frequency in Hz
        
        Returns:
        wavelength in meters
    
        >>> hz2wavelength(23e9)
        0.013034454695652174
    
        """
        c = 299792458.  # speed of light in m/s
        return (c/f)
       
    def gbtbeamsize(self, hz):
        """Estimate the GBT beam size at a given frequency
        
        Keywords:
        hz -- frequency in Hz
        
        Returns:
        beam size in arc seconds
        
        >>> gbtbeamsize(23e9)
        32.800331933144086
    
        """
        wavelength = self.hz2wavelength(hz) # in meters
        diameter = 100. # estimate of telescope diameter in meters
        rayleigh_criterion_factor = 1.22
        arcseconds_per_radian = 206265
        # return diffraction limit in arc seconds
        return ((rayleigh_criterion_factor * wavelength)/diameter) \
                * arcseconds_per_radian
       
    def interpolate_reference(self, refs, dates, tskys, tsyss, mjds):
        """Compute time-interpolated reference spectrum, tsky and tsys
        
        Keywords:
        refs -- (list 2 masked numpy arrays) each one a reference spectrum
        dates -- (list) of two mjd dates, each associated with a reference spectrum
        tskys -- (list 2 numpy arrays) holding sky model temperature values to
            subtract from each channel, one array for each reference spectrum
        tsyss -- (list) of two reference system temperatures, one for each spectrum
        mjds -- (numpy 1d array) of mjd values for each integration.  we will
            interpolate the other (y) values from these from these (x) input points
        
        Returns:
        Interpolated spectrum, sky model temperature values (tsky) and system
        temperatures (tsys) at each date (mjd) between the refrences, inclusive.
        
        This is used when there are two off source refrence scans with PS maps.
        
        """
        # we want a stack of interpolated spectra
        # dumb way
        # do each freq channel separately
        spectra = []
        for chan in range(len(refs[0])):
            chan_lo = refs[0][chan]
            chan_hi = refs[1][chan]
            lo_hi = (chan_lo, chan_hi)
            spectra.append(np.interp(mjds, dates, lo_hi))
        spec = np.array(spectra).transpose()
    
        # dumb way
        # do each freq channel separately
        tsky = []
        if np.any(tskys):
            for chan in range(len(tskys[0])):
                tsky_lo = tskys[0][chan]
                tsky_hi = tskys[1][chan]
                tskylo_hi = (tsky_lo, tsky_hi)
                newvals = np.interp(mjds, dates, tskylo_hi)
                tsky.append(newvals)
            tsky = np.array(tsky).transpose()
        
        # interpolate reference tsys
        tsys = np.interp(mjds, dates, tsyss)
        tsys = tsys.reshape((len(tsys), 1))
        
        return spec, tsky, tsys

    
    def _gain(self, gain_coeff, elevation):
        """
        >>> _gain((.91, .00434, -5.22e-5), 60)
        0.99321999999999999
    
        """
        # comput gain based on elevation, eqn. 12 in PS specification
        gain = 0
        zz = 90. - elevation
    
        for idx, coeff in enumerate(gain_coeff):
            gain = gain + coeff * zz**idx
            
        return gain
    
    def masked_array(self, array):
        """Mask nans in an array
        
        Keywords:
        array -- (numpy nd array)
        
        Returns:
        numpy masked array with nans masked out
        
        """
        return np.ma.masked_array(array, np.isnan(array))
        
    
   
    def parserange(self, rangelist):
        """Given a range string, produce a list of integers
    
        Inclusive and exclusive integers are both possible.
    
        The range string 1:4,6:8,10 becomes 1,2,3,4,6,7,8,10
        The range string 1:4,-2 becomes 1,3,4
    
        Keywords:
        rangelist -- a range string with inclusive ranges and exclusive integers
    
        Returns:
        a (list) of integers
    
        >>> parserange('1:4,6:8,10')
        ['1', '10', '2', '3', '4', '6', '7', '8']
        >>> parserange('1:4,-2')
        ['1', '3', '4']
    
        """
    
        oklist = set([])
        excludelist = set([])
    
        rangelist = rangelist.replace(' ','')
        rangelist = rangelist.split(',')
    
        # item is single value or range
        for item in rangelist:
            item = item.split(':')
    
            # change to ints
            try:
                int_item = [ int(ii) for ii in item ]
            except(ValueError):
                print repr(':'.join(item)), 'not convertable to integer'
                raise
    
            if 1 == len(int_item):
                # single inclusive or exclusive item
                if int_item[0] < 0:
                    excludelist.add(abs(int_item[0]))
                else:
                    oklist.add(int_item[0])
    
            elif 2 == len(int_item):
                # range
                if int_item[0] <= int_item[1]:
                    if int_item[0] < 0:
                        print item[0], ',', item[1], 'must start with a non-negative number'
                        return []
    
                    if int_item[0]==int_item[1]:
                        thisrange = [int_item[0]]
                    else:
                        thisrange = range(int_item[0], int_item[1]+1)
    
                    for ii in thisrange:
                        oklist.add(ii)
                else:
                    print item[0], ',', item[1], 'needs to be in increasing order'
                    raise
            else:
                print item, 'has more than 2 values'
    
        for exitem in excludelist:
            try:
                oklist.remove(exitem)
            except(KeyError):
                oklist = [ str(item) for item in oklist ]
                print 'ERROR: excluded item', exitem, 'does not exist in inclusive range'
                raise

        return sorted(list(oklist))
    
    def is_inclusive_range(self, rangelist):
        """Determine if a range is not an excluded integer
    
        For example, if '-5' is the range then return False.
        If 1:6,-5 is the range, return True because it is really 1:4,6
    
        Keywords:
        rangelist -- a string with integers to check
    
        Returns:
        (boolean) stating whether or not the range has exlusive values
    
        >>> is_inclusive_range('-5')
        False
        >>> is_inclusive_range('1:6,-5')
        True
    
        """
        rangelist = rangelist.replace(' ','')
        rangelist = rangelist.split(',')
    
        # item is single value or range
        for item in rangelist:
            item = item.split(':')
    
            # change to ints
            try:
                int_item = [ int(ii) for ii in item ]
            except(ValueError):
                print repr(':'.join(item)), 'not convertable to integer'
                raise
    
            # single inclusive or exclusive item
            if 1 == len(int_item) and int_item[0] >= 0:
                return True
    
            elif 2 == len(int_item):
                return True
    
        return False
        
    def string_to_floats(self, string_list):
        """Change a list of numbers to a list of floats
    
        Keywords:
        string_list -- a comma-seperated list of numbers
        
        Returns:
        a (list) of floats
    
        >>> string_to_floats('1.1,-5.55555,6e6')
        [1.1000000000000001, -5.5555500000000002, 6000000.0]
    
        """
        string_list = string_list.replace(' ','')
        string_list = string_list.split(',')
        return [ float(item) for item in string_list ]
    
