; procedure to compute the atmospheric opacity from a model
; This procedure will be used when weather data computed by Ron
; Maddallena's modes is un-available.
; The procedures were written in Tcl by Ron Maddallena and translated
; to idl by Glen Langston.   The model includes the water line, but
; neither O2 nor hydrosols (water droplets in clouds and rain).
; HISTORY
; 09DEC02 GIL initial version

pro partialPressureWater, pressureMBar, dewPtC, partPresMBar

   if ( not keyword_set( pressureMBar)) then begin
      print, 'partialPressureWater: calculated from pressure and dewpoint'
      print, 'Usage: partialPressureWater, pressureMBar, dewPtC, partPresMBar'
      print, 'Where pressureMBar   Astmospheric Pressure in mBar'
      print, '      dewPtC         Dew point Temperature in C'
      print, 'Return partPresMBar Partial Pressure of water (mBar)'
      print, 'Based on Goff Gratch equation (Smithsonian Tables, 1984'
      print, ' after Goff and Gratch, 1946) '
      print, 'Ron Maddalena and Glen Langston 2009 December 2'
      return
   endif

   dewPtK = dewPtC + 273.15
   tt= 373.16/dewPtK

   partPresMBar = 1013.246*(tt^5.02808)*(10.^(-7.90298*(tt-1.)))  $\
                    - 1.3816e-7*((10.^(11.344*(1.-1./tt))-1.)) $\
                    + 8.1328e-3*((10.^(-3.49149*(tt-1.))-1.))
; for ice: # Goff Gratch equation (Smithsonian Tables, 1984, after Goff
; and Gratch, 1946):
; {6.1071*pow(10.,9.973973-9.09718*$tt-0.876793/$tt)/pow($tt,3.56654)}]

   return
end
