#! /usr/bin/env python

import sys
import math

def humidityToTDew(humidity,tempC):
    """Converts from relative humidity to dew point
    
    Keyword arguments:
    humidity -- relative humidity, range 0 to 1'
    tempC -- Air temperature (C)'
      
    Returns:
    tDewC -- Dew point temperature (C)'
    """


   if ((humidity > 1) or (humidity < 0)):
      print 'humidity range is 0 to 1:',humidity,'is out of range'
      tDewC = tempC
      return tDewC

   a = 17.27
   b = 237.7  # Celsius
   alpha = ((a*tempC)/(b+tempC)) + math.log(humidity)

   tDewC = (b * alpha)/ (a - alpha)
   return tDewC

if __name__ == "__main__":
    outfilename = 'dewpointtemp.txt'
    dwpt = humidityToTDew(float(sys.argv[1]),float(sys.argv[2]))
    print 'Dew point temperature:',dwpt,'(C)'
    print 'Writing value to',outfilename
    outfile = open(outfilename,'w')
    outfile.write(str(dwpt))
    outfile.close()
    sys.exit(0)
