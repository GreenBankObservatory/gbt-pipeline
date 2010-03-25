#! /usr/bin/env python

"""Module to compute the atmospheric opacity from a model

   This will be used when weather data computed by Ron Maddallena's
   modes is un-available.

   The model includes the water line, but neither O2 nor hydrosols
   (water droplets in clouds and rain).

"""

import sys

def partialPressureWater(pressureMBar, dewPtC):
    """Compute partial pressure of water

    Calculated from pressure and dewpoint.
    Based on Goff Gratch equation (Smithsonian Tables, 1984
    after Goff and Gratch, 1946) 
    Ron Maddalena and Glen Langston 2009 December 2

    Keyword arguments:
    pressureMBar -- Astmospheric Pressure in mBar
    dewPtC -- Dew point Temperature in C
    
    Returns:
    Partial Pressure of water (mBar)

    For ice: Goff Gratch equation (Smithsonian Tables, 1984, after Goff
             and Gratch, 1946):
    {6.1071*pow(10.,9.973973-9.09718*$tt-0.876793/$tt)/pow($tt,3.56654)}

    """

   dewPtK = dewPtC + 273.15
   tt= 373.16/dewPtK

   partPresMBar = 1013.246*(tt^5.02808)*(10.^(-7.90298*(tt-1.)))\
                    - 1.3816e-7*((10.^(11.344*(1.-1./tt))-1.))\
                    + 8.1328e-3*((10.^(-3.49149*(tt-1.))-1.))
   return partPresMBar

if __name__ == "__main__":
    outfilename = "partialpressure.txt"
    pp = partialPressureWater(float(sys.argv[1]),float(sys.argv[2]))
    print 'Partial water pressure:',pp,'(mBar)'
    print 'Writing value to',outfilename
    outfile = open(outfilename,'w')
    outfile.write(str(pp))
    outfile.close()
    sys.exit(0)
