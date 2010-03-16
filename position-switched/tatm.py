"""Estimates the atmospheric effective temperature

Based on local ground temperature measurements.  These estimates
come from a model reported by Ron Maddalena
 
1) A = 1/sin(elev) is a good approximation down to about 15 deg but
starts to get pretty poor below that.  Here's a quick-to-calculate,
better approximation that I determined from multiple years worth of
weather data and which is good down to elev = 1 deg:

     if (elev LT 39) then begin
        A = -0.023437  + 1.0140 / sin( (!pi/180.)*(elev + 5.1774 / (elev
+ 3.3543) ) )
     else begin
        A = sin(!pi*elev/180.)
     endif 

2) Using Tatm = 270 is too rough an approximation since Tatm can vary
from 244 to 290, depending upon the weather conditions and observing
frequency.  One can derive an approximation for the default Tatm that is
accurate to about 3.5 K from the equation:

TATM = (A0 + A1*FREQ + A2*FREQ^2 +A3*FREQ^3 + A4*FREQ^4 + A5*FREQ^5)
              + (B0 + B1*FREQ + B2*FREQ^2 + B3*FREQ^3 + B4*FREQ^4 +
B5*FREQ^5)*TMPC

where TMPC = ground-level air temperature in C and Freq is in GHz.  The
A and B coefficients are:

                             A0=    259.69185966 +/- 0.117749542
                             A1=     -1.66599001 +/- 0.0313805607
                             A2=     0.226962192 +/- 0.00289457549
                             A3=   -0.0100909636 +/- 0.00011905765
                             A4=   0.00018402955 +/- 0.00000223708
                             A5=  -0.00000119516 +/- 0.00000001564
                             B0=      0.42557717 +/- 0.0078863791
                             B1=     0.033932476 +/- 0.00210078949
                             B2=    0.0002579834 +/- 0.00019368682
                             B3=  -0.00006539032 +/- 0.00000796362
                             B4=   0.00000157104 +/- 0.00000014959
                             B5=  -0.00000001182 +/- 0.00000000105

"""

import sys

def tatm(freqGHz, tmpC):
    """
    
    Keyword arguments:
    freqGHz -- input frequency in GHz
    where: tmpC     - input ground temperature in Celsius

    Returns:
    airTempK -- output Air Temperature in Kelvin

    tatm model is provided by Ron Maddalena

    """

    # where TMPC = ground-level air temperature in C and Freq is in GHz.
    # The A and B coefficients are:
    A = [259.69185966, -1.66599001, 0.226962192,
         -0.0100909636,  0.00018402955, -0.00000119516 ]
    B = [0.42557717,    0.033932476,0.0002579834,
         -0.00006539032, 0.00000157104, -0.00000001182]

    FREQ  = float(freqGHz)
    FREQ2 = FREQ*FREQ
    FREQ3 = FREQ2*FREQ
    FREQ4 = FREQ3*FREQ
    FREQ5 = FREQ4*FREQ

    TATM = A[0] + A[1]*FREQ + A[2]*FREQ2 +A[3]*FREQ3 + A[4]*FREQ4 + A[5]*FREQ5
    TATM = TATM + (B[0] + B[1]*FREQ + B[2]*FREQ2 + B[3]*FREQ3 + B[4]*FREQ4 + B[5]*FREQ5)*float(tmpC)

    airTempK = TATM
    return airTempK

if __name__ == "__main__":
    airtempK = tatm(sys.argv[1],sys.argv[1])
    outfile = open("airtempK.txt",'w')
    outfile.write(str(airtempK))
    outfile.close()
    sys.exit(0)
