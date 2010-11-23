import math
import os
import subprocess
import sys
import logging
import time

import pyfits
import numpy as np

def timestamp():
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
    logger.setLevel(level)
    
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
    """Convert a FITS date string to Modified Julian Date

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
    
    """
    c = 299792458  # speed of light in m/s
    return (c/f)

def etaA(freqHz):
    """Determine etaA    
    
    Keyword attributes:
    freqHz -- input frequency in Hz

    Returns:
    etaA -- output point source efficiency (range 0 to 1)
    
    """
    freqGHz = float(freqHz)/1e9
    freqScale = 0.0163 * freqGHz
    etaA = float(0.71) * math.exp(-freqScale**2)
    
    return etaA

def etaMB(freqHz):
    """Determine source efficiency

    Keyword attributes:
    freqHz -- input frequency in Hz

    Returns:
    etaA -- output point source efficiency (range 0 to 1)
    etaMB -- output extended source efficiency (range 0 to 1)
             main beam efficiency

    EtaA,MB model is from memo by Jim Condon, provided by Ron Maddalena

    """
    etaMB = float(1.37) * etaA(freqHz)

    return etaMB
    
def gbtbeamsize(hz):
    """Estimate the GBT beam size at a given frequency
    
    Keywords:
    hz -- frequency in Hz
    
    Returns:
    beam size in arc seconds
    
    """
    wavelength = hz2wavelength(hz)
    diameter = 10000 # estimate of telescope diameter in cm
    # return diffraction limit in arc seconds
    return ((1.22*wavelength)/diameter)*206265
   
def interpolate_tsys(tsyss,dates,tt):
    """Interpolate the system temperature along the time axis
    
    Keywords:
    tsyss -- system temps to interpolate from
    dates -- times of each tsys
    tt -- time of current scan
    
    Returns:
    vector of time interpolated system temperatures
    
    """

    return np.interp(tt,dates,tsyss)
    
def interpolate_reference(refs,dates,tskys,tsyss, mjds):
    """Compute time-interpolated reference spectrum, tsky and tsys
    
    Keywords:
    refs -- vector of beginning and ending reference spectra
    dates -- times of each spectr
    tt -- time of current scan
    
    Returns:
    time interpolated spectrum, tsky vector of spectrum and tsys
    
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
            # find the most recent forecast and parse out the coefficients for K-band
            coeffs.append((float(line.split('{{')[0]),\
                [float(xx) for xx in line.split('{{')[2].split('}')[0].split(' ')]))
               
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
    
    """
    n_atmos = natm(elevation)
    corrected_opacities = [math.exp(xx/n_atmos) for xx in zenith_opacities]

    return corrected_opacities

def interpolated_zenith_opacity(coeffs, freqs):
    """
    
    """
    # interpolate between the coefficients based on time for a given frequency
    def zenith_opacity(f):
        result=0
        for idx,term in enumerate(coeffs):
            if idx>0: result = result + term*f**idx
            else:
                result=term
        return result

    zenith_opacities = [ zenith_opacity(f) for f in freqs ]
    return np.array(zenith_opacities)

def _gain(gain_coeff,elevation):
    # comput gain based on elevation, eqn. 12 in PS specification
    gain = 0
    zz = 90. - elevation

    for idx,coeff in enumerate(gain_coeff):
        gain = gain + coeff * zz**idx
        
    return gain

def ta_correction(gain_coeff,spillover,aperture_eff,\
        fbeampol,opacity_coefficients,mjds,elevations,freq,verbose=0):
    """Compute correction to Ta for determining Ta*
    
    Correction is for atmospheric attenuation, rear spillover, ohmic loss
    and blockage efficiency.
    
    Returns:
    Ta correction factor at every frequency for every time and elevation
    
    """
   
    opacities = []
    
    if opacity_coefficients:
        
        for idx,mjd in enumerate(mjds):
            if len(elevations)>1:
                elevation = elevations[idx]
                gain = _gain(gain_coeff,elevation)
                
                # get the correct set of coefficients for this time
                for coeffs_line in opacity_coefficients:
                    if mjd > coeffs_line[0]:
                        coeffs = coeffs_line[1]
                
                zenith_opacities = interpolated_zenith_opacity(coeffs,freq)
                opacities.append(corrected_opacity(zenith_opacities[idx],elevation))
            
            else:
                elevation = elevations[0]
                gain = _gain(gain_coeff,elevation)
                
                # get the correct set of coefficients for this time
                for coeffs_line in opacity_coefficients:
                    if mjd > coeffs_line[0]:
                        coeffs = coeffs_line[1]

                zenith_opacities = interpolated_zenith_opacity(coeffs,freq)
                opacities.append(corrected_opacity(zenith_opacities,elevation))
        
        opacities = np.array(opacities)
        if opacities.ndim == opacities.size:
            opacities = opacities[0]
            
        return (fbeampol * np.array(opacities)) / (spillover * aperture_eff * gain)
        
    else:
    
        return False
    
def tsky(ambient_temp,freq,opacities):
    """Determine the sky temperature contribution at each frequency
    
    Keywords:
    ambient_temp --
    freq -- 
    opacities -- opacities for once time
    
    """
    freq_lo = freq[0]
    freq_hi = freq[-1]

    airTemp_lo = tatm(freq_lo,ambient_temp-273.15)
    airTemp_hi = tatm(freq_hi,ambient_temp-273.15)
    
    tsky_lo = airTemp_lo * (opacities[0]-1)
    tsky_hi = airTemp_hi * (opacities[-1]-1)
    
    nchan = len(freq)
    delta_tsky = (tsky_hi - tsky_lo) / float(nchan)
    
    # interpolate between lo and hi frequency opacities
    tskys = interpolate(freq,np.array([freq_lo,freq_hi]),np.array([tsky_lo,tsky_hi]))
    
    return tskys

def masked_array(array):
    """Mask nans in array
    
    """
    return np.ma.masked_array(array,np.isnan(array))
    

def check_for_sdfits_file( infile, sdfitsdir, beginscan, endscan,\
                           refscan1, refscan2, VERBOSE ):
    """Check for the existence of the SDFITS input file.
    
    If the SDFITS input file exists, then use it. Otherwise,
    recreate it from the project directory, if it is provided.
    
    """
    # if the SDFITS input file doesn't exist, generate it
    if (not os.path.isfile(infile) and os.path.isdir(sdfitsdir) and \
        beginscan < endscan):
        if VERBOSE > 0:
            print "SDFITS input file does not exist; trying to generate it from",\
                  "sdfits-dir input parameter directory and user-provided",\
                  "begin and end scan numbers."

        if not os.path.exists('/opt/local/bin/sdfits'):
            print "ERROR: input sdfits file does not exist and we can not"
            print "    regenerate it using the 'sdfits' filler program in"
            print "    Green Bank. (/opt/local/bin/sdfits).  Exiting"
            sys.exit(2)
            
        if refscan1 < beginscan:
            minscan = refscan1
        else:
            minscan = beginscan

        if refscan2 > endscan:
            maxscan = refscan2
        else:
            maxscan = endscan

        sdfitsstr = '/opt/local/bin/sdfits -fixbadlags -backends=acs' + \
                    ' -scans=' + str(minscan) + ':' + str(maxscan) + ' ' + \
                    sdfitsdir

        if VERBOSE > 0:
            print sdfitsstr

        os.system(sdfitsstr)
        
        infile = os.path.basename(sdfitsdir) + ".raw.acs.fits"

        # if the SDFITS input file exists, then use it to create the map
        if os.path.isfile(infile):
            if VERBOSE > 2:
                print "infile OK"
        else:
            if VERBOSE > 2:
                print "infile not OK"

    return infile

def index_it(indexfile,fitsfile=None,table_length=0,samplers=[],verbose=0):
    
    myFile = open(indexfile,'rU')
    if fitsfile:
        fd = pyfits.open(fitsfile,memmap=1)
        table_length = []
        # one set of masks per FITS extension
        # each set of masks has a mask for each sampler
        mask = []
        for blockid in range(1,len(fd)):
            table_length.append(len(fd[blockid].data))
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
    
def summarize_it(indexfile,debug=False):

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

    while row:
        
        obsid = row[7]
        scan = int(row[10])

        if not scan in scans:
            scans[scan] = obsid
            
        # read the next row
        row = myFile.readline().split()

    myFile.close()

    # print results
    if debug:
        print '------------------------- All scans'
        for scan in scans:
            print 'scan',scan,scans[scan]

        print '------------------------- Relavant scans'

    for scan in scans:
        if scans[scan].upper()=='MAP' or scans[scan].upper()=='OFF':
            map_scans[scan] = scans[scan]

    mapkeys = map_scans.keys()
    mapkeys.sort()

    if debug:
        for scan in mapkeys:
            print 'scan',scan,map_scans[scan]

    maps = [] # final list of maps
    ref1 = False
    ref2 = False
    prev_ref2 = False
    mapscans = [] # temporary list of map scans for a single map

    if debug:
        print 'mapkeys', mapkeys
        
    for idx,scan in enumerate(mapkeys):
        
        # look for the offs
        if (map_scans[scan]).upper()=='OFF':
            # if there is no ref1 or this is another ref1
            if not ref1 or (ref1 and bool(mapscans)==False):
                ref1 = scan
            else:
                ref2 = scan
                prev_ref2 = ref2

        elif (map_scans[scan]).upper()=='MAP':
            if not ref1 and prev_ref2:
                ref1 = prev_ref2
        
            mapscans.append(scan)
        
        # see if this scan is the last one in the relevant scan list
        # or see if we have a ref2
        #    if so, close out    
        if ref2 or idx==len(mapkeys)-1:
            maps.append((ref1,mapscans,ref2))
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

    return maps

def list_samplers(indexfile,debug=False):

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
        #    if so, close out    
        if ref2 or idx==len(mapkeys)-1:
            maps.append((ref1,mapscans,ref2,samplermap))
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

    return maps

def sampler_summary(logger,samplermap):
    """
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
            if int_item[0] < int_item[1]:
                if int_item[0] < 0:
                    print item[0],',',item[1],'must start with a non-negative number'
                    return []

                thisrange = range(int_item[0],int_item[1]+1)
                for ii in thisrange:
                    oklist.add(ii)
            else:
                print item[0],',',item[1],'needs to be in increasing order'
                return []
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
    print oklist
    return sorted(list(oklist))

def is_inclusive_range(rangelist):

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
    """
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
    doMessage(logger,msg.INFO,"disable idlToSdfits display ..",opt.nodisplay)
    doMessage(logger,msg.INFO,"spillover factor (eta_l)......",str(opt.spillover))
    doMessage(logger,msg.INFO,"aperture efficiency (eta_A)...",str(opt.aperture_eff))
    
    if opt.gaincoeffs:
        gaincoeffs = opt.gaincoeffs.split(',')
        opt.gaincoeffs = [ float(xx) for xx in gaincoeffs ]
    pretty_gaincoeffs = map(prettyfloat, gaincoeffs)
    doMessage(logger,msg.INFO,"gain coefficiencts............",str(pretty_gaincoeffs))
    
    doMessage(logger,msg.INFO,"disable mapping ..............",opt.imagingoff)
    doMessage(logger,msg.INFO,"map scans for scale ..........",opt.mapscansforscale)
    if opt.sampler:
        doMessage(logger,msg.INFO,"sampler(s)....................",opt.sampler)
    if opt.feed:
        doMessage(logger,msg.INFO,"feed(s) ......................",opt.feed)
    else:
        doMessage(logger,msg.INFO,"feed(s) ...................... All")
        
    if opt.pol:
        doMessage(logger,msg.INFO,"polarization .................",opt.pol)
    else:
        doMessage(logger,msg.INFO,"polarization ................. All")

    doMessage(logger,msg.INFO,"map scans for scale ..........",opt.mapscansforscale)
    doMessage(logger,msg.INFO,"verbosity level...............",str(opt.verbose))

    doMessage(logger,msg.INFO,"overwrite existing output.....",str(opt.clobber))
