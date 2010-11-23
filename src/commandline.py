import argparse

class myparser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line):
        arg_line = arg_line.lstrip()
        arg_line = arg_line.split('#')[0]

        if arg_line and arg_line[0] == '#':
            return

        for arg in arg_line.split():
            if not arg.strip():
                continue
            yield arg

class CommandLine:
    """Interpret command line options
    
    """
    def __init__(self):
        self.parser = myparser(fromfile_prefix_chars='@',
            description='Create maps from GBT observations.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,)
        self.parser.add_argument("-i", "--infile", dest="infile", default='',
                        help="SDFITS file name containing map scans", metavar="FILE")
        self.parser.add_argument("-m", "--map-scans", dest="mapscans", default=[],
                        help="range of scan numbers", metavar="N[,N]")
        self.parser.add_argument("--allmaps", dest="allmaps", action='store_true',
                        default=False, help="If set, attempt to process all maps in input file.")
        self.parser.add_argument("--imaging-off", dest="imagingoff", action='store_true',
                        default=False, help="If set, will not create images.")
        self.parser.add_argument("-u", "--units", dest="units", default='Ta*',
                        help="calibration units")                        
        self.parser.add_argument("-d", "--sdfits-dir", dest="sdfitsdir", default='',
                        help="SDFITS input directory; used if infile option is not usable",
                        metavar="DIR")
        self.parser.add_argument("--refscan1", dest="refscan1", default=False,
                        help="first reference scan", metavar="SCAN", type=int)
        self.parser.add_argument("--refscan2", dest="refscan2", default=False,
                        help="second reference scan", metavar="SCAN", type=int)
        self.parser.add_argument("-s", "--sampler",dest="sampler", default=[],
                        help="comma-separated sampler(s) to process", metavar="S[,S]")
        self.parser.add_argument("-f", "--feed",dest="feed", default=[],
                        help="comma-separated feed(s) to process", metavar="F[,F]")
        self.parser.add_argument("-p", "--pol",dest="pol", default=[],
                        help="comma-separated polarization(s) to process", metavar="P[,P]")
        self.parser.add_argument("-a", "--average",dest="average", default=0, type=int,
                        help="averge the spectra over N channels (idlToSdfits)", metavar="N")
        self.parser.add_argument("--spillover-factor",dest="spillover", default=.99, type=float,
                        help="rear spillover factor (eta-l)", metavar="N")
        self.parser.add_argument("--apperture-efficiency",dest="aperture_eff", default=.71, type=float,
                        help="aperture efficiency for freq.=0 (eta-A)", metavar="N")
        self.parser.add_argument("--gain-coefficients",dest="gaincoeffs", default=".91,.00434,-5.22e-5",
                        help="comma-separated gain coefficients", metavar="N")
        self.parser.add_argument("-v", "--verbose", dest="verbose", default=0,
                        help="set the verbosity level-- 0-1:none, "
                             "2:errors only, 3:+warnings, "
                             "4:+user info, 5:+debug", metavar="N", type=int)
        self.parser.add_argument("--nodisplay", action='store_true',
                        dest="nodisplay", default=False,
                        help="will not attempt to use the display")
        self.parser.add_argument("--clobber", action='store_true',
                        dest="clobber", default=False,
                        help="Overwrites existing output files if set.")
        self.parser.add_argument("--no-map-scans-for-scale", action='store_false',
                        dest="mapscansforscale", default=True,
                        help="When set, do not use the mapping scans to scale reference scans to K.")
                        
    def read(self,sys):
        """Read and parse the command line arguments
        
        """

        # if no options are set, print help
        if len(sys.argv) == 1:
            sys.argv.append('-h')

        # make sure parameter file is processed first
        # so that all options on the command line
        # have precedence
        if any(['@' in xx[0] for xx in sys.argv]):
            paridx = [xx[0] for xx in sys.argv].index('@')
            parfile = sys.argv.pop(paridx)
            sys.argv.insert(1,parfile)

        return self.parser.parse_args()