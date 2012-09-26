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

class Imaging:

    def __init__(self,):
        pass

    def run(self, log, terminal, cl_params, pipes):
        
        log.doMessage('INFO', '\n{t.underline}Start imaging.{t.normal}'.format(t = terminal) )
        
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
        elif RELCONTRIBDIR in sys.path and \
          os.path.isfile(RELCONTRIBDIR + DBCONSCRIPT) and \
          os.path.isfile(RELCONTRIBDIR + MAPSCRIPT):

            dbconScript = RELCONTRIBDIR + DBCONSCRIPT
            mapScript = RELCONTRIBDIR + MAPSCRIPT

        else:
            log.doMessage('ERR',"Imaging script(s) not found.  Stopping after calibration.")
            sys.exit()
            
        windows = set([])
        feeds = set([])
        for pp in pipes:
            mp, window, feed, pol = pp
            windows.add(str(window))
            feeds.add(str(feed))

        scanrange = str(cl_params.mapscans[0])+'_'+str(cl_params.mapscans[-1])

            
        for win in windows:
        
            aipsinputs = []
            
            log.doMessage('INFO','Imaging window {win}'.format(win=win))    
            
            imfiles = glob.glob('*' + scanrange + '*window' + win + '*' + '.fits')
            
            ff = fitsio.FITS(imfiles[0])
            nchans = int([xxx['tdim'] for xxx in ff[1].info['colinfo'] if xxx['name']=='DATA'][0][0])
            ff.close()
            if cl_params.channels:
                channels = str(cl_params.channels)
            elif nchans:
                chan_min = int(nchans*.02) # start at 2% of nchan
                chan_max = int(nchans*.98) # end at 98% of nchans
                channels = str(chan_min) + ':' + str(chan_max)
                
            aipsNumber = str(os.getuid())
            aipsinfiles = ' '.join(imfiles)
            
            if cl_params.display_idlToSdfits:
                display_idlToSdfits = '1'
            else:
                display_idlToSdfits = '0'
                
            if cl_params.idlToSdfits_rms_flag:
                idlToSdfits_rms_flag = str(cl_params.idlToSdfits_rms_flag)
            else:
                idlToSdfits_rms_flag = '0'
            
            if cl_params.idlToSdfits_baseline_subtract:
                idlToSdfits_baseline_subtract = str(cl_params.idlToSdfits_baseline_subtract)
            else:
                idlToSdfits_baseline_subtract = '0'
                
            if cl_params.keeptempfiles:
                keeptempfiles = '1'
            else:
                keeptempfiles = '0'
            
            doimg_cmd = ' '.join(('/home/gbtpipeline/integration/tools/doImage',
                dbconScript, aipsNumber, ','.join(map(str,feeds)),
                str(cl_params.average), channels, display_idlToSdfits,
                idlToSdfits_rms_flag, str(cl_params.verbose),
                idlToSdfits_baseline_subtract, keeptempfiles,
                aipsinfiles))
            
            log.doMessage('DBG', doimg_cmd)

            p = subprocess.Popen(doimg_cmd.split(), stdout = subprocess.PIPE,\
                                stderr = subprocess.PIPE)
            try:
                aips_stdout, aips_stderr = p.communicate()
            except: 
                log.doMessage('ERR', doimg_cmd,'failed.')
                sys.exit()

            log.doMessage('DBG', aips_stdout)
            log.doMessage('DBG', aips_stderr)
            log.doMessage('INFO','... (1/2) done')
            
            # define command to invoke mapping script
            # which in turn invokes AIPS via ParselTongue
            doimg_cmd = ' '.join(('doImage', mapScript, aipsNumber))
            log.doMessage('DBG', doimg_cmd)

            p = subprocess.Popen(doimg_cmd.split(), stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            aips_stdout, aips_stderr = p.communicate()

            log.doMessage('DBG', aips_stdout)
            log.doMessage('DBG', aips_stderr)
            log.doMessage('INFO','... (2/2) done')
     