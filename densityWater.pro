; procedure to compute the atmospheric opacity from a model
; This procedure will be used when weather data computed by Ron
; Maddellana's modes is un-available.
; The procedures were written in Tcl by Ron Maddallena and translated
; to idl by Glen Langston.   The model includes the water line, but
; neither O2 nor hydrosols (water droplets in clouds and rain).
;
; HISTORY
; 89JAN01 HJL Harry Johannes Lehto codes Liebe etal 1982's models.
; 09DEC02 GIL initial version

pro densityWater, pressureMBar, tempC, dewPtC, densityGM3
   if (not keyword_set(pressureMBar)) then begin
      print, 'densityWater: return the density of water in air'
      print, 'usage: densityWater, pressureMBar tempC, dewPtC'
      print, 'Where pressureMBar atmospheric pressure in mBar'
      print, '      tempC        air temperature in C'
      print, '      dewPtC       dew point temperature in C'
      print, 'Output: densityGM3 water density in gm/m^3'
      print, 'Lehto code transcribed from Ron Maddelenas TCL code'
      print, ' Glen Langston 2009 December 2'
      return
   endif

   partPresMBar = 1.
   partialPressureWater, pressureMBar, dewPtC, partPresMBar
   tempK = tempC + 273.15
   densityGM3 = (0.7217 * partPresMBar * 300./ tempK)
   return 
end
