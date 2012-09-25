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
        elif RELCONTRIBDIR in sys.path and \
          os.path.isfile(RELCONTRIBDIR + DBCONSCRIPT) and \
          os.path.isfile(RELCONTRIBDIR + MAPSCRIPT):

            dbconScript = RELCONTRIBDIR + DBCONSCRIPT
            mapScript = RELCONTRIBDIR + MAPSCRIPT

        else:
            import pdb; pdb.set_trace()
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
            
            for feed in feeds:

                imfiles = glob.glob('*' + scanrange + '*window' + win + '_feed' +  feed + '*' + '.fits')
                
                # if there are no files matching this window and feed
                if not imfiles:
                    continue
                    
                # set the idlToSdfits output file name
                aipsinname = '_'.join(imfiles[0].split('_')[:-1])+'.sdf'
                aipsinputs.append(aipsinname)
            
                # run idlToSdfits, which converts calibrated sdfits into a format
                options = ''
            
                if bool(cl_params.average):
                    options = options + ' -a ' + str(cl_params.average)
            
                ff = fitsio.FITS(imfiles[0])
                nchans = int([xxx['tdim'] for xxx in ff[1].info['colinfo'] if xxx['name']=='DATA'][0][0])
                ff.close()
                if cl_params.channels:
                    options = options + ' -c ' + str(cl_params.channels) + ' '
                elif nchans:
                    chan_min = int(nchans*.02) # start at 2% of nchan
                    chan_max = int(nchans*.98) # end at 98% of nchans
                    options = options + ' -c ' + str(chan_min) + ':' + str(chan_max) + ' '
            
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
            log.doMessage('DBG', aips_stderr)
            log.doMessage('INFO','... (1/2) done')
            
            if not cl_params.keeptempfiles:
                [os.unlink(xx) for xx in aipsinfiles.split()]
                if os.path.isdir('summary'):
                    [os.unlink('summary/'+xx) for xx in os.listdir('summary')]
                    os.rmdir('summary')

            # define command to invoke mapping script
            # which in turn invokes AIPS via ParselTongue
            doimg_cmd = ' '.join(('doImage', mapScript, aipsNumber))
            log.doMessage('DBG', doimg_cmd)

            p = subprocess.Popen(doimg_cmd.split(), stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            aips_stdout, aips_stderr = p.communicate()

            log.doMessage('DBG', aips_stdout)
            log.doMessage('DBG', aips_stderr)
            log.doMessage('INFO','... (2/2) done')
     