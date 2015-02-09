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
        
