#! /usr/bin/env python

import sys
import os
from optparse import OptionParser
import pyfits
import scan_info

usage = "usage: kfpa_pipeline [options]"
parser = OptionParser(usage=usage)
parser.add_option("-i", "--infile", dest="infile", default='0',
                  help="SDFITS file name containing map scans", metavar="FILE")
parser.add_option("-b", "--begin-scan", dest="beginscan", default='0',
                  help="beginning map scan number", metavar="SCAN")
parser.add_option("-e", "--end-scan", dest="endscan", default='0',
                  help="ending map scan number", metavar="SCAN")
parser.add_option("-c", "--vsource-center", dest="vsourcecenter", default='0',
                  help="defines center channel to select (km/sec)", metavar="N")
parser.add_option("-w", "--vsource-width", dest="vsourcewidth", default='0',
                  help="defines median filter width (km/sec)", metavar="N")
parser.add_option("--vsource-begin", dest="vsourcebegin", default='0',
                  help="defines begin channel to select (km/sec)", metavar="N")
parser.add_option("--vsource-end", dest="vsourceend", default='0',
                  help="defines end channel to select (km/sec)", metavar="N")
parser.add_option("-d", "--sdfits-dir", dest="sdfitsdir", default='0',
                  help="SDFITS input directory; used if infile option is not usable",
                  metavar="DIR")
parser.add_option("--refscan1", dest="refscan1", default='-1',
                  help="first reference scan", metavar="SCAN")
parser.add_option("--refscan2", dest="refscan2", default='-1',
                  help="second reference scan", metavar="SCAN")
parser.add_option("--all-scans-as-ref", action='store_const',
                  const='1',dest="allscansref", default='0',
                  help="use all scans as reference?")
parser.add_option("-v", "--verbose", dest="verbose", default='0',
                  help="set the verbosity level", metavar="N")
parser.add_option("--nodisplay", action='store_const', const='1',
                  dest="nodisplay", default='0',
                  help="will not attempt to use the display")

if len(sys.argv) < 2:
    sys.argv.append('-h')

(opt, args) = parser.parse_args()

#infile = check_for_sdfits_file(opt.infile, opt.sdfitsdir, opt.beginscan,\
                               #opt.endscan,opt.refscan1, opt.refscan2,\
                               #opt.verbose)

firstScan = opt.beginscan
lastScan  = opt.endscan
if (opt.verbose > 2):
    print "firstScan",firstScan
    print "lastScan",lastScan

allscans = range(int(firstScan),int(lastScan)+1)

if (opt.verbose > 2):
    print "allscans",allscans

if (opt.refscan1 > -1) and (opt.refscan2 > opt.refscan1):
    refscans = [opt.refscan1,opt.refscan2]
else:
    refscans = [firstScan,lastScan]

if (not opt.allscansref):
    refscans = allscans

if (opt.verbose > 2):
    print "refscans",refscans

# read in the input file
infile = pyfits.open(opt.infile,memmap=1)
sdfitsdata = infile[1].data

scanInfo = scan_info.scan_info(allscans[0],sdfitsdata)

if (opt.verbose > 2):
    print "vSource ",opt.vsourcecenter
    print "vSourceWidth ",opt.vsourcewidth
    print "vSourceBegin ",opt.vsourcebegin
    print "vSourceEnd ",opt.vsourceend
    print "nFeed ",len(scanInfo.n_feeds)
    print "nBand ",scanInfo.n_ifs
    print "nPol ",len(scanInfo.n_polarizations)
    #print "use display ",!g.has_display

sys.exit(9)

#------------------------------------------
#------------------------------------------
#------------------------------------------

for iFeed in range(scanInfo.n_feeds):
    for iBand in range(scanInfo.n_ifs):
        #gettp(refScans[0], int=0, ifnum=iBand)
        calBandRef(allscans, refscans, iBand, iFeed, scanInfo.n_polarizations, wait)
        # selects channels and writes the AIPS compatible data 
        #toaips(!g.s[0],vSource,vSourceWidth,vSourceBegin,vSourceEnd)

sys.exit(0)