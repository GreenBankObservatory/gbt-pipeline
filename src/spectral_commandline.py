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
            prog='spectralpipe')
        
        self.parser.add_argument(dest="infilename",
                        default='', 
                        help="SDFITS file name containing scans", type=str)
        
        self.parser.add_argument("--clobber", action='store_true',
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
        
        return opt
