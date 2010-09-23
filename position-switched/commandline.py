from optparse import OptionParser

class CommandLine:
    def __init__(self):
        self.usage = "usage: gbt_mapping_pipeline [options]"
        self.parser = OptionParser(usage=self.usage)
        self.parser.add_option("-i", "--infile", dest="infile", default='',
                        help="SDFITS file name containing map scans", metavar="FILE")
        self.parser.add_option("-b", "--begin-scan", dest="beginscan", default='0',
                        help="beginning map scan number", metavar="SCAN")
        self.parser.add_option("-e", "--end-scan", dest="endscan", default='0',
                        help="ending map scan number", metavar="SCAN")
        self.parser.add_option("-c", "--vsource-center", dest="vsourcecenter", default='0',
                        help="defines center channel to select (km/sec)", metavar="N")
        self.parser.add_option("-u", "--units", dest="units", default='Ta*',
                        help="calibration units")                        
        self.parser.add_option("-w", "--vsource-width", dest="vsourcewidth", default='0',
                        help="defines median filter width (km/sec)", metavar="N")
        self.parser.add_option("--vsource-begin", dest="vsourcebegin", default='0',
                        help="defines begin channel to select (km/sec)", metavar="N")
        self.parser.add_option("--vsource-end", dest="vsourceend", default='0',
                        help="defines end channel to select (km/sec)", metavar="N")
        self.parser.add_option("-d", "--sdfits-dir", dest="sdfitsdir", default='0',
                        help="SDFITS input directory; used if infile option is not usable",
                        metavar="DIR")
        self.parser.add_option("--refscan1", dest="refscan1", default='-1',
                        help="first reference scan", metavar="SCAN")
        self.parser.add_option("--refscan2", dest="refscan2", default='-1',
                        help="second reference scan", metavar="SCAN")
        self.parser.add_option("--all-scans-as-ref", action='store_const',
                        const='1',dest="allscansref", default='0',
                        help="use all scans as reference?")
        self.parser.add_option("-s", "--sampler",dest="sampler", default=[],
                        help="comma-separated sampler(s) to process")
        self.parser.add_option("-a", "--average",dest="average", default=0, type=int,
                        help="averge the spectra over N channels (idlToSdfits)")
        self.parser.add_option("-v", "--verbose", dest="verbose", default='0',
                        help="set the verbosity level", metavar="N")
        self.parser.add_option("--nodisplay", action='store_true',
                        dest="nodisplay", default=False,
                        help="will not attempt to use the display")

    def read(self,sys):
        if len(sys.argv) < 2: sys.argv.append('-h')
        return self.parser.parse_args()
