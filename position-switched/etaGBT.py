"""Compute the GBT efficiencies, etaA and etaB for a given frequency

   The model is based on a memo by Jim Condon, provided by
   Ron Maddalena

"""

import sys
import math

def etaGBT(freqMHz):
    """Determine source efficiency

    Keyword attributes:
    freqMHz -- input frequency in MHz

    Returns:
    etaA -- output point source efficiency (range 0 to 1)
    etaB -- output extended source efficiency (range 0 to 1)

    EtaA,B model is from memo by Jim Condon, provided by Ron Maddalena

    """

    freqGHz = float(freqMHz)*0.001
    freqScale = 0.0163 * freqGHz
    etaA = float(0.71) * math.exp(-freqScale**2)
    etaB = float(1.37) * etaA

    #if (doPrint > 0.):
        #print freqGHz,'(GHz) -> eta A, B:',etaA,etaB

    return etaA,etaB

if __name__ == "__main__":
    # write Modified Julian Date to a file named 'mjd.txt'
    # then, in IDL open file with time and read value into a variable
    etaA,etaB = etaGBT(sys.argv[1])
    outfile = open("eta.txt",'w')
    outfile.write(str(etaA)+','+str(etaB))
    outfile.close()
    sys.exit(0)
