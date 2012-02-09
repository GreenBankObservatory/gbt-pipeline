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

def timestamp():
    """Return a string with the current date and time

    The format of the string is: dd.mm.yyyy_hh:mm:ss

    """
    lt = time.localtime(time.time())
    return "%02d.%02d.%04d_%02d:%02d:%02d" % (lt[2], lt[1], lt[0], lt[3], lt[4], lt[5])
    
# message levels
class msg:
    CRIT = 1
    ERR = 2
    WARN = 3
    INFO = 4
    DBG = 5
    
def doMessage(logger,level,*args):
    """Write a message to the log file

    Keyword arguments:
    logger -- the log handler object
    level -- the level of the message (ERR,WARN,INFO,etc.)
    args -- the message text; this is a variable lengh list

    """
    message = ' '.join(map(str,(args)))
    if msg.CRIT == level:
        logger.critical(message)
    elif msg.ERR == level:
        logger.error(message)
    elif msg.WARN == level:
        logger.warning(message)
    elif msg.INFO == level:
        logger.info(message)
    elif msg.DBG == level:
        logger.debug(message)
    else:
        logger.critical(message)

def configure_logfile(opt,logfilename,toconsole=True):
    """Configure the format and levels for the logfile

    Keyword arguments:
    opt -- user-defined verbosity options
    logfilename -- name of desired log file
    toconsole -- optional console output

    """
    LEVELS = {5: logging.DEBUG, # errors + warnings + summary + debug
              4: logging.INFO, # errors + warnings + summary
              3: logging.WARNING, # errors + warnings
              2: logging.ERROR, # errors only
              1: logging.CRITICAL, # unused
              0: logging.CRITICAL} # no output 

    level = LEVELS.get(opt.verbose, logging.DEBUG)

    loggername = logfilename.split('.')[0]
    logger = logging.getLogger(loggername)
    
    # logging level defaults to WARN, so we need to override it
    logger.setLevel(logging.DEBUG)
    
    # create file handler which logs even debug messages
    fh = logging.FileHandler(filename=logfilename,mode='w')
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)

    if toconsole:
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(level)
        # create formatter and add it to the handlers
        ch_formatter = logging.Formatter("%(message)s")
        ch.setFormatter(ch_formatter)
        # add the handlers to logger
        logger.addHandler(ch)
    
    return logger
    
def gd2jd(day,month,year,hour,minute,second):
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

def dateToMjd(dateString):
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
    jd = gd2jd(day,month,year,hour,minute,second)
    mjd = jd - 2400000.5
    return mjd

def interpolate(vals,xx,yy):
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

def hz2wavelength(f):
    """Simple frequency (Hz) to wavelength conversion
    
    Keywords:
    f -- input frequency in Hz
    
    Returns:
    wavelength in meters

    >>> hz2wavelength(23e9)
    0.013034454695652174

    """
    c = 299792458  # speed of light in m/s
    return (c/f)

def eta(eta0,freqHz):
    """Determine aperture efficiency
    
    Keyword attributes:
    freqHz -- input frequency in Hz

    Returns:
    eta -- point or main beam efficiency (range 0 to 1)
    
    EtaA model is from memo by Jim Condon, provided by Ron Maddalena

    >>> eta(.71,23e9)
    0.64748265789117276

    >>> eta(.91,23e9)
    0.82987213898727774

    """

    BB = .0132 # Ruze equation parameter
    freqGHz = float(freqHz)/1e9
    eta = eta0 * math.e**-((BB * freqGHz)**2)
    
    return eta
   
def gbtbeamsize(hz):
    """Estimate the GBT beam size at a given frequency
    
    Keywords:
    hz -- frequency in Hz
    
    Returns:
    beam size in arc seconds
    
    >>> gbtbeamsize(23e9)
    32.800331933144086

    """
    wavelength = hz2wavelength(hz) # in meters
    diameter = 100 # estimate of telescope diameter in meters
    rayleigh_criterion_factor = 1.22
    arcseconds_per_radian = 206265
    # return diffraction limit in arc seconds
    return ((rayleigh_criterion_factor * wavelength)/diameter) \
            * arcseconds_per_radian
   
def interpolate_reference(refs,dates,tskys,tsyss, mjds):
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

def opacity_coefficients(opacity_coefficients_filename):
    """Return opacities (taus) derived from a list of coeffients
    
    These coefficients are produced from Ron Madalenna's getForecastValues script
    
    Keywords:
    infilename -- input file name needed for project name
    mjd -- date for data
    freq -- list of frequencies for which we seek an opacity
    
    Returns:
    a list of opacity coefficients for the time range of the dataset
    
    """
    FILE = open(opacity_coefficients_filename,'r')

    coeffs = []
    if FILE:
        for line in FILE:
            # find the most recent forecast and parse out the coefficients for 
            # each band
            # coeffs[0] is the mjd timestamp
            # coeffs[1] are the coefficients for 2-22 GHz
            # coeffs[2] are the coefficients for 22-50 GHz
            # coeffs[3] are the coefficients for 70-116 GHz
            coeffs.append((float(line.split('{{')[0]),\
                [float(xx) for xx in line.split('{{')[1].split('}')[0].split(' ')],\
                [float(xx) for xx in line.split('{{')[2].split('}')[0].split(' ')],\
                [float(xx) for xx in line.split('{{')[3].split('}')[0].split(' ')]))
               
    else:
        if opt.verbose > 1:
            print "WARNING: Could not read coefficients for Tau in",opacity_coefficients_filename
        return False

    return coeffs


def natm(elDeg):
    """Compute number of atmospheres at elevation (deg)

    Keyword arguments:
    elDeg -- input elevation in degrees

    Returns:
    nAtmos -- output number of atmospheres

    Estimate the number of atmospheres along the line of site
    at an input elevation

    This comes from a model reported by Ron Maddale

    1) A = 1/sin(elev) is a good approximation down to about 15 deg but
    starts to get pretty poor below that.  Here's a quick-to-calculate,
    better approximation that I determined from multiple years worth of
    weather data and which is good down to elev = 1 deg:
    
    if (elev LT 39):
    A = -0.023437  + 1.0140 / math.sin( (math.pi/180.)*(elev + 5.1774 /
        (elev + 3.3543) ) )
    else:
    A = math.sin(math.pi*elev/180.)

    natm model is provided by Ron Maddalena
    
    """

    DEGREE = math.pi/180.

    if (elDeg < 39.):
        nAtmos = -0.023437 + \
            (1.0140 / math.sin( DEGREE*(elDeg + 5.1774 / (elDeg + 3.3543))))
    else:
        nAtmos =1./math.sin(DEGREE*elDeg)

    #print 'Model Number of Atmospheres:', nAtmos,' at elevation ',elDeg
    return 1./nAtmos
    

def tatm(freqHz, tmpC):
    """Estimates the atmospheric effective temperature
    
    Keyword arguments:
    freqHz -- input frequency in Hz
    where: tmpC     - input ground temperature in Celsius

    Returns:
    airTempK -- output Air Temperature in Kelvin

    Based on local ground temperature measurements.  These estimates
    come from a model reported by Ron Maddalena
    
    1) A = 1/sin(elev) is a good approximation down to about 15 deg but
    starts to get pretty poor below that.  Here's a quick-to-calculate,
    better approximation that I determined from multiple years worth of
    weather data and which is good down to elev = 1 deg:

        if (elev LT 39) then begin
            A = -0.023437  + 1.0140 / sin( (!pi/180.)*(elev + 5.1774 / (elev
    + 3.3543) ) )
        else begin
            A = sin(!pi*elev/180.)
        endif 

    2) Using Tatm = 270 is too rough an approximation since Tatm can vary
    from 244 to 290, depending upon the weather conditions and observing
    frequency.  One can derive an approximation for the default Tatm that is
    accurate to about 3.5 K from the equation:

    TATM = (A0 + A1*FREQ + A2*FREQ^2 +A3*FREQ^3 + A4*FREQ^4 + A5*FREQ^5)
                + (B0 + B1*FREQ + B2*FREQ^2 + B3*FREQ^3 + B4*FREQ^4 +
    B5*FREQ^5)*TMPC

    where TMPC = ground-level air temperature in C and Freq is in GHz.  The
    A and B coefficients are:

                                A0=    259.69185966 +/- 0.117749542
                                A1=     -1.66599001 +/- 0.0313805607
                                A2=     0.226962192 +/- 0.00289457549
                                A3=   -0.0100909636 +/- 0.00011905765
                                A4=   0.00018402955 +/- 0.00000223708
                                A5=  -0.00000119516 +/- 0.00000001564
                                B0=      0.42557717 +/- 0.0078863791
                                B1=     0.033932476 +/- 0.00210078949
                                B2=    0.0002579834 +/- 0.00019368682
                                B3=  -0.00006539032 +/- 0.00000796362
                                B4=   0.00000157104 +/- 0.00000014959
                                B5=  -0.00000001182 +/- 0.00000000105


    tatm model is provided by Ron Maddalena

    >>> tatm(23e9,40)
    298.88517422006998
    >>> tatm(23e9,30)
    289.78060278466995
    >>> tatm(1.42e9,30)
    271.97866556636637

    """

    # where TMPC = ground-level air temperature in C and Freq is in GHz.
    # The A and B coefficients are:
    A = [259.69185966, -1.66599001, 0.226962192,
         -0.0100909636,  0.00018402955, -0.00000119516 ]
    B = [0.42557717,    0.033932476,0.0002579834,
         -0.00006539032, 0.00000157104, -0.00000001182]
    freqGHz = float(freqHz)/1e9
    FREQ  = float(freqGHz)
    FREQ2 = FREQ*FREQ
    FREQ3 = FREQ2*FREQ
    FREQ4 = FREQ3*FREQ
    FREQ5 = FREQ4*FREQ

    TATM = A[0] + A[1]*FREQ + A[2]*FREQ2 +A[3]*FREQ3 + A[4]*FREQ4 + A[5]*FREQ5
    TATM = TATM + (B[0] + B[1]*FREQ + B[2]*FREQ2 + B[3]*FREQ3 + B[4]*FREQ4 + B[5]*FREQ5)*float(tmpC)

    airTempK = TATM
    return airTempK

def corrected_opacity(zenith_opacities,elevation):
    """Compute elevation-corrected opacities.
    
    Keywords:
    zenith_opacities -- opacity based only on time
    elevation -- (float) elevation angle of integration or scan

    """
    n_atmos = natm(elevation)

    corrected_opacities = [math.exp(-xx/n_atmos) for xx in zenith_opacities]

    return corrected_opacities

def zenith_opacity(coeffs, freqs):
    """Interpolate low and high opacities across a vector of frequencies

    Keywords:
    coeffs -- (list) opacitiy coefficients from archived text file, produced by
        GBT weather prediction code
    freqs -- (list) of frequency values in GHz

    Returns:
    A (numpy 1d array) of a zenith opacity at each requested frequency.
    
    """
    # interpolate between the coefficients based on time for a given frequency
    def interpolated_zenith_opacity(f):
        # for frequencies < 2 GHz, return a default zenith opacity
        if np.array(f).mean() < 2:
            result = np.ones(np.array(f).shape)*0.008
            return result
        result=0
        for idx,term in enumerate(coeffs):
            if idx>0: result = result + term*f**idx
            else:
                result=term
        return result

    zenith_opacities = [ interpolated_zenith_opacity(f) for f in freqs ]
    return np.array(zenith_opacities)

def _gain(gain_coeff,elevation):
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

def ta_correction(zenithtau,gain_coeff,spillover,\
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
    
def tsky(ambient_temp,freq,opacity_factors):
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

def masked_array(array):
    """Mask nans in an array
    
    Keywords:
    array -- (numpy nd array)
    
    Returns:
    numpy masked array with nans masked out
    
    """
    return np.ma.masked_array(array,np.isnan(array))
    

def check_for_sdfits_file( infile, sdfitsdir, beginscan, endscan,\
                           refscan1, refscan2, VERBOSE ):
    """Check for the existence of the SDFITS input file.
    
    If the SDFITS input file exists, then use it. Otherwise,
    recreate it from the project directory, if it is provided.
    
    Keywords:
    infile -- an SDFITS file path
    sdfitsdir -- an archive directory path as an alternative to an SDFITS file
    beginscan -- optional begin scan number for filling by sdfits
    endscan -- optional end scan number for filling by sdfits
    refscan1 -- optional reference scan number for filling by sdfits
    refscan2 -- optional reference scan number for filling by sdfits
    VERBOSE -- verbosity level
    
    Returns:
    SDFITS input file path
    
    """
    # if the SDFITS input file doesn't exist, generate it
    if (not os.path.isfile(infile) and os.path.isdir(sdfitsdir)):
        if VERBOSE > 0:
            print "SDFITS input file does not exist; trying to generate it from",\
                  "sdfits-dir input parameter directory and user-provided",\
                  "begin and end scan numbers."

        if not os.path.exists('/opt/local/bin/sdfits'):
            print "ERROR: input sdfits file does not exist and we can not"
            print "    regenerate it using the 'sdfits' filler program in"
            print "    Green Bank. (/opt/local/bin/sdfits).  Exiting"
            sys.exit(2)

        if beginscan and endscan:
            if not beginscan <= endscan:
                print 'ERROR: begin scan is greater than end scan',beginscan,'>',endscan
                sys.exit(9)

        if beginscan or endscan or refscan1 or refscan2:

            scanslist = [beginscan,endscan,refscan1,refscan2]
            while(True):
                try:
                    scanslist.remove(False)
                except(ValueError):
                    break

            minscan = min(scanslist)
            maxscan = max(scanslist)

        if minscan and not maxscan:
            scanrange = '-scans=' + str(minscan) + ': '
        elif maxscan and not minscan:
            scanrange = '-scans=:'+ str(maxscan) + ' '
        elif minscan and maxscan:
            scanrange = '-scans=' + str(minscan) + ':' + str(maxscan) + ' '
        else:
            scanrange = ''

        sdfitsstr = '/opt/local/bin/sdfits -fixbadlags ' + \
                    scanrange + sdfitsdir

        if VERBOSE > 0:
            print sdfitsstr

        os.system(sdfitsstr)
        
        filelist = glob.glob(os.path.basename(sdfitsdir)+'.raw.*fits')
        if 1==len(filelist):
            infile = filelist[0]
        elif len(filelist) > 1:
            print "ERROR: too many possible SDFITS input files for pipeline"
            print "    please check input directory for a single"
            print "    raw fits file with matching index file"
            sys.exit(3)
        else:
            print "ERROR: could not identify an input SDFITS file for the"
            print "    pipeline.  Please check input directory."
            sys.exit(5)

        # if the SDFITS input file exists, then use it to create the map
        if os.path.isfile(infile):
            if VERBOSE > 2:
                print "infile OK"
        else:
            if VERBOSE > 2:
                print "infile not OK"

    return infile

def get_start_mjd(indexfile,verbose=0):
    """Get the start date (mjd) of the session

    Keywords:
    indexfile -- file which contains integrations with time stamps
    verbose -- optional verbosity level

    Returns:
    The session start date (mjd) as an integer
    
    """
    myFile = open(indexfile,'rU')

    # skip over the index file header lines
    while True:
        row = myFile.readline().split()
        if len(row)==40:
            # we just found the column keywords, so read the next line
            row = myFile.readline().split()
            break

    dateobs = row[34]
    start_mjd = dateToMjd(dateobs)
    myFile.close()
    return int(start_mjd)

def get_masks(indexfile,fitsfile=None,samplers=[],verbose=0):
    """Create a mask on the input file for each sampler


    Keywords:
    indexfile -- used to find integrations for each sampler
    fitsfile -- used to get length of table
    samplers -- (list) of samplers which is set when only masks for some
        samplers are desired
    verbose -- optional verbosity on output

    Returns:
    a (dictionary) of the form:
    mask[fits block][sampler name] = boolean mask on block table

    """
    myFile = open(indexfile,'rU')
    table_length = []
    if fitsfile:
        fd = pyfits.open(fitsfile,memmap=1,mode='readonly')

        # one set of masks per FITS extension
        # each set of masks has a mask for each sampler
        mask = []
        for blockid in range(1,len(fd)):
            table_length.append(fd[blockid].header['naxis2'])
            mask.append({})

        fd.close()
    else:
        if not bool(table_length):
            print 'ERROR: either fits file or table size must be provided'
            return False

    # skip over the index file header lines
    while True:
        row = myFile.readline().split()
        if len(row)==40:
            # we just found the column keywords, so read the next line
            row = myFile.readline().split()
            break

    while row:
        
        sampler = row[20]
        ii = int(row[4])
        extension_idx = int(row[3])-1  # FITS extention index, same as blockid +1 (above)

        # if samplers is empty, assume all samplers
        # i.e. not samplers == all samplers
        # if 1 or more sampler is specified, only use those for masks
        if (not samplers) or (sampler in samplers):
            
            # add a mask for a new sampler
            if not sampler in mask[extension_idx]:
                mask[extension_idx][sampler] = np.zeros((table_length[extension_idx]),dtype='bool')

            mask[extension_idx][sampler][ii] = True
            
        # read the next row
        row = myFile.readline().split()

    # print results
    for idx,maskblock in enumerate(mask):
        total = 0
        if verbose: print '-------------------'
        if verbose: print 'EXTENSION',idx+1
        if verbose: print '-------------------'
        for sampler in maskblock:
            total = total + maskblock[sampler].tolist().count(True)
            if verbose: print sampler,maskblock[sampler].tolist().count(True)
        if verbose: print 'total',total
        
    myFile.close()
    
    return mask

def get_maps_and_samplers(allmaps,indexfile,debug=False):
    """Find mapping blocks. Also find samplers used in each map

    Keywords:
    allmaps -- when this flag is set, mapping block discovery is enabled
    indexfile -- input required to search for maps and samplers
    debug -- optional debug flag

    Returns:
    a (list) of map blocks, with each entry a (tuple) of the form:
    (int) reference 1,
    (list of ints) mapscans,
    (int) reference 2,
    samplermap,
        (dictionary) [sampler] = (int)feed, (string)pol, (float)centerfreq
    'PS' -- default representing Position-switched
            this will change to when FS-mode is supported with map discovery
    
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

    samplermap = {}
    while row:

        obsid = row[7]
        scan = int(row[10])
        sampler = row[20]
        feed = int(row[14])
        pol = row[11]
        centerfreq = float(row[29])

        if not scan in scans:
            samplermap = {}

        samplermap[sampler] = (feed,pol,centerfreq)
        scans[scan] = (obsid,samplermap)

        # read the next row
        row = myFile.readline().split()

    myFile.close()

    # print results
    if debug:
        print '------------------------- All scans'
        for scan in scans:
            print 'scan',scan,scans[scan][0]

        print '------------------------- Relavant scans'

    for scan in scans:
        if scans[scan][0].upper()=='MAP' or scans[scan][0].upper()=='OFF':
            map_scans[scan] = scans[scan]

    mapkeys = map_scans.keys()
    mapkeys.sort()

    if debug:
        for scan in mapkeys:
            print 'scan',scan,map_scans[scan][0]

    maps = [] # final list of maps
    ref1 = False
    ref2 = False
    prev_ref2 = False
    mapscans = [] # temporary list of map scans for a single map

    if debug:
        print 'mapkeys', mapkeys

    samplermap = {}

    if not allmaps:
        return scans
        
    for idx,scan in enumerate(mapkeys):

        # look for the offs
        if (map_scans[scan][0]).upper()=='OFF':
            # if there is no ref1 or this is another ref1
            if not ref1 or (ref1 and bool(mapscans)==False):
                ref1 = scan
                samplermap = map_scans[scan][1]
            else:
                ref2 = scan
                prev_ref2 = ref2

        elif (map_scans[scan][0]).upper()=='MAP':
            if not ref1 and prev_ref2:
                ref1 = prev_ref2
        
            mapscans.append(scan)

        # see if this scan is the last one in the relevant scan list
        # or see if we have a ref2
        # if so, close out
        if ref2 or idx==len(mapkeys)-1:
            maps.append((ref1,mapscans,ref2,samplermap,'PS'))
            ref1 = False
            ref2 = False
            mapscans = []
            
    if debug:
        import pprint
        pprint.pprint(maps)

        for idx,mm in enumerate(maps):
            print "Map",idx
            if mm[2]:
                print "\tReference scans.....",mm[0],mm[2]
            else:
                print "\tReference scan......",mm[0]
            print "\tMap scans...........",mm[1]
            print "\tMap type...........",mm[4]

    return maps

def sampler_summary(logger,samplermap):
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

def parserange(rangelist):
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

def is_inclusive_range(rangelist):
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


def commandSummary(logger,opt):
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

def string_to_floats(string_list):
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

def maptype(firstscan,indexfile,debug=False):
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

def gainfactor(logger,opt,samplermap,sampler):
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

def fractional_shift(spectra,delta_f):
    """Returns gain factor set for a given beam and polarization

    Keywords:
    spectra -- (numpy 2d array) of one or more spectra to be shifted
    delta_f -- (float) the channel amount to shift the spectra (< 1)

    Returns:
    (numpy 2d array) of shifted spectra

    """
    N_CHANNELS_start = spectra.shape[-1]
    N_CHANNELS_doubled = N_CHANNELS_start*2

    # double the size of the array
    spectra = np.append(spectra, np.zeros(shape=spectra.shape),axis=1)

    # shift the spectra to the center, with zeros padding either end
    ROLLDISTANCE = N_CHANNELS_start/2
    spectra = np.roll(np.array(spectra),ROLLDISTANCE)

    # pad out spectrum on both sides with end values
    for idx,row in enumerate(spectra):
        spectra[idx][:ROLLDISTANCE] = spectra[idx][ROLLDISTANCE]
        spectra[idx][-ROLLDISTANCE:] = spectra[idx][-ROLLDISTANCE-1]

    # inverse fft of spetrum, 0
    ifft = np.fft.ifft(spectra)
    real = ifft.real
    imag = ifft.imag

    # eqn. 9
    delta_p = 2.0 * np.pi * delta_f / N_CHANNELS_doubled

    # eqn. 7
    amplitude = np.sqrt(real**2 + imag**2)

    # eqn. 8
    phase = np.arctan2(imag,real)

    # eqn. 10
    kk = [np.mod(ii,N_CHANNELS_doubled/2) for ii in range(N_CHANNELS_doubled)]
    kk = np.array(kk,dtype=float)

    ## eqn. 11
    amplitude = amplitude * (1 - (kk/N_CHANNELS_doubled)**2)

    ## eqn. 12
    phase = phase + delta_p * kk

    # eqn. 13
    real = amplitude * np.cos(phase)

    # eqn. 14
    imag = amplitude * np.sin(phase)

    # finally fft to get back to spectra
    shifted = np.fft.fft(real+imag*1j)

    shifted = np.roll(shifted,-ROLLDISTANCE)
    shifted = shifted[:,:N_CHANNELS_start]

    return abs(shifted)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
