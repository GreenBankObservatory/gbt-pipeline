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

import commandline
from MappingPipeline import MappingPipeline
from SdFitsIO import SdFits
import Imaging
from PipeLogging import Logging
from Weather import Weather
from Pipeutils import Pipeutils
from settings import *

import blessings
import fitsio

import os
import errno
import multiprocessing
import sys
import glob
import copy
from collections import namedtuple


def mkdir_p(path):
    """Create a directory if it does not exist

    Keyword arguments:
    path -- the directory name

    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


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
            log.doMessage('ERR', 'missing reference scan #',
                          cl_params.refscans[0], 'for feed', feed,
                          'window', window, 'polarization', pol)
            return

        # calibrate the first reference scan.
        #   this involves averaging the reference integrations and computing
        #   a weighted average of the Tsys, timestamp, ambient temperature,
        #   and elevation.
        log.doMessage('DBG', 'Calibrating reference scan:', cl_params.refscans[0])
        (refSpectrum1, refTsys1, refTimestamp1,
         refTambient1, refElevation1, refExposure1) = \
            pipe.getReference(cl_params.refscans[0], feed, window, pol, cl_params.beamscaling)

        # check to see if there are any rows for the second reference scan
        #  note: the row_list.get() call below is normally used to return
        #  a list of rows, but here we are just checking to see if any rows
        #  exist.  If not, row_list.get() will throw an exeption.
        if len(cl_params.refscans) > 1:
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
            log.doMessage('DBG', 'Calibrating reference scan:', cl_params.refscans[1])
            (refSpectrum2, refTsys2, refTimestamp2,
             refTambient2, refElevation2,
             refExposure2) = pipe.getReference(cl_params.refscans[1],
                                               feed, window, pol, cl_params.beamscaling)

    # calibrate the signal (map) scans
    #   for position-switched calibration, the reference scans will be used.
    #   for frequency-switched calibration, all the ref* parameters are set
    #   to None.
    #  The calibrate_sdfits_integrations() method does not return anything.
    #   It determines the correct calibration path and writes the calibrated
    #   SDFITS output file specific to this feed/window/polarization.
    pipe.calibrate_sdfits_integrations(feed, window, pol,
                                       refSpectrum1, refTsys1, refTimestamp1,
                                       refTambient1, refElevation1,
                                       refExposure1, refSpectrum2,
                                       refTsys2, refTimestamp2, refTambient2,
                                       refElevation2, refExposure2,
                                       cl_params.beamscaling)


def preview_zenith_tau(log, row_list, cl_params, feeds, windows, pols):

    foo = None

    # if using the weather database
    if cl_params.zenithtau is None:
        for feed in feeds:
            for window in windows:
                for pol in pols:
                    try:
                        foo = row_list.get(cl_params.mapscans[0], feed, window, pol)
                        break  # if we found a row move on, otherwise try another feed/win/pol
                    except KeyError:
                        continue
        if not foo:
            log.doMessage('ERR', 'Could not find scan for zenith opacity preview')
            return

        ff = fitsio.FITS(cl_params.infilename)
        extension = foo['EXTENSION']
        row = foo['ROW'][0]
        bar = ff[extension]['OBSFREQ', 'DATE-OBS'][row]
        dateobs = bar['DATE-OBS'][0]
        obsfreq = bar['OBSFREQ'][0]
        ff.close()

        weather = Weather()
        pu = Pipeutils()

        mjd = pu.dateToMjd(dateobs)
        zenithtau = weather.retrieve_zenith_opacity(mjd, obsfreq, log)
        if zenithtau:
            log.doMessage('INFO',
                          'Approximate zenith opacity for map: {0:.3f}'.format(zenithtau))
        else:
            log.doMessage('ERR', 'Not able to retrieve integration '
                          'zenith opacity for calibration to:', cl_params.units,
                          '\n  Please supply a zenith opacity or calibrate to Ta.')
            sys.exit(9)

    # else if set at the command line
    else:

        log.doMessage('INFO',
                      'Zenith opacity for '
                      'map: {0:.3f}'.format(cl_params.zenithtau))


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
        log.doMessage('INFO', 'Refscan(s):',
                      ','.join([str(xx) for xx in cl_params.refscans]))
    if cl_params.mapscans:
        log.doMessage('INFO', 'Mapscan(s):',
                      ','.join([str(xx) for xx in cl_params.mapscans]))
    else:
        log.doMessage('ERR', '{t.bold}ERROR{t.normal}: '
                      'Need map scan(s).\n'.format(t=term))
        sys.exit()

    # make sure not all map scans specified in the mapscans parameter
    #   are missing from the scanlist
    have_at_least_one_scan = False
    for scan in cl_params.mapscans:
        if scan not in scanlist:
            log.doMessage('DBG', 'Scan', scan, 'not found.')
        else:
            have_at_least_one_scan = True

    if not have_at_least_one_scan:
        log.doMessage('DBG', 'No scans found for this map. Continuing.')
        return None

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
        log.doMessage('DBG', 'Estimating zenith opacity')
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
                    mp = MappingPipeline(cl_params, row_list, feed, window,
                                         pol, term)
                except KeyError:
                    continue

                # add the MappingPipeline object to a list of feeds and pols
                #  to be calibrated for this window.  That way, when running
                #  parallel processes, only one window will be done at a time.
                #  A group of processes will start for one spectral window,
                #  then the loop will iterate to a new group of processes
                #  for the next window, and so on.
                maps_for_this_window.append((mp, window, feed, pol))

                # add the MappingPipeline object to a list of all the
                #  to be calibrated
                CalibratedMap = namedtuple('CalibratedMap', 'mp_object, window, feed, pol, start, end')
                calibrated_maps.append(CalibratedMap(mp, window, feed, pol,
                                                     cl_params.mapscans[0],
                                                     cl_params.mapscans[-1]))

        pids = []
        if maps_for_this_window:
            log.doMessage('INFO', '\nCalibrating window '
                          '{ww}.'.format(ww=window))
            sys.stdout.flush()

            # run the calibration for each feed/pol in this spectral window
            for mp, window, feed, pol in maps_for_this_window:

                # pipe output will be printed in order of window
                if PARALLEL:
                    p = multiprocessing.Process(target=calibrate_win_feed_pol,
                                                args=(log, cl_params, window,
                                                      feed, pol, mp,))
                    pids.append(p)
                else:
                    log.doMessage('DBG', 'Feed {feed} Pol {pol} '
                                  'started.'.format(feed=feed, pol=pol))
                    calibrate_win_feed_pol(log, cl_params, window, feed, pol,
                                           mp)
                    log.doMessage('DBG', 'Feed {feed} Pol {pol} '
                                  'finished.'.format(feed=feed, pol=pol))

            if PARALLEL:
                for pp in pids:
                    pp.start()
                for mp, window, feed, pol in maps_for_this_window:
                    log.doMessage('DBG', 'Feed {feed} Pol {pol} '
                                  'started.'.format(feed=feed, pol=pol))
                for pp in pids:
                    pp.join()
                for mp, window, feed, pol in maps_for_this_window:
                    log.doMessage('DBG', 'Feed {feed} Pol {pol} '
                                  'finished.'.format(feed=feed, pol=pol))

    # iterate to the next window
    return calibrated_maps


def command_summary(cl_params, term, log):
    log.doMessage('INFO', '{t.underline}Command '
                  'summary{t.normal}'.format(t=term))
    for input_param in cl_params._get_kwargs():
        parameter, parameter_value = input_param

        if 'zenithtau' == parameter:
            if parameter_value is None:
                if cl_params.units != 'ta':
                    value = 'determined from GB database'
                else:
                    value = 'not applicable to units'
            else:
                value = str(parameter_value)
        elif ('feed' == parameter or
              'pol' == parameter or
              'window' == parameter):
            if parameter_value is None:
                value = 'all'
            else:
                value = ','.join(map(str, parameter_value))
        elif 'imagingoff' == parameter:
            parameter = 'imaging'
            if parameter_value:
                value = 'off'
            else:
                value = 'on'
        elif 'channels' == parameter:
            if parameter_value is False:
                value = 'all'
            else:
                value = str(parameter_value)
        else:
            value = str(parameter_value)

        log.doMessage('INFO', '\t', parameter, '=', value)


def set_map_scans(cl_params, map_params):
    """Use the information found in find_maps to set refscans.

    """
    cl_params.refscans = []
    if map_params.refscan1:
        cl_params.refscans.append(map_params.refscan1)
    if map_params.refscan2:
        cl_params.refscans.append(map_params.refscan2)
    cl_params.mapscans = map_params.mapscans
    return cl_params


def calibrate_file(term, log, command_options):
    """Calibrate a single SDFITS file

       Actual calibration is done in calibrate_win_feed_pol(),
       which is called by calibrate_maps().

    """

    # Instantiate a SdFits object for I/O and interpreting the
    #  contents of the index file
    sdf = SdFits()

    # generate a name for the index file based on the name of the
    #  raw SDFITS file.  The index file simply has a different extension
    indexfile = sdf.nameIndexFile(command_options.infilename)
    try:
        # create a structure that lists the raw SDFITS rows for
        #  each scan/window/feed/polarization
        row_list, summary = sdf.parseSdfitsIndex(indexfile, command_options.mapscans)
    except IOError:
        log.doMessage('ERR', 'Could not open index file', indexfile)
        sys.exit()

    log.doMessage('INFO', indexfile)
    log.doMessage('INFO', '    ', len(summary['WINDOWS']), 'spectral window(s)')
    for (win, freq) in sorted(summary['WINDOWS']):
        log.doMessage('INFO', '       {win}: {freq:.4f} GHz'.format(win=win, freq=freq))
    log.doMessage('INFO', '    ', len(summary['FEEDS']), 'feed(s):', ', '.join(sorted(summary['FEEDS'])))

    proceed_with_calibration = True

    # check for presence of pol(s) in dataset before attempting calibration
    if command_options.pol:
        if set(command_options.pol).isdisjoint(set(row_list.pols())):
            log.doMessage('WARN', 'POL', command_options.pol, 'not in', os.path.basename(indexfile))
            proceed_with_calibration = False
        else:
            requested_pols = command_options.pol
            command_options.pol = list(set(command_options.pol).intersection(set(row_list.pols())))
            pol_diff = set(requested_pols).difference(set(command_options.pol))
            if pol_diff:
                log.doMessage('WARN', 'POL', list(pol_diff), 'not in', os.path.basename(indexfile))

    # check for presence of feed(s) in dataset before attempting calibration
    if command_options.feed:
        if set(command_options.feed).isdisjoint(set(row_list.feeds())):
            log.doMessage('WARN', 'FEED', command_options.feed, 'not in', os.path.basename(indexfile))
            proceed_with_calibration = False
        else:
            requested_feeds = command_options.feed
            command_options.feed = list(set(command_options.feed).intersection(set(row_list.feeds())))
            feed_diff = set(requested_feeds).difference(set(command_options.feed))
            if feed_diff:
                log.doMessage('WARN', 'FEED', list(feed_diff), 'not in', os.path.basename(indexfile))

    # check for presence of window(s) in dataset before attempting calibration
    if command_options.window:
        if set(command_options.window).isdisjoint(set(row_list.windows())):
            log.doMessage('DBG', 'WINDOW', command_options.window, 'not in', os.path.basename(indexfile))
            proceed_with_calibration = False
        else:
            requested_windows = command_options.window
            command_options.window = list(set(command_options.window).intersection(set(row_list.windows())))
            window_diff = set(requested_windows).difference(set(command_options.window))
            if window_diff:
                log.doMessage('DBG', 'WINDOW', list(window_diff), 'not in', os.path.basename(indexfile))

    if proceed_with_calibration is False:
        return None

    calibrated_maps = []
    # if there are no mapscans set at the command line, the user
    #  probably wants the pipeline to find maps in the input file
    if not command_options.mapscans:
        if command_options.refscans:
            log.doMessage('WARN', 'Referene scan(s) given without map scans, '
                          'ignoring reference scan settings.')
        command_options.refscans = []
        # this is where we try to guess the mapping blocks in the
        #  input file.  A powition-switched mapping block is defined
        #  as a reference scan, followed by mapping scans, optionally
        #  followed by another reference scan.  The returned structure
        #  is a list of tuples of (reference1, mapscans, reference2)
        maps = sdf.find_maps(indexfile)

        if maps:
            log.doMessage('INFO', 'Found', len(maps), 'map(s).')
        else:
            log.doMessage('ERR', 'No scans specified and found no '
                          'position-switched maps.')
            sys.exit()

        # calibrate each map found in the input file
        for map_number, map_params in enumerate(maps):
            cmd_options = set_map_scans(command_options, map_params)
            log.doMessage('INFO', '\nProcessing map:', str(map_number+1), 'of',
                          len(maps))
            calibrated_maps.append(calibrate_maps(log, cmd_options, row_list, term))
    else:
        # calibrate the map defined by the user
        calibrated_maps.append(calibrate_maps(log, command_options, row_list, term))

    return calibrated_maps


def runPipeline():

    # the blessings.Terminal object is used for printing to the screen
    terminal = blessings.Terminal()
    term = terminal

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

    if not cl_params.imagingoff:

        # instantiate an Imaging object
        imag = Imaging.Imaging()

    else:
        imag = None

    log.doMessage('INFO', '{t.underline}Start '
                  'calibration.{t.normal}'.format(t=term))

    # calibrated_maps will contain a list of tuples each with a
    # MappingPipeline instance, window id, feed id and polarization id
    calibrated_maps = []

    # check to see if the infile parameter is a directory.  This is the
    # default case for vegas data processing.  If we have a directory of
    # files, we calibrate each input file separately, then perform the
    # imaging step on all the calibrated outputs.
    if os.path.isdir(cl_params.infilename):
        log.doMessage('INFO', 'Infile name is a directory')
        input_directory = cl_params.infilename

        # Instantiate a SdFits object for I/O and interpreting the
        #  contents of the index file
        sdf = SdFits()

        # generate a name for the index file based on the name of the
        #  raw SDFITS file.  The index file simply has a different extension
        directory_name = os.path.basename(cl_params.infilename.rstrip('/'))
        indexfile = cl_params.infilename + '/' + directory_name + '.index'
        try:
            # create a structure that lists the raw SDFITS rows for
            #  each scan/window/feed/polarization
            row_list, summary = sdf.parseSdfitsIndex(indexfile, cl_params.mapscans)
        except IOError:
            log.doMessage('ERR', 'Could not open index file', indexfile)
            sys.exit()

        quitcal = False
        if cl_params.window and set(cl_params.window).isdisjoint(set(row_list.windows())):
            log.doMessage('ERR', 'no given WINDOW(S)', cl_params.window, 'in dataset')
            quitcal = True
        if cl_params.feed and set(cl_params.feed).isdisjoint(set(row_list.feeds())):
            log.doMessage('ERR', 'no given FEED(S)', cl_params.feed, 'in dataset')
            quitcal = True
        if cl_params.pol and set(cl_params.pol).isdisjoint(set(row_list.pols())):
            log.doMessage('ERR', 'no given POL(S)', cl_params.pol, 'in dataset')
            quitcal = True
        if cl_params.mapscans and set(cl_params.mapscans).isdisjoint(set(row_list.scans())):
            log.doMessage('ERR', 'no given MAPSCAN(S)', cl_params.mapscans, 'in dataset')
            quitcal = True
        if cl_params.refscans and set(cl_params.refscans).isdisjoint(set(row_list.scans())):
            log.doMessage('ERR', 'no given REFSCAN(S)', cl_params.refscans, 'in dataset')
            quitcal = True

        if quitcal:
            sys.exit(12)

        # calibrate one raw SDFITS file at a time
        for infilename in glob.glob(input_directory + '/' +
                                    os.path.basename(input_directory) +
                                    '*.fits'):
            log.doMessage('DBG', 'Attempting to calibrate', os.path.basename(infilename).rstrip('.fits'))
            # change the infilename in the params structure to the
            #  current infile in the directory for each iteration
            cl_params.infilename = infilename

            # copy the cl_params structure so we can modify it during calibration
            # for each seperate file.
            commandline_options = copy.deepcopy(cl_params)
            calibrated_maps_this_file = calibrate_file(term, log, commandline_options)
            if calibrated_maps_this_file:
                calibrated_maps.extend(calibrated_maps_this_file)
    else:
        commandline_options = copy.deepcopy(cl_params)
        calibrated_maps_this_file = calibrate_file(term, log, commandline_options)
        if calibrated_maps_this_file:
            calibrated_maps.extend(calibrated_maps_this_file)

    if not calibrated_maps:
        log.doMessage('ERR', 'No calibrated spectra.  Check inputs and try again')
        sys.exit(-1)

    # if we are doing imaging
    if not cl_params.imagingoff:

        # image all the calibrated maps
        import itertools
        calibrated_maps = list(itertools.chain(*calibrated_maps))

        imag.run(log, term, cl_params, calibrated_maps)

    sys.stdout.write('\n')

if __name__ == '__main__':

    runPipeline()
