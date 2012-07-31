import commandline
from MappingPipeline import MappingPipeline
import sys

if __name__ == '__main__':
    
    # create instance of CommandLine object to parse input
    cl = commandline.CommandLine()
    
    # parse all the input parameters and store them as attributes in param structure
    cl_params = cl.read(sys)

    pipe = MappingPipeline(cl_params)
    
    refSpectrum1 = None
    refTsys1 = None
    refTimestamp1 = None
    refTambient1 = None
    refElevation1 = None
    refSpectrum2 = None
    refTsys2 = None
    refTimestamp2 = None
    refTambient2 = None
    refElevation2 = None

    feed=0
    window=0
    pol=0
    beam_scaling=1

    # -------------- reference 1
    scan=13
    refSpectrum1, refTsys1, refTimestamp1, refTambient1, refElevation1 = \
        pipe.getReference(scan, feed, window, pol)
    
    # -------------- reference 2
    scan=26
    refSpectrum2, refTsys2, refTimestamp2, refTambient2, refElevation2 = \
        pipe.getReference(scan, feed, window, pol)

    # -------------- calibrate signal scans
    mapscans = (14,15,16,17,18,19,20)
    #mapscans = (14,18)
    #mapscans = (14,)
        
    pipe.CalibrateSdfitsIntegrations( mapscans, feed, window, pol, \
            refSpectrum1, refTsys1, refTimestamp1, refTambient1, refElevation1, \
            refSpectrum2, refTsys2, refTimestamp2, refTambient2, refElevation2, \
            beam_scaling, units='ta' )
