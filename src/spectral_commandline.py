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
            description='Calibrate spectra from GBT observations.',
            epilog="Use @filename.par as a command line parameter to "
            "use options from a file.  Any options set on the command "
            "line will override whatever is stored in the file.",
            prog='spectralpipe',
            usage='%(prog)s [options]')
        
        input_group = self.parser.add_argument_group('Input')
        input_group.add_argument("-i", "--infile", dest="infilename",
                        default='', required=True,
                        help="SDFITS file name containing scans", type=str)
        
        #data_selection = self.parser.add_argument_group('Data Selection')
        #data_selection.add_argument("-p", "--pol", dest="pol", default=None,
        #                help='polarizations, e.g. "0,1"')
        #data_selection.add_argument("-w", "--window", dest="window",
        #                default=None,
        #                help='spectral windows, e.g. "0,1,2,3"')

        control = self.parser.add_argument_group('Control')
        #control.add_argument("-a", "--average", dest="average", default=0,
        #                type=int,
        #                help='average the spectra over N channels (passed '
        #                'directly to idlToSdfits)')
        control.add_argument("-o", "--order", dest="order", default=3,
                        type=int,
                        help="Order of baseline fit. Default: 3")

        calibration = self.parser.add_argument_group('Calibration')
        #calibration.add_argument("-u", "--units", dest="units", default='tmb',
        #                help="calibration units.  Default: tmb",
        #                choices=['ta', 'ta*', 'tmb', 'jy'],
        #                type=str.lower)
        calibration.add_argument("--spillover-factor", dest="spillover",
                        default=.99, type=float,
                        help="Rear spillover factor (eta_l). Default: .99")
        calibration.add_argument("--aperture-efficiency", dest="aperture_eff",
                        default=.71, type=float,
                        help='Aperture efficiency for spectral window 0.  '
                        'Other window efficiencies are adjusted to this value. '
                        '(eta_A)  Default: .71')
        calibration.add_argument("-t", "--zenith-opacity", dest="zenithtau",
                        type=float, default=.008,
                        help='Zenith opacity value (tau_z).  Default: '
                        'determined from GB weather prediction tools.')

        output = self.parser.add_argument_group('Output')
        #output.add_argument("-v", "--verbose", dest="verbose", default=4,
        #                help="set the verbosity level-- 0-1:none, "
        #                     "2:errors only, 3:+warnings, "
        #                     "4(default):+user info, 5:+debug", type=int)
        output.add_argument("--clobber", action='store_true',
                        dest="clobber", default=False,
                        help="Overwrites existing output files if set.")

    def _parse_range(self, rangelist):
        """Given a range string, produce a list of integers
    
        Inclusive and exclusive integers are both possible.
    
        The range string 1:4,6:8,10 becomes 1,2,3,4,6,7,8,10
        The range string 1:4,-2 becomes 1,3,4
    
        Keywords:
        rangelist -- a range string with inclusive ranges and exclusive integers
    
        Returns:
        a (list) of integers
    
        >>> parserange('1:4,6:8,10')
        ['1', '10', '2', '3', '4', '6', '7', '8']
        >>> parserange('1:4,-2')
        ['1', '3', '4']
    
        """
    
        oklist = set([])
        excludelist = set([])
    
        rangelist = rangelist.replace(' ','')
        rangelist = rangelist.split(',')
    
        # item is single value or range
        for item in rangelist:
            item = item.split(':')
    
            # change to ints
            try:
                int_item = [ int(ii) for ii in item ]
            except(ValueError):
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
    
                    if int_item[0]==int_item[1]:
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
                oklist = [ str(item) for item in oklist ]
                print 'ERROR: excluded item', exitem, 'does not exist in '
                'inclusive range'
                raise

        return sorted(list(oklist))

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
        #try:
        #    if opt.pol:
        #        opt.pol = self._parse_range(opt.pol)
        #
        #    if opt.window:
        #        opt.window = self._parse_range(opt.window)
        #
        #except ValueError:
        #    print 'ERROR: there is a malformed parameter option'
        #    print '   please check your command line settings and try again.'
        #    sys.exit()
        #
        #opt.units = opt.units.lower()
        
        return opt
