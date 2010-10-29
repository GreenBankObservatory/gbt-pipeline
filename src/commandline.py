from optparse import OptionParser

class CommandLine:
    """Interpret command line options
    
    """
    def __init__(self):
        self.usage = "usage: gbtpipeline [options]"
        self.parser = OptionParser(usage=self.usage)
        self.parser.add_option("-i", "--infile", dest="infile", default='',
                        help="SDFITS file name containing map scans", metavar="FILE")
        self.parser.add_option("-b", "--begin-scan", dest="beginscan", default='0',
                        help="beginning map scan number", metavar="SCAN")
        self.parser.add_option("-e", "--end-scan", dest="endscan", default='0',
                        help="ending map scan number", metavar="SCAN")
        self.parser.add_option("--allmaps", dest="allmaps", action='store_true',
                        default=False, help="If set, attempt to process all maps in input file.")
        self.parser.add_option("--imaging-off", dest="imagingoff", action='store_true',
                        default=False, help="If set, will not create images.")
        self.parser.add_option("-u", "--units", dest="units", default='Ta*',
                        help="calibration units")                        
        self.parser.add_option("-d", "--sdfits-dir", dest="sdfitsdir", default='0',
                        help="SDFITS input directory; used if infile option is not usable",
                        metavar="DIR")
        self.parser.add_option("--refscan1", dest="refscan1", default='-1',
                        help="first reference scan", metavar="SCAN")
        self.parser.add_option("--refscan2", dest="refscan2", default='-1',
                        help="second reference scan", metavar="SCAN")
        self.parser.add_option("-s", "--sampler",dest="sampler", default=[],
                        help="comma-separated sampler(s) to process", metavar="SAMPLER,SAMPLER")
        self.parser.add_option("-a", "--average",dest="average", default=0, type=int,
                        help="averge the spectra over N channels (idlToSdfits)", metavar="N")
        self.parser.add_option("--spillover-factor",dest="spillover", default=.99, type=float,
                        help="rear spillover factor (eta-l)", metavar="N")
        self.parser.add_option("--apperture-efficiency",dest="aperture_eff", default=.71, type=float,
                        help="aperture efficiency for freq.=0 (eta-A)", metavar="N")
        self.parser.add_option("--gain-coefficients",dest="gaincoeffs", default=".91,.00434,-5.22e-5",
                        help="comma-separated gain coefficients", metavar="N")
        self.parser.add_option("-v", "--verbose", dest="verbose", default='0',
                        help="set the verbosity level", metavar="N")
        self.parser.add_option("--nodisplay", action='store_true',
                        dest="nodisplay", default=False,
                        help="will not attempt to use the display")
        self.parser.add_option("--clobber", action='store_true',
                        dest="clobber", default=False,
                        help="Overwrites existing output files if set.")
        #self.parser.add_option("-c", "--vsource-center", dest="vsourcecenter", default='0',
                        #help="defines center channel to select (km/sec)", metavar="N")
        #self.parser.add_option("-w", "--vsource-width", dest="vsourcewidth", default='0',
                        #help="defines median filter width (km/sec)", metavar="N")
        #self.parser.add_option("--vsource-begin", dest="vsourcebegin", default='0',
                        #help="defines begin channel to select (km/sec)", metavar="N")
        #self.parser.add_option("--vsource-end", dest="vsourceend", default='0',
                        #help="defines end channel to select (km/sec)", metavar="N")
        #self.parser.add_option("--mainbeam-efficiency",dest="mainbeam_eff", default=.97, type=float,
                        #help="main beam efficiency for freq.=0  (eta-B)")
                        
    def read(self,sys):
        """Read and parse the command line arguments
        
        """
        if len(sys.argv) < 2: sys.argv.append('-h')
        return self.parser.parse_args()
