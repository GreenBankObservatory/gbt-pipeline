"""Command line reading methods for the GBT Pipeline.

This module contains the code for reading parameter values from
the gbtpipeline.

"""
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

from settings import *

import argparse


class _MyParser(argparse.ArgumentParser):
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
    """Interpret command line options.

    """
    def __init__(self):

        parser_args = {'fromfile_prefix_chars': '@',
                       'description': 'Calibrate spectra and create maps '
                       'from GBT observations.',
                       'epilog': 'Use @filename.par as a command line '
                       'parameter to use options from a file.  Any options '
                       'set on the command line will override whatever is '
                       'stored in the file.\n'
                       'Pipeline version:  ' + PIPELINE_VERSION,
                       'prog': 'gbtpipeline',
                       'usage': '%(prog)s [options]'}
        self.parser = _MyParser(**parser_args)

        self.parser.add_argument("-V", "--version", action='version',
                                 version='%(prog)s ' + PIPELINE_VERSION,
                                 help="Prints the pipeline version.")

        input_group = self.parser.add_argument_group('Input')
        input_group.add_argument("-i", "--infile", dest="infilename",
                                 default='', required=True,
                                 help='SDFITS file name containing map scans',
                                 type=str)
        data_selection = self.parser.add_argument_group('Data Selection')
        data_selection.add_argument("-m", "--map-scans", dest="mapscans",
                                    default=None,
                                    help='map scans, e.g. "10:20,30:40" '
                                    'identifies two ranges of 11 scans each')
        data_selection.add_argument("--refscan", "--refscans", dest="refscans",
                                    default=None,
                                    help='reference scan(s), e.g. "4,13" to '
                                    'identify two reference scans')
        data_selection.add_argument("-f", "--feed", dest="feed", default=None,
                                    help='feeds, e.g. "0:6" identifies feeds '
                                    '0 through 6')
        data_selection.add_argument("-p", "--pol", dest="pol", default=None,
                                    help='polarizations, e.g. "0,1"')
        data_selection.add_argument("-w", "--window", dest="window",
                                    default=None,
                                    help='spectral windows, e.g. "0,1,2,3"')
        data_selection.add_argument("-c", "--channels", dest="channels",
                                    default=False, type=str,
                                    help='channel selection, e.g. "100:200" '
                                    '(passed to gbtgridder)')

        control = self.parser.add_argument_group('Control')
        control.add_argument("--imaging-off", dest="imagingoff",
                             action='store_true',
                             default=False, help="If set, will calibrate "
                             "data and write calibrated SDFITS files but "
                             "will not create image FITS files.")
        control.add_argument("-a", "--average", dest="average", default=0,
                             type=int,
                             help='average the spectra over N channels '
                             '(passed to gbtgridder)')

        calibration = self.parser.add_argument_group('Calibration')
        calibration.add_argument("-u", "--units", dest="units", default='tmb',
                                 help="calibration units.  Default: tmb",
                                 choices=['ta', 'ta*', 'tmb', 'jy'],
                                 type=str.lower)
        calibration.add_argument("--no-sky-brightness-correction", action='store_false',
                                 dest="tsky", default=True,
                                 help="Disable adjustment for sky brightness.")
        calibration.add_argument("--spillover-factor", dest="spillover",
                                 default=.99, type=float,
                                 help="rear spillover factor (eta_l). "
                                 "Default: .99")
        calibration.add_argument("--aperture-efficiency", dest="aperture_eff",
                                 default=.71, type=float,
                                 help='aperture efficiency for spectral '
                                 'window 0.  Other window efficiencies '
                                 'are adjusted to this value. (eta_A)  '
                                 'Default: .71')
        calibration.add_argument("--main-beam-efficiency", dest="mainbeam_eff",
                                 default=.91, type=float,
                                 help='main beam efficiency for spectral '
                                 'window 0. Other window efficiencies '
                                 'are adjusted to this value. '
                                 '(eta_B)  Default: .91')
        calibration.add_argument("--beam-scaling", dest="beamscaling",
                                 default=1,
                                 help='comma-separated scaling factor '
                                 'applied to each feed and polarization in the '
                                 'order 0L,0R,1L,1R,etc.  This option only applies '
                                 'to KFPA.  All 14 beam scale values required as '
                                 'input.')
        calibration.add_argument("-t", "--zenith-opacity", dest="zenithtau",
                                 type=float, default=None,
                                 help='zenith opacity value (tau_z).  '
                                 'Default: determined from GB weather '
                                 'prediction tools.')
        calibration.add_argument("--smoothing-kernel-size", dest="smoothing_kernel",
                                 type=int, default=3,
                                 help='boxcar kernel size for '
                                 'reference spectrum smoothing. '
                                 'A value <= 1 means no smoothing.  Default: 3')

        output = self.parser.add_argument_group('Output')
        output.add_argument("-v", "--verbose", dest="verbose", default=4,
                            help="set the verbosity level-- 0-1:none, "
                            "2:errors only, 3:+warnings, "
                            "4(default):+user info, 5:+debug", type=int)
        output.add_argument("--clobber", action='store_true',
                            dest="clobber", default=False,
                            help="Overwrites existing output files if set.")
        output.add_argument("--keep-temporary-files", action='store_true',
                            dest='keeptempfiles', default=False,
                            help='If set, do not remove intermediate aips.fits '
                            'imaging files and summary directory.')

    @staticmethod
    def parse_range(rangelist):
        r"""Given a range string, produce a list of integers.

        Inclusive and exclusive integers are both possible.

        The range string 1:4,6:8,10 becomes 1,2,3,4,6,7,8,10.
        The range string 1:4,-2 becomes 1,3,4.

        Args:
            rangelist(string): a range string with inclusive ranges and exclusive integers

        Returns:
            list:
            A list of integers.

        .. testsetup::

           from commandline import CommandLine

        .. doctest:: :hide:

            >>> CommandLine.parse_range('1:4,6:8,10')
            [1, 2, 3, 4, 6, 7, 8, 10]
            >>> CommandLine.parse_range('1:4,-2')
            [1, 3, 4]

        """
        oklist = set([])
        excludelist = set([])

        rangelist = rangelist.replace(' ', '')
        rangelist = rangelist.split(',')

        # item is single value or range
        for item in rangelist:
            item = item.split(':')

            # change to ints
            try:
                int_item = [int(ii) for ii in item]
            except ValueError:
                print repr(':'.join(item)), 'not convertable to integer'
                raise

            if 1 == len(int_item):
                # single inclusive or exclusive item
                if int_item[0] < 0:
                    excludelist.add(abs(int_item[0]))
                else:
                    oklist.add(int_item[0])

            elif 2 == len(int_item):
                # range
                if int_item[0] <= int_item[1]:
                    if int_item[0] < 0:
                        print item[0], ',', item[1], 'must start with a '
                        'non-negative number'
                        return []

                    if int_item[0] == int_item[1]:
                        thisrange = [int_item[0]]
                    else:
                        thisrange = range(int_item[0], int_item[1]+1)

                    for ii in thisrange:
                        oklist.add(ii)
                else:
                    print item[0], ',', item[1], 'needs to be in increasing '
                    'order'
                    raise
            else:
                print item, 'has more than 2 values'

        for exitem in excludelist:
            try:
                oklist.remove(exitem)
            except(KeyError):
                oklist = [str(item) for item in oklist]
                print 'ERROR: excluded item', exitem, 'does not exist in '
                'inclusive range'
                raise

        return sorted(list(oklist))

    def read(self, sys):
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
            sys.argv.insert(1, parfile)

        opt = self.parser.parse_args()

        # transform some parameters to proper types
        try:
            if 1 != opt.beamscaling:
                opt.beamscaling = [float(xx)
                                   for xx
                                   in opt.beamscaling.split(',')]

            if opt.feed:
                opt.feed = self.parse_range(opt.feed)

            if opt.pol:
                opt.pol = self.parse_range(opt.pol)

            if opt.window:
                opt.window = self.parse_range(opt.window)

            if opt.mapscans:
                opt.mapscans = self.parse_range(opt.mapscans)

            if opt.refscans:
                opt.refscans = self.parse_range(opt.refscans)

        except ValueError:
            print 'ERROR: there is a malformed parameter option'
            print '   please check your command line settings and try again.'
            sys.exit()

        opt.units = opt.units.lower()

        return opt
