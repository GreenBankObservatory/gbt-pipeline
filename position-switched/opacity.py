""" Module to estimate the opacity correction factor 

   fourVelocity takes an input start index, 
    and assume the x and y ranges have already been set

"""

import sys
import math
import natm
def opacity(zenithTau,elDeg):
    """Estimate the opacity correction factor 

    Keyword arguments:
    zenithTau -- the zenith tau factor
    elDeg -- optional source elDeg (degrees)

    Returns:
    opacityFactor -- scale factor (> 1) atmosphere

    """

    opacityFactor = 1.
    if (float(zenithTau) < 0.):
        print 'Illegal zenithTau:',float(zenithTau)
        return

    nAtmos = natm.natm(float(elDeg)) #  get number of atmospheres at el
    opacityFactor = math.exp(float(zenithTau)*nAtmos)
    return opacityFactor

if __name__ == "__main__":
    of = opacity(sys.argv[1],sys.argv[1])
    outfile = open("of.txt",'w')
    outfile.write(str(of))
    outfile.close()
    sys.exit(0)
