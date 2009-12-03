; tsysair.pro estimates the atmospheric contribution to the system temp
; HISTORY
; 08DEC19 GIL initial version
;

pro tsysair, tau, opacityFactor, tempAir

  on_error,2
  if (not keyword_set(tau)) then begin
    print,'tSysAir: compute the atmospheric contribution to system temp'
    print,'usage: tSysAir, tau, tempAir'
    print,'where: tau     - current atmospheric attenuation'
    print,'where: tempAir - output atmospheric contribution to the system temp'
    print,'Procedure written by Glen Langston, 2008 December 19'
    return 
  endif  

  if (not keyword_set(opacityFactor)) then opacityFactor = 1.0
  elevation = !g.s[0].elevation
  freqGHz = !g.s[0].center_frequency / 1000000000.
  tmpC      = !g.s[0].tambient - 273.15 ; Ground temperature (C)
  airTempK  = !g.s[0].tambient  ; Air temperature (K)
  tatm, freqGHz, tmpC, airTempK ; compute Air temp from model
  opacity, tau, opacityFactor, elevation
  tSysAir = airTempK*(1.-(1./opacityFactor))
  airTempAdded = airTempK*(1.-(1./opacityFactor))
  if (not keyword_set(tempAir)) then $\
    print,'Atmospheric contribution to System temp: ', airTempAdded
  
  tempAir = airTempAdded
  return
end


