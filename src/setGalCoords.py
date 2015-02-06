
import pyfits
import sys
import os

if len(sys.argv) <= 1:
    print 'Usage: setGalCoords fitsCube1 [fitsCube2 ... fitsCubeN]'
    sys.exit(0)

for fitsCube in sys.argv[1:]:
    if not os.path.exists(fitsCube):
        print '%s does not exist, skipping' % fitsCube
    else:
        pf = pyfits.open(fitsCube,mode='update')
        ctype1 = pf[0].header['ctype1']
        ctype2 = pf[0].header['ctype2']
        if len(ctype1) != 8 or len(ctype2) != 8:
            print 'CTYPE1 or CTYPE2 have an unexpected length, skipping %s' % fitsCube
            pf.close()
            continue

        proj1 = ctype1[4:]
        proj2 = ctype2[4:]
        if proj1 != proj2:
            print 'CTYPE and CTYPE have different projections, skipping %s' % fitsCube
            pf.close()
            continue
        
        if ctype1[:4] == 'GLON' and ctype2[:4] == 'GLAT':
            print 'Coordinates are already galactic, skipping %s' % fitsCube
            pf.close()
            continue
        
        pf[0].header['ctype1'] = 'GLON%s' % proj1
        pf[0].header['ctype2'] = 'GLAT%s' % proj1

        pf.flush()
        pf.close()

        print '%s set' % fitsCube
        
