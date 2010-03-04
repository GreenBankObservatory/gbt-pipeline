import sys
import os
from optparse import OptionParser

usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-i", "--infile", dest="infile", default='0',
                  help="SDFITS file name containing map scans", metavar="FILE")
parser.add_option("-b", "--begin-scan", dest="beginscan", default='0',
                  help="beginning map scan number", metavar="SCAN")
parser.add_option("-e", "--end-scan", dest="endscan", default='0',
                  help="ending map scan number", metavar="SCAN")
parser.add_option("-c", "--vsource-center", dest="vsourcecenter", default='0',
                  help="defines center channel to select (km/sec)", metavar="")
parser.add_option("-w", "--vsource-width", dest="vsourcewidth", default='0',
                  help="defines median filter width (km/sec)", metavar="")
parser.add_option("--vsource-begin", dest="vsourcebegin", default='0',
                  help="defines begin channel to select (km/sec)", metavar="")
parser.add_option("--vsource-end", dest="vsourceend", default='0',
                  help="defines end channel to select (km/sec)", metavar="")
parser.add_option("-d", "--sdfits-dir", dest="sdfitsdir", default='0',
                  help="SDFITS input directory; used if infile option is not usable", metavar="")
parser.add_option("--refscan1", dest="refscan1", default='-1',
                  help="first reference scan", metavar="SCAN")
parser.add_option("--refscan2", dest="refscan2", default='-1',
                  help="second reference scan", metavar="SCAN")
parser.add_option("-a", "--all-scans-as-ref", dest="allscanref", default='0',
                  help="use all scans as reference?", metavar="0|1")
parser.add_option("-v", "--verbose", dest="verbose", default='0',
                  help="set the verbosity level", metavar="N")

if len(sys.argv) < 2:
    sys.argv.append('-h')

(options, args) = parser.parse_args()

cmdstring = './gbtidl -quiet -e @createMap.pro -args ' + options.infile + ' ' + \
             options.beginscan + ' ' + options.endscan + ' ' + options.vsourcecenter + ' ' + \
             options.vsourcewidth + ' ' + options.vsourcebegin + ' ' + \
             options.vsourceend + ' ' + options.sdfitsdir + ' ' + options.refscan1 + ' ' + \
             options.refscan2 + ' ' + options.allscanref + ' ' + options.verbose

os.system(cmdstring)
