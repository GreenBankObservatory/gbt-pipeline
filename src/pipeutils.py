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

import math
import os
import subprocess
import sys
import logging
import time
import glob

import pyfits
import numpy as np

# message levels
class msg:
    CRIT = 1
    ERR = 2
    WARN = 3
    INFO = 4
    DBG = 5

class Pipeutils:

        
    def gd2jd(self, day,month,year,hour,minute,second):
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
    
        dd=int(day)
        mm=int(month)
        yyyy=int(year)
        hh=float(hour)
        min=float(minute)
        sec=float(second)
    
        UT=hh+min/60+sec/3600
    
        total_seconds=hh*3600+min*60+sec
    
        if (100*yyyy+mm-190002.5)>0:
            sig=1
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
        jd = self.gd2jd(day,month,year,hour,minute,second)
        mjd = jd - 2400000.5
        return mjd
    
    def interpolate(self, vals,xx,yy):
        """Interpolate with increasing or decreasing x-axis values
        
        Keywords:
        vals -- vector of x values to interpolate
        xx -- known x-axis values
        yy -- known y-axis values (must be same length as xx)
        
        """
        
        decreasing_xx_axis=False
        
        interp_vals = np.zeros((len(yy),len(vals)))
    
        # see if xx is decreasing
        if xx.ndim==1 and xx[0] > xx[-1] or xx.ndim==2 and xx[0][0] > xx[0][-1]:
            if xx.ndim==1:
                xx_reversed = xx[::-1]
                yy_reversed = yy[::-1]
                interp_vals = np.interp(vals,xx_reversed,yy_reversed)
            elif xx.ndim==2:
                xx_reversed = [ee[::-1] for ee in xx]
                yy_reversed = [ee[::-1] for ee in yy]
                for idx,ee in enumerate(yy_reversed):
                    interp_vals[idx] = np.interp(vals,xx_reversed[idx],ee)
        else:
            if xx.ndim==1:
                interp_vals = np.interp(vals,xx,yy)
            if xx.ndim==2:
                for idx,ee in enumerate(yy):
                    interp_vals[idx] = np.interp(vals,xx[idx],ee)
    
        return interp_vals
    
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
        wavelength = hz2wavelength(hz) # in meters
        diameter = 100. # estimate of telescope diameter in meters
        rayleigh_criterion_factor = 1.22
        arcseconds_per_radian = 206265
        # return diffraction limit in arc seconds
        return ((rayleigh_criterion_factor * wavelength)/diameter) \
                * arcseconds_per_radian
       
    def interpolate_reference(self, refs,dates,tskys,tsyss, mjds):
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
            lo_hi = (chan_lo,chan_hi)
            spectra.append(np.interp(mjds,dates,lo_hi))
        spec = np.array(spectra).transpose()
    
        # dumb way
        # do each freq channel separately
        tsky = []
        if np.any(tskys):
            for chan in range(len(tskys[0])):
                tsky_lo = tskys[0][chan]
                tsky_hi = tskys[1][chan]
                tskylo_hi = (tsky_lo,tsky_hi)
                newvals = np.interp(mjds,dates,tskylo_hi)
                tsky.append(newvals)
            tsky = np.array(tsky).transpose()
        
        # interpolate reference tsys
        tsys = np.interp(mjds,dates,tsyss)
        tsys = tsys.reshape((len(tsys),1))
        
        return spec,tsky,tsys

    
    def _gain(self, gain_coeff,elevation):
        """
        >>> _gain((.91,.00434,-5.22e-5),60)
        0.99321999999999999
    
        """
        # comput gain based on elevation, eqn. 12 in PS specification
        gain = 0
        zz = 90. - elevation
    
        for idx,coeff in enumerate(gain_coeff):
            gain = gain + coeff * zz**idx
            
        return gain
    
    def ta_correction(self, zenithtau,gain_coeff,spillover,\
            opacity_coefficients,mjds,elevations,freq,verbose=0):
        """Compute correction to Ta for determining Ta*
        
        Correction is for atmospheric attenuation, rear spillover, ohmic loss
        and blockage efficiency.
        
        Keywords:
        zenithtau -- (float) zenith opacity value set by user; it overrides the
            use of zenith values obtained from GB weather forecasting scripts
        gain_coeff -- (list) of gain coefficients set with default values or
            overriden by the user
        spillover -- (float) constant set by default or overriden by the user
        opacity_coefficients -- a (list) of coefficent values read from GBT
            weather files stored on the GB network
        mjds -- (numpy 1d array) of dates, one for each output row
            read from the FITS input table as DATE
        elevations -- (numpy 1d array) of elevations, either one for each output
            row or a single value if all integrations are at the same elevation
            read from the FITS input table at ELEVATION
        freq -- (numpy 2d array) of first and last channel frequency values, one
            pair for each output row in GHz
        
        All of this equates to the right part of equation 13 in the PS document
        and equation 15 in the FS document.
        
        Returns:
        Ta correction factor at every frequency for every time and elevation
        
        """
        opacities = []
        meanfreq = freq[0].mean()
    
        if meanfreq >= 2 and not opacity_coefficients and not zenithtau:
            return False
        else:
            for idx,mjd in enumerate(mjds):
                if len(elevations)>1:
                    elevation = elevations[idx]
                    gain = _gain(gain_coeff,elevation)
    
                    if zenithtau:
                        zenith_opacities = np.ones(freq.shape) * zenithtau
                    else:
                        # get the correct set of coefficients for this time
                        if meanfreq < 2:
                            coeffs = ()
                        else:
                            for coeffs_line in opacity_coefficients:
                                if mjd > coeffs_line[0]:
                                    if (meanfreq >= 2 and meanfreq <= 22):
                                        coeffs = coeffs_line[1]
                                    elif (meanfreq > 22 and meanfreq <= 50):
                                        coeffs = coeffs_line[2]
                                    elif (meanfreq > 50 and meanfreq <= 116):
                                        coeffs = coeffs_line[3]
    
                        # get the zenith opacity of the first and last frequency for
                        #    every integration of the scan
                        zenith_opacities = zenith_opacity(coeffs,freq)
                        # get a more accurate list of opacities by correcting for
                        #    elevation
                    opacities.append(corrected_opacity(zenith_opacities[idx],elevation))
    
                else:
                    elevation = elevations[0]
                    gain = _gain(gain_coeff,elevation)
    
                    if zenithtau:
                        zenith_opacities = np.ones(freq.shape) * zenithtau
                    else:
                        # get the correct set of coefficients for this time
                        if meanfreq < 2:
                            coeffs = ()
                        else:
                            for coeffs_line in opacity_coefficients:
                                    if mjd > coeffs_line[0]:
                                        if (meanfreq >= 2 and meanfreq <= 22):
                                            coeffs = coeffs_line[1]
                                        elif (meanfreq > 22 and meanfreq <= 50):
                                            coeffs = coeffs_line[2]
                                        elif (meanfreq > 50 and meanfreq <= 116):
                                            coeffs = coeffs_line[3]
    
                        zenith_opacities = zenith_opacity(coeffs,freq)
                    opacities.append(corrected_opacity(zenith_opacities,elevation))
    
            opacities = np.array(opacities)
    
            if opacities.ndim == opacities.size:
                opacities = opacities[0]
    
            # return right part of equation 13
            return (np.array(opacities)) / (spillover * gain)
        
    def tsky(self, ambient_temp,freq,opacity_factors):
        """Determine the sky temperature contribution at each frequency
        
        Keywords:
        ambient_temp -- (float) mean ambient temperature value for scan, as read
            from the TAMBIENT column in the SDFITS input file
        freq -- (numpy 1d array) with the first and last frequency values on an
            axis
        opacity_factors -- (numpy 1d array) with an opacity value (e^-tau) for
             each frequency
        Returns:
        the sky model temperature contribution at every frequncy channel of the
        spectrum
        """
        freq_lo = freq[0]
        freq_hi = freq[-1]
    
        airTemp_lo = tatm(freq_lo,ambient_temp-273.15)
        airTemp_hi = tatm(freq_hi,ambient_temp-273.15)
        
        tsky_lo = airTemp_lo * (1-opacity_factors[0])
        tsky_hi = airTemp_hi * (1-opacity_factors[-1])
        
        nchan = len(freq)
        delta_tsky = (tsky_hi - tsky_lo) / float(nchan)
        
        # interpolate between lo and hi frequency opacities
        tskys = interpolate(freq,np.array([freq_lo,freq_hi]),np.array([tsky_lo,tsky_hi]))
        
        return tskys
    
    def masked_array(self, array):
        """Mask nans in an array
        
        Keywords:
        array -- (numpy nd array)
        
        Returns:
        numpy masked array with nans masked out
        
        """
        return np.ma.masked_array(array,np.isnan(array))
        
    
   
    def sampler_summary(self, logger,samplermap):
        """Print a summary of samplers used in a map
    
        Keywords:
        logger -- where to send output
        samplermap -- data structure holding sampler information
    
        """
        
        import operator
        samplermap_sorted = sorted(samplermap.iteritems(), key=operator.itemgetter(1))
        doMessage(logger,msg.INFO,'Map sampler summary:')
        doMessage(logger,msg.INFO,'sampler\tfeed\tpol\tcenterfreq')
        doMessage(logger,msg.INFO,'-------\t----\t---\t----------')
        for sampler in samplermap_sorted:
            message = '%s\t%s\t%s\t%g' % (sampler[0],sampler[1][0],sampler[1][1],sampler[1][2])
            doMessage(logger,msg.INFO,message)
    
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
                print repr(':'.join(item)),'not convertable to integer'
                raise
    
            if 1==len(int_item):
                # single inclusive or exclusive item
                if int_item[0] < 0:
                    excludelist.add(abs(int_item[0]))
                else:
                    oklist.add(int_item[0])
    
            elif 2==len(int_item):
                # range
                if int_item[0] <= int_item[1]:
                    if int_item[0] < 0:
                        print item[0],',',item[1],'must start with a non-negative number'
                        return []
    
                    if int_item[0]==int_item[1]:
                        thisrange = [int_item[0]]
                    else:
                        thisrange = range(int_item[0],int_item[1]+1)
    
                    for ii in thisrange:
                        oklist.add(ii)
                else:
                    print item[0],',',item[1],'needs to be in increasing order'
                    raise
            else:
                print item,'has more than 2 values'
    
        for exitem in excludelist:
            try:
                oklist.remove(exitem)
            except(KeyError):
                oklist = [ str(item) for item in oklist ]
                print 'ERROR: excluded item', exitem, 'does not exist in inclusive range'
                raise
    
        oklist = [ str(item) for item in oklist ]
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
                print repr(':'.join(item)),'not convertable to integer'
                raise
    
            # single inclusive or exclusive item
            if 1==len(int_item) and int_item[0] >= 0:
                return True
    
            elif 2==len(int_item):
                return True
    
        return False
    
    
    def commandSummary(self, logger,opt):
        """Print a summary of the options controlling the pipeline run.
    
        Keywords:
        logger -- where the output will be written
        opt -- command options
    
        """
    
        class prettyfloat(float):
            def __repr__(self):
                return "%0.2g" % self
    
        doMessage(logger,msg.INFO,"---------------")
        doMessage(logger,msg.INFO,"Command summary")
        doMessage(logger,msg.INFO,"---------------")
        doMessage(logger,msg.INFO,"Input file....................",opt.infile)
        doMessage(logger,msg.INFO,"Calibrating to units of.......",opt.units)
        if not opt.allmaps:
            doMessage(logger,msg.INFO,"Map scans.....................",opt.mapscans[0],'to',opt.mapscans[-1])
        doMessage(logger,msg.INFO,"creating all maps.............",opt.allmaps)
        doMessage(logger,msg.INFO,"display idlToSdfits plots ....",opt.display_idlToSdfits)
        doMessage(logger,msg.INFO,"spillover factor (eta_l)......",str(opt.spillover))
        doMessage(logger,msg.INFO,"aperture efficiency (eta_A0)..",str(opt.aperture_eff))
        doMessage(logger,msg.INFO,"main beam efficiency (eta_B0)..",str(opt.mainbeam_eff))
        
        if opt.gaincoeffs:
            pretty_gaincoeffs = map(prettyfloat, opt.gaincoeffs)
            doMessage(logger,msg.INFO,"gain coefficiencts............",str(pretty_gaincoeffs))
        
        if opt.gain_left:
            pretty_gains_left = map(prettyfloat, opt.gain_left)
            doMessage(logger,msg.INFO,"relative gain factors (LL) ...",str(pretty_gains_left))
    
        if opt.gain_right:
            pretty_gains_right = map(prettyfloat, opt.gain_right)
            doMessage(logger,msg.INFO,"relative gain factors (RR) ...",str(pretty_gains_right))
    
        doMessage(logger,msg.INFO,"disable mapping ..............",opt.imagingoff)
        doMessage(logger,msg.INFO,"map scans for scale ..........",opt.mapscansforscale)
        if opt.feed:
            doMessage(logger,msg.INFO,"feed(s) ......................",opt.feed)
        else:
            doMessage(logger,msg.INFO,"feed(s) ...................... All")
            
        if opt.pol:
            doMessage(logger,msg.INFO,"polarization .................",opt.pol)
        else:
            doMessage(logger,msg.INFO,"polarization ................. All")
    
        doMessage(logger,msg.INFO,"verbosity level...............",str(opt.verbose))
    
        doMessage(logger,msg.INFO,"overwrite existing output.....",str(opt.clobber))
    
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
    
    def maptype(self, firstscan,indexfile,debug=False):
        """Return a string describing the type of the mapping block
    
        Typically, this will say whether a map used position-switched (PS) calibration
        or frequency-switched (FS) calibration.
    
        Keywords:
        firstscan -- the first scan number of the map
        indexfile -- used to determine the number of switching states
        debug -- optional debug flag
    
        Returns:
        a string describing the type of the mapping block
        'PS' == position-switched
        'FS' == frequency-switched
        'UNKNOWN' == other
    
        """
        myFile = open(indexfile,'rU')
    
        scans = {}
        map_scans = {}
    
        # skip over the index file header lines
        while True:
            row = myFile.readline().split()
            if len(row)==40:
                # we just found the column keywords, so read the next line
                row = myFile.readline().split()
                break
    
        states = set([])
        while row:
    
            scan = int(row[10])
    
            if scan == firstscan:
                states.add(row[18])
            elif scan > firstscan:
                break
    
            # read the next row
            row = myFile.readline().split()
    
        myFile.close()
    
        if debug:
            print states
    
        if len(states) == 2:
            return 'FS'
        elif len(states) == 1:
            return 'PS'
        else:
            return 'UKNOWN'
    
    def gainfactor(self, logger,opt,samplermap,sampler):
        """Returns gain factor set for a given beam and polarization
    
        Keywords:
        logger -- where to write output
        opt -- structure which holds gain factors
        samplermap -- lists samplers for each mapping block
        sampler -- sampler representing beam and polarization which needs gain adjustment
    
        Returns:
        (float) gain for a given feed number and sampler name
    
        """
        # set relative gain factors for each beam/pol
        #  if they are supplied
        if opt.gain_left and samplermap[sampler][1]=='LL':
            doMessage(logger,msg.DBG,'Multiplying by gain factor',
                opt.gain_left[samplermap[sampler][0]-1])
            gain_factor = opt.gain_left[samplermap[sampler][0]-1]
        elif opt.gain_right and samplermap[sampler][1]=='RR':
            doMessage(logger,msg.DBG,'Multiplying by gain factor',
                opt.gain_right[samplermap[sampler][0]-1])
            gain_factor = opt.gain_right[samplermap[sampler][0]-1]
        else:
            gain_factor = float(1)
    
        return gain_factor
    
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
