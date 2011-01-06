import argparse
import pipeutils

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
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            epilog="Use @filename.par as a command line parameter to\
            use options from a file.  Any options set on the command\
            line will override whatever is stored in the file.",)
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
        self.parser.add_argument("-f", "--feed",dest="feed", default=[],
                        help="comma-separated feed(s) to process", metavar="F[,F]")
        self.parser.add_argument("-p", "--pol",dest="pol", default=[],
                        help="comma-separated polarization(s) to process", metavar="P[,P]")
        self.parser.add_argument("-a", "--average",dest="average", default=0, type=int,
                        help="averge the spectra over N channels (idlToSdfits)", metavar="N")
        self.parser.add_argument("-n", "--idlToSdfits-rms-flag",dest="idlToSdfits_rms_flag", default=False,
                        help="flag integrations with excess noise, see idlToSdfits help",
                        metavar="N")
        self.parser.add_argument("-w", "--idlToSdfits-baseline-subtract",dest="idlToSdfits_baseline_subtract",
                        default=False, help="subtract median-filtered baseline, see idlToSdfits help",
                        metavar="N")
        self.parser.add_argument("--display-idlToSdfits", action='store_true',
                        dest="display_idlToSdfits", default=False,
                        help="will attempt to display idlToSdfits plots")
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
        self.parser.add_argument("--clobber", action='store_true',
                        dest="clobber", default=False,
                        help="Overwrites existing output files if set.")
        self.parser.add_argument("--map-scans-for-scale", action='store_true',
                        dest="mapscansforscale", default=False,
                        help="When set, use the mapping scans to scale map Tsys's to K.")
        self.parser.add_argument("--gain-factors-left",dest="gain_left", default=[],
                        help="comma-separated gain factors for each left-polarized feed", metavar="G[,G]")
        self.parser.add_argument("--gain-factors-right",dest="gain_right", default=[],
                        help="comma-separated gain factors for each right-polarized feed", metavar="G[,G]")
        self.parser.add_argument("--max-processors",dest="process_max", default=False, type=int,
                        help="optional max number of processors, to reduce resource usage", metavar="N")

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

        opt = self.parser.parse_args()

        # transform some parameters to proper types
        if opt.gain_left:
            opt.gain_left = pipeutils.string_to_floats(opt.gain_left)
        if opt.gain_right:
            opt.gain_right = pipeutils.string_to_floats(opt.gain_right)
        if opt.gaincoeffs:
            opt.gaincoeffs = pipeutils.string_to_floats(opt.gaincoeffs)

        return opt
