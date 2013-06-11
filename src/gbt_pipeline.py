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

PARALLEL = True # useful to turn off when debugging

import commandline
from MappingPipeline import MappingPipeline
from SdFitsIO import SdFits
from Imaging import Imaging
from PipeLogging import Logging
from Weather import Weather
from Pipeutils import Pipeutils

from blessings import Terminal
import fitsio

import os
import errno
import multiprocessing
import sys
import glob

def mkdir_p(path):
    """Create a directory if it does not exist

    Keyword arguments:
    path -- the directory name

    """
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise

def calibrate_win_feed_pol(log, cl_params, window, feed, pol, pipe):
    """Calibrate integrations for a single window, feed, polarization.

    Keyword arguments:
    log        -- logging object 
    cl_params  -- command line parameters
    window     -- window number
    feed       -- feed number
    pol        -- polarization number
    pipe       -- mapping pipeline instance from MappingPipeline class

    """
 
    # initialize reference spectrum variables
    refSpectrum1 = None
    refTsys1 = None
    refTimestamp1 = None
    refTambient1 = None
    refElevation1 = None
    refSpectrum2 = None
    refTsys2 = None
    refTimestamp2 = None
    refTambient2 = None
    refElevation2 = None
    refExposure1 = None
    refExposure2 = None
    
    # if we are using reference spectra
    if cl_params.refscans:
        
        # check to see if there are any rows for the first reference scan
        #  note: the row_list.get() call below is normally used to return
        #  a list of rows, but here we are just checking to see if any rows
        #  exist.  If not, row_list.get() will throw an exeption.
        try:
            pipe.row_list.get(cl_params.refscans[0], feed, window, pol)
        except:
            log.doMessage('ERR','missing 2nd reference scan #',
                          cl_params.refscans[0],'for feed', feed,'window', window,
                          'polarization', pol)
            return

        # calibrate the first reference scan.
        #   this involves averaging the reference integrations and computing
        #   a weighted average of the Tsys, timestamp, ambient temperature,
        #   and elevation.
        refSpectrum1, refTsys1, refTimestamp1, refTambient1, refElevation1, refExposure1 = \
            pipe.getReference(cl_params.refscans[0], feed, window, pol)
        
        # check to see if there are any rows for the second reference scan
        #  note: the row_list.get() call below is normally used to return
        #  a list of rows, but here we are just checking to see if any rows
        #  exist.  If not, row_list.get() will throw an exeption.
        if len(cl_params.refscans)>1:
            try:
                pipe.row_list.get(cl_params.refscans[1], feed, window, pol)
            except:
                log.doMessage('ERR', 'missing 2nd reference scan #',
                              cl_params.refscans[1], 'for feed', feed,
                              'window', window, 'polarization', pol)
                return

            # calibrate the first reference scan.
            #  this involves averaging the reference integrations and computing
            #  a weighted average of the Tsys, timestamp, ambient temperature,
            #  and elevation.
            refSpectrum2, refTsys2, refTimestamp2, refTambient2, refElevation2, refExposure2 = \
               pipe.getReference(cl_params.refscans[1], feed, window, pol)

    # calibrate the signal (map) scans
    #   for position-switched calibration, the reference scans will be used.
    #   for frequency-switched calibration, all the ref* parameters are set
    #   to None.
    #  The calibrate_sdfits_integrations() method does not return anything.
    #   It determines the correct calibration path and writes the calibrated
    #   SDFITS output file specific to this feed/window/polarization.
    pipe.calibrate_sdfits_integrations( feed, window, pol,\
            refSpectrum1, refTsys1, refTimestamp1, refTambient1, refElevation1, refExposure1, \
            refSpectrum2, refTsys2, refTimestamp2, refTambient2, refElevation2, refExposure2, \
            cl_params.beamscaling )

def preview_zenith_tau(log, row_list, cl_params, feeds, windows, pols):

    # if using the weather database
    if not cl_params.zenithtau:

        foo = row_list.get(cl_params.mapscans[0], feeds[0], windows[0], pols[0])
        ff = fitsio.FITS(cl_params.infilename)
        extension = foo['EXTENSION']
        row = foo['ROW'][0]
        bar = ff[extension]['OBSFREQ','DATE-OBS'][row]
        dateobs = bar['DATE-OBS'][0]
        obsfreq = bar['OBSFREQ'][0]
        ff.close()
        
        weather = Weather()
        pu = Pipeutils()
           
        mjd = pu.dateToMjd(dateobs)
        zenithtau = weather.retrieve_zenith_opacity(mjd, obsfreq)
        log.doMessage('INFO',
            'Zenith opacity for map: {0:.3f}'.format(zenithtau) )
    
    # else if set at the command line
    else:
    
        log.doMessage('INFO',
            'Zenith opacity for map: {0:.3f}'.format(cl_params.zenithtau) )
        

def calibrate_maps(log, cl_params, row_list, term):
    """Calibrate maps for each window/feed/polarization

       Actual calibration is done in calibrate_win_feed_pol().

       Returns a list of calibrated maps.  Each list item
       is a tuple of (MappingPipe instance, window, feed, pol)

    """
    feeds = cl_params.feed
    pols = cl_params.pol
    windows = cl_params.window
   
    # get a list of all the scans in the input file 
    scanlist = row_list.scans()

    # print some info to the logfile/screen
    if cl_params.refscans:
        log.doMessage('INFO','Refscan(s):', ','.join([str(xx) for xx in cl_params.refscans]) )
    if cl_params.mapscans:
        log.doMessage('INFO','Mapscan(s):', ','.join([str(xx) for xx in cl_params.mapscans]) )
    else:
        log.doMessage('ERR', '{t.bold}ERROR{t.normal}: Need map scan(s).\n'.format(t = term))
        sys.exit()
    
    # make sure there are no map scans specified in the mapscans parameter
    #   that are missing from the scanlist    
    missingscan = False
    for scan in cl_params.mapscans:
        if scan not in scanlist:
            log.doMessage('ERR', 'Scan', scan,'not found.')
            missingscan = True
    if missingscan:
        sys.exit()

    # if feeds, pols and/or windows are not set at the command line then
    #  default to all that are found in the input file
    if not feeds:
        feeds = row_list.feeds()
    if not pols:
        pols = row_list.pols()
    if not windows:
        windows = row_list.windows()
   
    # the zenith tau preview is simply to show the user a zenith opacity 
    #  for the map.  The zenith tau used for calibration is determined
    #  not just once for the whole map, but for every scan.
    if cl_params.units != 'ta': 
        preview_zenith_tau(log, row_list, cl_params, feeds, windows, pols)
    
    # calibrated_maps will contain a list of tuples of
    #  ( MappingPipeline object, window, feed, polarization )
    calibrated_maps = []

    # calibrate one window/feed/pol at a time
    for window in windows:
        maps_for_this_window = []
        for feed in feeds:
            for pol in pols:

                # create MappingPipeline object for this window/feed/pol
                try:
                    mp = MappingPipeline(cl_params, row_list, feed, window, pol, term)
                except KeyError:
                    continue

                # add the MappingPipeline object to a list of feeds and pols
                #  to be calibrated for this window.  That way, when running
                #  parallel processes, only one window will be done at a time.
                #  A group of processes will start for one spectral window, 
                #  then the loop will iterate to a new group of processes
                #  for the next window, and so on.
                maps_for_this_window.append( (mp, window, feed, pol) )

                # add the MappingPipeline object to a list of all the
                #  to be calibrated
                calibrated_maps.append( (mp, window, feed, pol) )
        
        pids = []
        if maps_for_this_window:
            log.doMessage('INFO', '\nCalibrating window {ww}.'.format(ww=window))
            sys.stdout.flush()

            # run the calibration for each feed/pol in this spectral window
            for mp, window, feed, pol in maps_for_this_window:
               
                # pipe output will be printed in order of window
                if PARALLEL:
                    p = multiprocessing.Process(target = calibrate_win_feed_pol,
                          args = (log, cl_params, window, feed, pol, mp, ))
                    pids.append(p)
                else:
                    log.doMessage('DBG', 'Feed {feed} Pol {pol} started.'.format(feed = feed, pol = pol))
                    calibrate_win_feed_pol(log, cl_params, window, feed, pol, mp)
                    log.doMessage('DBG', 'Feed {feed} Pol {pol} finished.'.format(feed = feed, pol = pol))
        
            if PARALLEL:
                for pp in pids:
                    pp.start()
                for mp, window, feed, pol in maps_for_this_window:
                    log.doMessage('DBG', 'Feed {feed} Pol {pol} started.'.format(feed = feed, pol = pol))
                for pp in pids:
                    pp.join()
                for mp, window, feed, pol in maps_for_this_window:
                    log.doMessage('DBG', 'Feed {feed} Pol {pol} finished.'.format(feed = feed, pol = pol))
        # iterate to the next window
 
        return calibrated_maps

def command_summary(cl_params, term, log):
    log.doMessage('INFO','{t.underline}Command summary{t.normal}'.format(t = term))
    for input_param in cl_params._get_kwargs():
        parameter, parameter_value = input_param
        
        if 'zenithtau' == parameter:
            if None == parameter_value:
                if cl_params.units != 'ta':
                    value = 'determined from GB database'
                else:
                    value = 'not applicable to units'
            else:
                value = str(parameter_value)
        elif 'feed' == parameter or 'pol' == parameter or \
             'window' == parameter:
            if None == parameter_value:
                value = 'all'
            else:
                value = ','.join(map(str,parameter_value))
        elif 'imagingoff' == parameter:
            parameter = 'imaging'
            if parameter_value:
                value = 'off'
            else:
                value = 'on'
        elif 'channels' == parameter:
            if False == parameter_value:
                value = 'all'
            else:
                value = str(parameter_value)
        else:
            value = str(parameter_value)
            
        log.doMessage('INFO','\t', parameter,'=', value)

def set_map_scans(cl_params, map_params):
    """Use the information found in find_maps to set refscans.

    """
    if map_params.refscan1:
        cl_params.refscans.append(map_params.refscan1)
    if map_params.refscan2:
        cl_params.refscans.append(map_params.refscan2)
    cl_params.mapscans = map_params.mapscans
    return cl_params

def calibrate_file(term, log, cl_params):
    """Calibrate a single SDFITS file

       Actual calibration is done in calibrate_win_feed_pol(),
       which is called by calibrate_maps().

    """
 
    # Instantiate a SdFits object for I/O and interpreting the
    #  contents of the index file
    sdf = SdFits()

    # generate a name for the index file based on the name of the
    #  raw SDFITS file.  The index file simple has a different extension
    indexfile = sdf.nameIndexFile( cl_params.infilename )
    try:
        # create a structure that lists the raw SDFITS rows for
        #  each scan/window/feed/polarization
        row_list = sdf.parseSdfitsIndex( indexfile )
    except IOError:
        log.doMessage('ERR','Could not open index file', indexfile )
        sys.exit()

    # if there are no mapscans set at the command line, the user
    #  probably wants the pipeline to find maps in the input file
    if not cl_params.mapscans:
        if cl_params.refscans:
            log.doMessage('WARN', 'Referene scan(s) given without map scans, '
            'ignoring reference scan settings.')
        cl_params.refscans = []
         # this is where we try to guess the mapping blocks in the
        #  input file.  A powition-switched mapping block is defined
        #  as a reference scan, followed by mapping scans, optionally
        #  followed by another reference scan.  The returned structure
        #  is a list of tuples of (reference1, mapscans, reference2)
        maps = sdf.find_maps( indexfile )
        
        if maps:
            log.doMessage('INFO','Found', len(maps),'map(s).' )
        else:
            log.doMessage('ERR','No scans specified and found no position-switched maps.')
            sys.exit()

        # calibrate each map found in the input file
        for map_number, map_params in enumerate(maps):
            cl_params = set_map_scans(cl_params, map_params)
            log.doMessage('INFO','Processing map:', str(map_number+1),'of', len(maps) )
            calibrated_maps = calibrate_maps(log, cl_params, row_list, term)
    else:
        # calibrate the map defined by the user
        calibrated_maps = calibrate_maps(log, cl_params, row_list, term)
    
    return calibrated_maps

def runPipeline():

    # the terminal object is used for printing to the screen
    term = Terminal()
    
    # create instance of CommandLine object to parse input, then
    # parse all the input parameters and store them as attributes in 
    # cl_params structure
    cl = commandline.CommandLine()
    cl_params = cl.read(sys)
    
    # create a directory for storing log files    
    mkdir_p('log')
    
    # instantiate a log object for log files and screen output 
    log = Logging(cl_params, 'pipeline')
    
    # print a command summary to log file/terminal
    command_summary(cl_params, term, log)
    
    log.doMessage('INFO','{t.underline}Start calibration.{t.normal}'.format(t = term))
    
    # calibrated_maps will contain a list of tuples each with a MappingPipeline instance,
    #  window id, feed id and polarization id
    calibrated_maps = []

    # check to see if the infile parameter is a directory.  This is the
    # default case for vegas data processing.  If we have a directory of
    # files, we calibrate each input file separately, then perform the 
    # imaging step on all the calibrated outputs.
    if os.path.isdir(cl_params.infilename):
        log.doMessage('INFO', 'Infile name is a directory')
        input_directory = cl_params.infilename
    
        # calibrate one raw SDFITS file at a time 
        for infilename in glob.glob(input_directory + '/' + \
            os.path.basename(input_directory) + '*.fits'):
            log.doMessage('INFO','\nCalibrating', infilename.rstrip('.fits'))
            # change the infilename in the params structure to the
            #  current infile in the directory for each iteration
            cl_params.infilename = infilename
            calibrated_maps_this_file = calibrate_file(term, log, cl_params)
            calibrated_maps.extend(calibrated_maps_this_file)
    else:
            calibrated_maps_this_file = calibrate_file(term, log, cl_params)
            calibrated_maps.extend(calibrated_maps_this_file)

    # if we are doing imaging
    if not cl_params.imagingoff:

        # instantiate an Imaging object
        imag = Imaging()
        # image all the calibrated maps
        imag.run(log, term, cl_params, calibrated_maps)
    
    sys.stdout.write('\n')

if __name__ == '__main__':

    runPipeline()

