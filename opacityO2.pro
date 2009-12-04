; procedure to compute the atmospheric opacity from a model
; This procedure will be used when weather data computed by Ron
; Maddallena's modes is un-available.
; The procedures were written in Tcl by Ron Maddallena and translated
; to idl by Glen Langston.   The model includes the water line, but
; neither O2 nor hydrosols (water droplets in clouds and rain).
; HISTORY
; 09DEC02 GIL initial version

pro opacityO2, freqGHz, tauO2

   if ( not keyword_set( freqGHz)) then begin
      print, 'opacityO2: returns interpolated O2 opacity based on Letho'
      print, 'thesis values, pag 149, table A-2'
      print, 'Usage: freqGHz, tauO2'
      print, 'Where    freqGHz     Observing Frequency GHz'
      print, 'Return   tauO2       Oxygen Opacity'
      print, 'Glen Langston 2009 December 3'
      return
   endif

   if (freqGHz lt 3.) then begin
     tauO2 = 0. 
     return
   endif
   if (freqGHz gt 55.) then begin
     tauO2 = 6.4204
     return
   endif

   ; else will interpolate O2 taus values
   ;       0     1     2     3     4      5    6     7     8     9  GHz
   tauO2s=[.0000,.0000,.0000,.0001,.0002,.0003,.0004,.0006,.0008,.0010,$\
           .0013,.0015,.0018,.0022,.0026,.0030,.0035,.0040,.0046,.0052,$\
           .0059,.0067,.0075,.0085,.0095,.0106,.0119,.0132,.0148,.0165,$\
           .0184,.0205,.0229,.0256,.0286,.0321,.0360,.0405,.0458,.0518,$\
           .0590,.0674,.0774,.0896,.1044,.1228,.1460,.1761,.2161,.2715,$\
           .3528,.4857,.7452,1.3518,2.8771,6.4204]
   iFreq = round(freqGHz - .5)
   tau1  = tauO2s[iFreq]
   tau2  = tauO2s[iFreq+1]
                                ; linearly interpolate/extrapolate;
                                ; since dFreq = 1GHz, no division needed.
   tauO2 = (tau2 * (freqGHz - iFreq)) + (tau1 * ((iFreq + 1.)-freqGHz))
   return
end
