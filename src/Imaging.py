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
import socket


class Imaging:

    def __init__(self,):
        pass

    def run(self, log, terminal, cl_params, mapping_pipelines):

        log.doMessage('INFO', '\n{t.underline}Start imaging.{t.normal}'.format(t=terminal))

        # ------------------------------------------------- identify imaging scripts

        MapStruct = namedtuple("MapStruct", "nchans, window, start, end")

        maps = {}
        for mp in mapping_pipelines:
            nchans = int(mp.mp_object.row_list.get(mp.start, mp.feed, mp.window, mp.pol)['NCHANS'])
            maps[MapStruct(nchans, mp.window, mp.start, mp.end)] = set()

        for mp in mapping_pipelines:
            nchans = int(mp.mp_object.row_list.get(mp.start, mp.feed, mp.window, mp.pol)['NCHANS'])
            maps[MapStruct(nchans, mp.window, mp.start, mp.end)].add(mp.feed)

        log.doMessage('DBG', 'maps', maps)

        for thismap in maps:

            log.doMessage('INFO', 'Imaging window {win} '
                          'for map scans {start}-{stop}'.format(win=thismap.window,
                                                                start=thismap.start,
                                                                stop=thismap.end))

            scanrange = str(thismap.start) + '_' + str(thismap.end)

            imfiles = glob.glob('*' + scanrange + '*window' +
                                str(thismap.window) + '*pol*' + '.fits')

            if not imfiles:
                # no files found
                log.doMessage('ERR', 'No calibrated files found.')
                continue

            # filter file list to only include those with a feed calibrated for use in this map
            feeds = map(str, sorted(maps[thismap]))

            ff = fitsio.FITS(imfiles[0])
            nchans = int([xxx['tdim'] for xxx
                          in ff[1].get_info()['colinfo']
                          if xxx['name'] == 'DATA'][0][0])
            ff.close()
            if cl_params.channels:
                channels = str(cl_params.channels)
            elif nchans:
                chan_min = int(nchans*.02)  # start at 2% of nchan
                chan_max = int(nchans*.98)  # end at 98% of nchans
                channels = str(chan_min) + ':' + str(chan_max)

            infiles = ' '.join(imfiles)

            if cl_params.keeptempfiles:
                keeptempfiles = '1'
            else:
                keeptempfiles = '0'

            # get the source name and restfrequency from an input file
            tabledata = fitsio.read(imfiles[0])
            source = tabledata['OBJECT'][0].strip()
            restfreq = tabledata['RESTFREQ'][0]
            del tabledata

            freq = "_%.0f_MHz" % (restfreq * 1e-6)
            output_basename = source + '_' + scanrange + freq

            if cl_params.average <= 1:
                average = 1
            else:
                average = cl_params.average

            if cl_params.clobber:
                clobber = ' --clobber'
            else:
                clobber = ''

            self.grid(log,
                      channels,
                      str(average),
                      output_basename,
                      str(cl_params.verbose),
                      clobber,
                      infiles)


    def grid(self, log, channels, average, output, verbose, clobber, infiles):
        cmd = ' '.join(('gbtgridder',
                        '--channels', channels,
                        '--average', average,
                        '--output', output,
                        '--verbose', verbose,
                        clobber,
                        infiles))

        p = subprocess.Popen(cmd.split(),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        try:
            print(cmd)
            a_stdout, a_stderr = p.communicate()
        except:
            log.doMessage('ERR', cmd, 'failed.')
            sys.exit()

        log.doMessage('DBG', a_stdout)
        log.doMessage('DBG', a_stderr)
