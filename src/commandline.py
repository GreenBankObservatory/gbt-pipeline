import argparse

class CommandLine:
    """Interpret command line options
    
    """
    def __init__(self):
        self.parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
            description='Create maps from GBT observations.',)
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
        self.parser.add_option("--no-map-scans-for-scale", action='store_false',
                        dest="mapscansforscale", default=True,
                        help="When set, do not use the mapping scans to scale reference scans to K.")
                        
    def read(self,sys):
        """Read and parse the command line arguments
        
        """
        return self.parser.parse_args()
