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

import fitsio

from Calibration import Calibration
from Pipeutils import Pipeutils
from ObservationRows import ObservationRows

class SdFitsIndexRowReader:
    
    def __init__(self,lookup_table):
        self.lookup = lookup_table
        
    def setrow(self,row):
        self.row = row
    
    def __getitem__(self,key):
        return self.row[self.lookup[key]].lstrip()
        
class SdFits:
    """Class contains methods to read and write to the GBT SdFits format.
    
    This includes code for both the FITS files and associated index files.
    
    A description (but not a definition) of the SD FITS is here:
    https://safe.nrao.edu/wiki/bin/view/Main/SdfitsDetails
    
    """
    
    def __init__(self):
        
        self.pu = Pipeutils()
        
    def check_for_sdfits_file( self, infile, sdfitsdir, beginscan, endscan,\
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
    
  
    def get_start_mjd(self, indexfile,verbose=0):
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
    
    def get_maps(self, indexfile, debug=False):
        """Find mapping blocks. Also find samplers used in each map
    
        Keywords:
        indexfile -- input required to search for maps and samplers
        debug -- optional debug flag
    
        Returns:
        a (list) of map blocks, with each entry a (tuple) of the form:
        (int) reference 1,
        (list of ints) mapscans,
        (int) reference 2
        
        """
    
        myFile = open(indexfile,'rU')
        
        scans = {}
        map_scans = {}
    
        MapParams = namedtuple("MapParams", "refscan1 mapscans refscan2")
        
        # skip over the index file header lines
        while True:
            line = myFile.readline()
            # look for start of row data or EOF (i.e. not line)
            if '[rows]' in line or not line:
                row = myFile.readline().split()
                row = myFile.readline().split()
                break
            
        #import pdb; pdb.set_trace()
        while row:
    
            obsid = row[7]
            scan = int(row[10])
            scans[scan] = (obsid)
    
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
        ref1 = None
        ref2 = None
        prev_ref2 = None
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
            # if so, close out
            if ref2 or idx==len(mapkeys)-1:
                maps.append(MapParams(ref1,mapscans,ref2))
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
    
    def parseSdfitsIndex(self, infile):
        
        try:
            ifile = open(infile)
        except IOError:
            print "ERROR: Could not open file.  Please check and try again."
            raise
        
        observation = ObservationRows()
        
        while True:
            line = ifile.readline()
            # look for start of row data or EOF (i.e. not line)
            if '[rows]' in line or not line:
                break
    
        lookup_table = {}
        header = ifile.readline()
        
        fields = [xx.lstrip() for xx in re.findall(r' *\S+',header)]
        
        iterator = re.finditer(r' *\S+',header)
        for idx,mm in enumerate(iterator):
            lookup_table[fields[idx]] = slice(mm.start(),mm.end())
        
        rr = SdFitsIndexRowReader(lookup_table)
        
        for row in ifile:
        
            rr.setrow(row)
            
            scanid = int(rr['SCAN'])
            feed = int(rr['FDNUM'])
            windowNum = int(rr['IFNUM'])
            pol = int(rr['PLNUM'])
            fitsExtension = int(rr['EXT'])
            rowOfFitsFile = int(rr['ROW'])
            typeOfScan = ''
            
            # we can assume all integrations of a single scan are within the same
            #   FITS extension
            observation.addRow(scanid, feed, windowNum, pol,
                                       fitsExtension, rowOfFitsFile, typeOfScan)
            
        try:
            ifile.close()
        except NameError:
            raise
        
        return observation

    def getReferenceIntegration(self, calON, calOFF):
        
        cal = Calibration()
        calONdata = calON['DATA']
        calOFFdata = calOFF['DATA']
        cref = cal.Cavg(calONdata, calOFFdata)
        ccal = cal.Cdiff(calONdata, calOFFdata)
        tcal = calOFF['TCAL']
        #tref = cal.Tref( tcal, calONdata, calOFFdata )
        tref = cal.idlTsys80( tcal, calONdata, calOFFdata )
        
        dateobs = calOFF['DATE-OBS']
        timestamp = self.pu.dateToMjd(dateobs)
            
        exposure = calON['EXPOSURE'] + calOFF['EXPOSURE']
        tambient = calOFF['TAMBIENT']
        elevation = calOFF['ELEVATIO']
        
        return cref,tref,exposure,timestamp,tambient,elevation

    def nameIndexFile(self, fitsfile):
        # -------------------------------------------------  name index file
        
        if fitsfile.endswith('.fits'):
            return os.path.splitext(fitsfile)[0]+'.index'
        
        else:
            #doMessage(logger,msg.ERR,'input file not recognized as a fits file.',\
            #  ' Please check the file extension and change to \'fits\' if necessary.')
            sys.exit(9)
        