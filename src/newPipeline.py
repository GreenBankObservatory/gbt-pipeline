from MappingPipeline import MappingPipeline

if __name__ == '__main__':
    
    FILENAME = '/media/980d0181-4160-4bbf-8c3d-3d370f24fefd/data/TKFPA_29/TKFPA_29.raw.acs.'
    
    pipe = MappingPipeline(FILENAME)
    
    refSpectrum1 = None
    refTsys1 = None
    refTimestamp1 = None
    refSpectrum2 = None
    refTsys2 = None
    refTimestamp2 = None

    feed=0
    window=0
    pol=0

    # -------------- reference 1
    scan=13
    refSpectrum1, refTsys1, refTimestamp1 = pipe.getReference(scan, feed, window, pol)
    
    # -------------- reference 2
    scan=26
    refSpectrum2, refTsys2, refTimestamp2 = pipe.getReference(scan, feed, window, pol)

    # -------------- calibrate signal scans
    for scan in (14,15,16,17,18,19,20):
        pipe.CalibrateSdfitsScan( scan, feed, window, pol, \
               refSpectrum1, refTimestamp1, refTsys1, \
               refSpectrum2, refTimestamp2, refTsys2, units='ta*' )
