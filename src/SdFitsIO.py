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

import os
import sys
import re
from collections import namedtuple

from Calibration import Calibration
from Pipeutils import Pipeutils
from ObservationRows import ObservationRows


class SdFitsIndexRowReader:

    def __init__(self, lookup_table):
        self.lookup = lookup_table
        self.row = None

    def setrow(self, row):
        self.row = row

    def __getitem__(self, key):
        try:
            val = self.row[self.lookup[key]].lstrip()
        except KeyError:
            val = ''
        finally:
            return val


class SdFits:
    """Class contains methods to read and write to the GBT SdFits format.

    This includes code for both the FITS files and associated index files.

    A description (but not a definition) of the SD FITS is here:
    https://safe.nrao.edu/wiki/bin/view/Main/SdfitsDetails

    """

    def __init__(self):

        self.pu = Pipeutils()

    def find_maps(self, indexfile, debug=False):
        """Find mapping blocks. Also find samplers used in each map

        Args:
            indexfile: input required to search for maps and samplers
            debug: optional debug flag

        Returns:
        a (list) of map blocks, with each entry a (tuple) of the form:
        (int) reference 1,
        (list of ints) mapscans,
        (int) reference 2

        """

        map_scans = {}
        observation, summary = self.parseSdfitsIndex(indexfile)
        feed = observation.feeds()[0]
        window = observation.windows()[0]
        pol = observation.pols()[0]

        # print results
        if debug:
            print '------------------------- All scans'
            for scanid in sorted(observation.scans()):
                scanstruct = observation.get(scanid, feed, window, pol)
                print('scan \'{0}\' obsid \'{1}\' procname \'{2}\' procscan \'{3}\''.format(scanid,
                                                                                            scanstruct['OBSID'],
                                                                                            scanstruct['PROCNAME'],
                                                                                            scanstruct['PROCSCAN']))

        for scanid in observation.scans():
            scanstruct = observation.get(scanid, feed, window, pol)
            obsid = scanstruct['OBSID'].upper()
            procname = scanstruct['PROCNAME'].upper()
            procscan = scanstruct['PROCSCAN'].upper()

            # keyword check should depend on presence of PROCSCAN key, which is an
            # alternative to checking SDFITVER.
            # OBSID is the old way, PROCSCAN is the new way MR8Q312

            # create a new list that only has 'MAP' and 'OFF' scans
            if not procscan and (obsid == 'MAP' or obsid == 'OFF'):
                map_scans[scanid] = obsid
            elif (procscan == 'MAP' or
                  procname == 'TRACK' or
                  (procname == 'ONOFF' and procscan == 'OFF') or
                  (procname == 'OFFON' and procscan == 'OFF')):
                map_scans[scanid] = procscan

        mapkeys = map_scans.keys()
        mapkeys.sort()

        if debug:
            print '------------------------- Relavant scans'
            for scanid in mapkeys:
                print 'scan', scanid, map_scans[scanid]

        maps = []  # final list of maps
        ref1 = None
        ref2 = None
        prev_ref2 = None
        mapscans = []  # temporary list of map scans for a single map

        if debug:
            print 'mapkeys', mapkeys

        MapParams = namedtuple("MapParams", "refscan1 mapscans refscan2")
        for idx, scan in enumerate(mapkeys):

            # look for the reference scans
            if (map_scans[scan]).upper() == 'OFF' or (map_scans[scan]).upper() == 'ON':
                # if there is no ref1 or this is another ref1
                if not ref1 or (ref1 and bool(mapscans) == False):
                    ref1 = scan
                else:
                    ref2 = scan
                    prev_ref2 = ref2

            elif (map_scans[scan]).upper() == 'MAP':
                if not ref1 and prev_ref2:
                    ref1 = prev_ref2

                mapscans.append(scan)

            # see if this scan is the last one in the relevant scan list
            # or see if we have a ref2
            # if so, close out
            if ref2 or idx == len(mapkeys)-1:
                maps.append(MapParams(ref1, mapscans, ref2))
                ref1 = False
                ref2 = False
                mapscans = []

        if debug:
            import pprint
            pprint.pprint(maps)

            for idx, mm in enumerate(maps):
                print "Map", idx
                if mm.refscan2:
                    print "\tReference scans.....", mm.refscan1, mm.refscan2
                else:
                    print "\tReference scan......", mm.refscan1
                print "\tMap scans...........", mm.mapscans

        return maps

    def parseSdfitsIndex(self, infile, mapscans=[]):

        try:
            ifile = open(infile)
        except IOError:
            print("ERROR: Could not open file: {0}\n"
                  "Please check and try again.".format(infile))
            raise

        observation = ObservationRows()

        while True:
            line = ifile.readline()
            # look for start of row data or EOF (i.e. not line)
            if '[rows]' in line or not line:
                break

        lookup_table = {}
        header = ifile.readline()

        fields = [xx.lstrip() for xx in re.findall(r' *\S+', header)]

        iterator = re.finditer(r' *\S+', header)
        for idx, mm in enumerate(iterator):
            lookup_table[fields[idx]] = slice(mm.start(), mm.end())

        rr = SdFitsIndexRowReader(lookup_table)

        summary = {'WINDOWS': set([]), 'FEEDS': set([])}

        # keep a list of suspect scans so we can know if the
        # user has already been warned
        suspectScans = set()

        for row in ifile:

            rr.setrow(row)

            scanid = int(rr['SCAN'])

            # have a look at the procedure
            #  if it is "Unknown", the data is suspect, so skip it
            procname = rr['PROCEDURE']
            if scanid in suspectScans:
                continue

            if ((scanid not in suspectScans) and procname.lower() == 'unknown'):

                suspectScans.add(scanid)
                if scanid in mapscans:
                    print 'WARNING: scan', scanid, 'has "Unknown" procedure. Skipping.'
                continue

            feed = int(rr['FDNUM'])
            windowNum = int(rr['IFNUM'])
            pol = int(rr['PLNUM'])
            fitsExtension = int(rr['EXT'])
            rowOfFitsFile = int(rr['ROW'])
            obsid = rr['OBSID']
            procscan = rr['PROCSCAN']
            nchans = rr['NUMCHN']

            summary['WINDOWS'].add((windowNum, float(rr['RESTFREQ'])/1e9))
            summary['FEEDS'].add(rr['FDNUM'])

            # we can assume all integrations of a single scan are within the same
            #   FITS extension
            observation.addRow(scanid, feed, windowNum, pol,
                               fitsExtension, rowOfFitsFile, obsid,
                               procname, procscan, nchans)

        try:
            ifile.close()
        except NameError:
            raise

        return observation, summary

    def getReferenceIntegration(self, cal_on, cal_off, scale):

        cal = Calibration()
        cal_ondata = cal_on['DATA']
        cal_offdata = cal_off['DATA']
        cref, exposure = cal.total_power(cal_ondata, cal_offdata, cal_on['EXPOSURE'], cal_off['EXPOSURE'])

        tcal = cal_off['TCAL'] * scale
        tsys = cal.tsys(tcal, cal_ondata, cal_offdata)

        dateobs = cal_off['DATE-OBS']
        timestamp = self.pu.dateToMjd(dateobs)

        tambient = cal_off['TAMBIENT']
        elevation = cal_off['ELEVATIO']

        return cref, tsys, exposure, timestamp, tambient, elevation

    def nameIndexFile(self, pathname):
        # -------------------------------------------------  name index file
        if not os.path.exists(pathname):
            print ('ERROR: Path does not exist {0}.\n'
                   '       Please check and try again'.format(pathname))
            sys.exit(9)

        if os.path.isdir(pathname):
            bn = os.path.basename(pathname.rstrip('/'))
            return '{0}/{1}.index'.format(pathname, bn)

        elif os.path.isfile(pathname) and pathname.endswith('.fits'):
            return os.path.splitext(pathname)[0]+'.index'

        else:
            # doMessage(logger,msg.ERR,'input file not recognized as a fits file.',\
            #  ' Please check the file extension and change to \'fits\' if necessary.')
            print 'ERROR: Input file does not end with .fits:', pathname
            sys.exit(9)
