""" Module to compute the atmospheric opacity from a model

    This procedure will be used when weather data computed by Ron
    Maddellana's modes is un-available.

    The model includes the water line, but neither O2 nor hydrosols
    (water droplets in clouds and rain).

"""
import sys
import partialPressureWater

def densityWater(pressureMBar, tempC, dewPtC):
    """Determine density of water in air

      Lehto code transcribed from Ron Maddelenas TCL code

      Keyword arguments:
      pressureMBar -- atmospheric pressure in mBar
      tempC -- air temperature in C
      dewPtC -- dew point temperature in C

      Returns:
      densityGM3 water density in gm/m^3

    """

   partPresMBar = 1.0
   partPresMBar = partialPressureWater.partialPressureWater(pressureMBar,dewPtC)
   tempK = tempC + 273.15
   densityGM3 = (0.7217 * partPresMBar * 300.0/ tempK)
   return densityGM3

if __name__ == "__main__":
    outfilename = "waterdensity.txt"
    dw = densityWater(sys.argv[1],sys.argv[2])
    print 'Water density:',dw,'(gm/m^3)'
    print 'Writing value to',outfilename
    outfile = open(outfilename,'w')
    outfile.write(str(dw))
    outfile.close()
    sys.exit(0)
