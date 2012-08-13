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

import argparse
from Pipeutils import Pipeutils

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

        self.pu = Pipeutils()
        
        self.parser = myparser(fromfile_prefix_chars='@',
            description='Calibrate spectra and create maps from GBT observations.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            epilog="Use @filename.par as a command line parameter to\
            use options from a file.  Any options set on the command\
            line will override whatever is stored in the file.",
            prog='gbtpipeline',
            usage='%(prog)s [options]')
        
        input_group = self.parser.add_argument_group('Input')
        input_group.add_argument("-i", "--infile", dest="infile", default='',
                        help="SDFITS file name containing map scans", metavar="FILE")
        
        data_selection = self.parser.add_argument_group('Data Selection')
        data_selection.add_argument("-m", "--map-scans", dest="mapscans", default=[],
                        help="range of scan numbers", metavar="N[,N]")
        data_selection.add_argument("--refscan1", dest="refscan1", default=False,
                        help="first reference scan", metavar="SCAN", type=int)
        data_selection.add_argument("--refscan2", dest="refscan2", default=False,
                        help="second reference scan", metavar="SCAN", type=int)
        data_selection.add_argument("--allmaps", dest="allmaps", action='store_true',
                        default=False, help="If set, attempt to process all maps in input file.")
        data_selection.add_argument("-c", "--channels",dest="channels", default=False, type=str,
                        help="channel selection i.e. 100:200 (idlToSdfits); use with CAUTION")
        data_selection.add_argument("-f", "--feed",dest="feed", default=[],
                        help="comma-separated feed(s) to process", metavar="F[,F]")
        data_selection.add_argument("-p", "--pol",dest="pol", default=[],
                        help="comma-separated polarization(s) to process", metavar="P[,P]")

        control = self.parser.add_argument_group('Control')
        control.add_argument("--imaging-off", dest="imagingoff", action='store_true',
                        default=False, help="If set, will not create images.")
        control.add_argument("-a", "--average",dest="average", default=0, type=int,
                        help="averge the spectra over N channels (idlToSdfits)", metavar="N")
        control.add_argument("-n", "--idlToSdfits-rms-flag",dest="idlToSdfits_rms_flag", default=False,
                        help="flag integrations with excess noise, see idlToSdfits help",
                        metavar="N")
        control.add_argument("-w", "--idlToSdfits-baseline-subtract",dest="idlToSdfits_baseline_subtract",
                        default=False, help="subtract median-filtered baseline, see idlToSdfits help",
                        metavar="N")
        control.add_argument("--display-idlToSdfits", action='store_true',
                        dest="display_idlToSdfits", default=False,
                        help="will attempt to display idlToSdfits plots")

        calibration = self.parser.add_argument_group('Calibration')
        calibration.add_argument("-u", "--units", dest="units", default='Ta*',
                        help="calibration units")
        calibration.add_argument("--spillover-factor",dest="spillover", default=.99, type=float,
                        help="rear spillover factor (eta-l)", metavar="N")
        calibration.add_argument("--apperture-efficiency",dest="aperture_eff", default=.71, type=float,
                        help="aperture efficiency for freq.=0 (eta-A)", metavar="N")
        calibration.add_argument("--main-beam-efficiency",dest="mainbeam_eff", default=.91, type=float,
                        help="main beam efficiency for freq.=0 (eta-B)", metavar="N")
        calibration.add_argument("--gain-coefficients",dest="gaincoeffs", default=".91,.00434,-5.22e-5",
                        help="comma-separated gain coefficients", metavar="N")
        calibration.add_argument("--gain-factors-left",dest="gain_left", default=[],
                        help="comma-separated gain factors for each left-polarized feed", metavar="G[,G]")
        calibration.add_argument("--gain-factors-right",dest="gain_right", default=[],
                        help="comma-separated gain factors for each right-polarized feed", metavar="G[,G]")
        calibration.add_argument("-t", "--zenith-opacity",dest="zenithtau", type=float,
                        help="zenith opacity value (tau-z)", metavar="N", default=False)

        output = self.parser.add_argument_group('Output')
        output.add_argument("-v", "--verbose", dest="verbose", default=0,
                        help="set the verbosity level-- 0-1:none, "
                             "2:errors only, 3:+warnings, "
                             "4:+user info, 5:+debug", metavar="N", type=int)
        output.add_argument("--clobber", action='store_true',
                        dest="clobber", default=False,
                        help="Overwrites existing output files if set.")

        other = self.parser.add_argument_group('Other')
        other.add_argument("--max-processors",dest="process_max", default=False, type=int,
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
            opt.gain_left = self.pu.string_to_floats(opt.gain_left)
        if opt.gain_right:
            opt.gain_right = self.pu.string_to_floats(opt.gain_right)
        if opt.gaincoeffs:
            opt.gaincoeffs = self.pu.string_to_floats(opt.gaincoeffs)

        return opt
