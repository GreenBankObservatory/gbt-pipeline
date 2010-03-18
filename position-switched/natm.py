#! /usr/bin/env python

"""Estimate the number of atmospheres along the line of site
   at an input elevation

This comes from a model reported by Ron Maddale

1) A = 1/sin(elev) is a good approximation down to about 15 deg but
starts to get pretty poor below that.  Here's a quick-to-calculate,
better approximation that I determined from multiple years worth of
weather data and which is good down to elev = 1 deg:
 
if (elev LT 39):
   A = -0.023437  + 1.0140 / math.sin( (math.pi/180.)*(elev + 5.1774 /
       (elev + 3.3543) ) )
else:
   A = math.sin(math.pi*elev/180.)

"""

import sys
import math

def natm(elDeg):
    """Compute number of atmospheres at elevation (deg)

    Keyword arguments:
    elDeg -- input elevation in degrees

    Returns:
    nAtmos -- output number of atmospheres

    natm model is provided by Ron Maddalena
    """

    degree = math.pi/180.

    if (elDeg < 39.):
        A = -0.023437 + \
            (1.0140 / math.sin( degree*(elDeg + 5.1774 / (elDeg + 3.3543))))
    else:
        A =1./math.sin(DEGREE*elDeg)

    #print 'Model Number of Atmospheres:', A,' at elevation ',elDeg

    nAtmos = A
    return nAtmos

if __name__ == "__main__":
    outfilename = 'natm.txt'
    natm = natm(sys.argv[1])
    print 'Number of atmospheres:',natm
    print 'Writing value to',outfilename
    outfile = open(outfilename,'w')
    outfile.write(str(natm))
    outfile.close()
    sys.exit(0)
