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

from PipeLogging import Logging


from blessings import Terminal

import multiprocessing
import sys
import glob
import os
import subprocess

def calibrateWindowFeedPol(log, cl_params, window, feed, pol, pipe):

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
    
    # -------------- reference 1
    if cl_params.refscans:
        
        try:
            pipe.row_list.get(cl_params.refscans[0], feed, window, pol)
        except:
            log.doMessage('ERR','missing 2nd reference scan #',
                          cl_params.refscans[0],'for feed', feed,'window', window,
                          'polarization', pol)
            return
        
        refSpectrum1, refTsys1, refTimestamp1, refTambient1, refElevation1 = \
            pipe.getReference(cl_params.refscans[0], feed, window, pol)
        
        if len(cl_params.refscans)>1:
            # -------------- reference 2
            try:
                pipe.row_list.get(cl_params.refscans[1], feed, window, pol)
            except:
                log.doMessage('ERR', 'missing 2nd reference scan #', cl_params.refscans[1],'for feed', feed,'window', window,'polarization', pol)
                return
            
            refSpectrum2, refTsys2, refTimestamp2, refTambient2, refElevation2 = \
                pipe.getReference(cl_params.refscans[1], feed, window, pol)

    # -------------- calibrate signal scans
    if 1 != cl_params.gainfactors:
        try:
            beam_scaling = cl_params.gainfactors[feed+pol]
        except IndexError:
            log.doMessage('ERR', 'ERORR: can not get a gainfactor for feed and polarization.', feed,'\n  You need to supply a factor for each feed and\n  polarization for the receiver.')
    else:
        beam_scaling = cl_params.gainfactors
    
    pipe.CalibrateSdfitsIntegrations( feed, window, pol,\
            refSpectrum1, refTsys1, refTimestamp1, refTambient1, refElevation1, \
            refSpectrum2, refTsys2, refTimestamp2, refTambient2, refElevation2, \
            beam_scaling )
    
def doImaging(log, terminal, cl_params, pipe):
    
    log.doMessage('INFO', '{t.underline}Start imaging.{t.normal}'.format(t = terminal) )
    
    # ------------------------------------------------- identify imaging scripts
    
    # look in integration or release contrib directories for imaging script
    # if no script is found, turn imaging off
    
    RELCONTRIBDIR = '/home/gbtpipeline/release/contrib'
    TESTCONTRIBDIR = '/home/gbtpipeline/integration/contrib'
    DBCONSCRIPT = '/' + 'dbcon.py'
    MAPSCRIPT = '/' + 'mapDefault.py'
    
    # if the user opted to do imaging, then check for the presence of
    # the necessary imaging scripts (dbcon.py, mapDefault.py). the path
    # to the scripts depends on the version (release vs. test) of the
    # pipeline which is running.
    dbconScript = 'None'
    mapScript = 'None'
    
    
    # test version of pipeline
    if TESTCONTRIBDIR in sys.path and \
      os.path.isfile(TESTCONTRIBDIR + DBCONSCRIPT) and \
      os.path.isfile(TESTCONTRIBDIR + MAPSCRIPT):

        dbconScript = TESTCONTRIBDIR + DBCONSCRIPT
        mapScript = TESTCONTRIBDIR + MAPSCRIPT

    # release version of pipeline
    elif os.path.isfile(RELCONTRIBDIR + DBCONSCRIPT) and \
      os.path.isfile(RELCONTRIBDIR + MAPSCRIPT):

        dbconScript = RELCONTRIBDIR + DBCONSCRIPT
        mapScript = RELCONTRIBDIR + MAPSCRIPT

    else:
        log.doMessage('ERR',"Imaging script(s) not found.  Stopping after calibration.")
        sys.exit()
        
    windows = set([])
    for pp in pipe:
        windows.add(str(pp[1]))
    
    for _window in windows:
        scanrange = str(cl_params.mapscans[0])+'_'+str(cl_params.mapscans[-1])

        aipsinputs = []
        for pp in pipe:
            win = str(pp[1])
            feed = str(pp[2])
            
            imfiles = glob.glob('*' + scanrange + '*window' + win + '_feed' +  feed + '*' + '.fits')
            print 'IMFILE',','.join(imfiles)
            
            # set the idlToSdfits output file name
            aipsinname = '_'.join(imfiles[0].split('_')[:-1])+'.sdf'
            aipsinputs.append(aipsinname)
        
            # run idlToSdfits, which converts calibrated sdfits into a format
            options = ''
        
            if bool(cl_params.average):
                options = options + ' -a ' + str(cl_params.average)
        
            if cl_params.channels:
                options = options + ' -c ' + str(cl_params.channels) + ' '
        
            if not cl_params.display_idlToSdfits:
                options = options + ' -l '
        
            if cl_params.idlToSdfits_rms_flag:
                options = options + ' -n ' + cl_params.idlToSdfits_rms_flag + ' '
                
            if cl_params.verbose > 4:
                options = options + ' -v 2 '
            else:
                options = options + ' -v 0 '
        
            if cl_params.idlToSdfits_baseline_subtract:
                options = options + ' -w ' + cl_params.idlToSdfits_baseline_subtract + ' '
                
            idlcmd = '/home/gbtpipeline/bin/idlToSdfits -o ' + aipsinname + options + ' '.join(imfiles)
            
            log.doMessage('DBG', idlcmd)
            
            os.system(idlcmd)
        
        aipsNumber = str(os.getuid())
        aipsinfiles = ' '.join(aipsinputs)
        doimg_cmd = ' '.join(('/home/gbtpipeline/integration/tools/doImage', dbconScript, aipsNumber, aipsinfiles))
        log.doMessage('DBG', doimg_cmd)

        p = subprocess.Popen(doimg_cmd.split(), stdout = subprocess.PIPE,\
                             stderr = subprocess.PIPE)
        try:
            aips_stdout, aips_stderr = p.communicate()
        except: 
            log.doMessage('ERR', doimg_cmd,'failed.')
            sys.exit()

        log.doMessage('DBG', aips_stdout)
        log.doMessage('ERR', aips_stderr)
        log.doMessage('INFO','... (1/2) done')

        # define command to invoke mapping script
        # which in turn invokes AIPS via ParselTongue
        channel_average = 3
        doimg_cmd = ' '.join(('doImage', mapScript, aipsNumber, str(channel_average)))
        log.doMessage('DBG', doimg_cmd)

        p = subprocess.Popen(doimg_cmd.split(), stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        aips_stdout, aips_stderr = p.communicate()

        log.doMessage('DBG', aips_stdout)
        log.doMessage('DBG', aips_stderr)
        log.doMessage('INFO','... (2/2) done')            
    
def process_map(log, cl_params, row_list):
    
    feeds = cl_params.feed
    pols = cl_params.pol
    windows = cl_params.window
    
    scanlist = row_list.scans()

    if cl_params.refscans:
        log.doMessage('INFO','Refscan(s):', ','.join([str(xx) for xx in cl_params.refscans]) )
    if cl_params.mapscans:
        log.doMessage('INFO','Mapscan(s):', ','.join([str(xx) for xx in cl_params.mapscans]) )
        
    missingscan = False
    for scan in cl_params.mapscans:
        if scan not in scanlist:
            log.doMessage('ERR', 'Scan', scan,'not found.')
            missingscan = True
    if missingscan:
        sys.exit()

    if not feeds:
        feeds = row_list.feeds()
    if not pols:
        pols = row_list.pols()
    if not windows:
        windows = row_list.windows()
    
    log.doMessage('INFO','{t.underline}Start calibration.{t.normal}'.format(t = term))
    
    for window in windows:
        log.doMessage('INFO', 'Window', window,'started')
        sys.stdout.flush()
        pipe = []
        for feed in feeds:
            for pol in pols:
                try:
                    mp = MappingPipeline(log, cl_params, row_list, feed, window, pol, term)
                except KeyError:
                    continue
                pipe.append( (mp, window, feed, pol) )
        
        pids = []
        for idx, pp in enumerate(pipe):
            window = pp[1]
            feed = pp[2]
            pol = pp[3]
           
            # pipe output will be printed in order of window, feed
            if PARALLEL:
                p = multiprocessing.Process(target = calibrateWindowFeedPol, args = (log, cl_params, window, feed, pol, pp[0], ))
                pids.append(p)
    
            else:
                log.doMessage('INFO', 'Feed {feed} Pol {pol} started.'.format(feed = pp[2], pol = pp[3]))
                calibrateWindowFeedPol(log, cl_params, window, feed, pol, pp[0])
                log.doMessage('INFO', 'Feed {feed} Pol {pol} finished.'.format(feed = pp[2], pol = pp[3]))
    
        if PARALLEL:
            for pp in pids:
                pp.start()
            for pp in pipe:
                log.doMessage('INFO', 'Feed {feed} Pol {pol} started.'.format(feed = pp[2], pol = pp[3]))
                
        
            for pp in pids:
                pp.join()
            for pp in pipe:
                log.doMessage('INFO', 'Feed {feed} Pol {pol} finished.'.format(feed = pp[2], pol = pp[3]))
                
    if not cl_params.imagingoff:

        doImaging(log, term, cl_params, pipe)
    

def set_map_scans(cl_params, map_params):
    if map_params.refscan1:
        cl_params.refscans.append(map_params.refscan1)
    if map_params.refscan2:
        cl_params.refscans.append(map_params.refscan2)
    cl_params.mapscans = map_params.mapscans
    return cl_params

def runPipeline(term):

    # create instance of CommandLine object to parse input, then
    # parse all the input parameters and store them as attributes in param structure
    cl = commandline.CommandLine()
    cl_params = cl.read(sys)
    
    
    log = Logging(cl_params, 'pipeline')
    log.doMessage('INFO','{t.underline}Command summary{t.normal}'.format(t = term))
    for x in cl_params._get_kwargs():
        log.doMessage('INFO','\t', x[0],'=', str(x[1]))
    
    sdf = SdFits()
    indexfile = sdf.nameIndexFile( cl_params.infilename )
    try:
        row_list = sdf.parseSdfitsIndex( indexfile )
        maps = sdf.get_maps( indexfile )
    except IOError:
        log.doMessage('ERR','Could not open index file', indexfile )
        sys.exit()

    if not cl_params.mapscans:
        if cl_params.refscans:
            log.doMessage('WARN', 'Refscan(s) given without map scans, ignoring refscan settings.')
        cl_params.refscans = []
        log.doMessage('INFO','Found', len(maps),'map(s).' )
        for map_number, map_params in enumerate(maps):
            cl_params = set_map_scans(cl_params, map_params)
            log.doMessage('INFO','Processing map:', str(map_number),'of', len(maps) )
            process_map(log, cl_params, row_list)
    else:
        process_map(log, cl_params, row_list)
        
if __name__ == '__main__':

    term = Terminal()
    
    # clear the screen
    runPipeline(term)
