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

import sys
import os
import glob
import subprocess
from collections import namedtuple

class Imaging:

    def __init__(self,):
        pass

    def run(self, log, terminal, cl_params, mapping_pipelines):
        
        log.doMessage('INFO', '\n{t.underline}Start imaging.{t.normal}'.format(t = terminal) )
        
        # ------------------------------------------------- identify imaging scripts
        
        # set the tools directory path
        # and location of the needed scripts and tools
        # if these are not found, turn imaging off
        pipe_dir = os.path.dirname(os.path.abspath(__file__))
        tools_dir = '/'.join((pipe_dir, "tools"))

        load_script = '/convert_and_load.py'
        map_script = '/image.py'

        aipspy = '/'.join((tools_dir, "aipspy"))

        # if the user opted to do imaging, then check for the presence
        # of the necessary imaging scripts (load.py, image.py, aipspy).
        if ((not os.path.isfile(map_script)) or
            (not os.path.isfile(load_script)) or
            (not os.path.isfile(aipspy))):

            log.doMessage('ERR',"Imaging script(s) not found.  Stopping after calibration.")
            sys.exit()

        maps = {}
        MapStruct = namedtuple("MapStruct", "window, start, end")
        for mp in mapping_pipelines:
            maps[MapStruct(mp.window, mp.start, mp.end)] = set()
        for mp in mapping_pipelines:
            maps[MapStruct(mp.window, mp.start, mp.end)].add(mp.feed)

        for thismap in maps:

            aipsinputs = []

            log.doMessage('INFO','Imaging window {win} '
                          'for map scans {start}-{stop}'.format(win = thismap.window,
                                                                start = thismap.start,
                                                                stop = thismap.end))

            scanrange = str(thismap.start) + '_' + str(thismap.end)

            all_imfiles = glob.glob('*' + scanrange + '*window' +
                                str(thismap.window) + '*feed*pol*' + '.fits')

            # filter file list to only include those with a feed calibrated for use in this map
            feeds = map(str, sorted(maps[thismap]))
            imfiles = [] # list of image files filtered for feed
            for feed in feeds:
                for imfile in all_imfiles:
                    if 'feed{0}_'.format(feed) in imfile:
                        imfiles.append(imfile)
            
            ff = fitsio.FITS(imfiles[0])
            nchans = int([xxx['tdim'] for xxx in ff[1].get_info()['colinfo'] if xxx['name']=='DATA'][0][0])
            ff.close()
            if cl_params.channels:
                channels = str(cl_params.channels)
            elif nchans:
                chan_min = int(nchans*.02) # start at 2% of nchan
                chan_max = int(nchans*.98) # end at 98% of nchans
                channels = str(chan_min) + ':' + str(chan_max)

            aips_number = str(os.getuid())
            aipsinfiles = ' '.join(imfiles)

            if cl_params.display_sdfits2aips:
                display_sdfits2aips = '1'
            else:
                display_sdfits2aips = '0'

            if cl_params.sdfits2aips_rms_flag:
                sdfits2aips_rms_flag = str(cl_params.sdfits2aips_rms_flag)
            else:
                sdfits2aips_rms_flag = '0'

            if cl_params.sdfits2aips_baseline_subtract:
                sdfits2aips_baseline_subtract = str(cl_params.sdfits2aips_baseline_subtract)
            else:
                sdfits2aips_baseline_subtract = '0'

            if cl_params.keeptempfiles:
                keeptempfiles = '1'
            else:
                keeptempfiles = '0'

            aips_cmd = ' '.join((aipspy,
                load_script, aips_number, ','.join(feeds),
                str(cl_params.average), channels, display_sdfits2aips,
                sdfits2aips_rms_flag, str(cl_params.verbose),
                sdfits2aips_baseline_subtract, keeptempfiles,
                aipsinfiles))

            log.doMessage('DBG', aips_cmd)

            p = subprocess.Popen(aips_cmd.split(), stdout = subprocess.PIPE,\
                                stderr = subprocess.PIPE)
            try:
                aips_stdout, aips_stderr = p.communicate()
            except: 
                log.doMessage('ERR', aips_cmd,'failed.')
                sys.exit()

            log.doMessage('DBG', aips_stdout)
            log.doMessage('DBG', aips_stderr)
            log.doMessage('INFO','... (step 1 of 2) done')

            # define command to invoke mapping script
            # which in turn invokes AIPS via ParselTongue
            aips_cmd = ' '.join((aipspy, map_script, aips_number,
                                  '-u=_{0}_{1}'.format(str(thismap.start), str(thismap.end))))
            log.doMessage('DBG', aips_cmd)

            p = subprocess.Popen(aips_cmd.split(), stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            aips_stdout, aips_stderr = p.communicate()

            log.doMessage('DBG', aips_stdout)
            log.doMessage('DBG', aips_stderr)
            log.doMessage('INFO','... (step 2 of 2) done')

