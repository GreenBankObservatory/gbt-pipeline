;IDL procedure to estimate the opacity correction factor 
;HISTORY 
;08DEC18 GIL aadd frequencies for TMC-BELL search for max HC9N
;06AUG04 GIL add frequencies for TMC-BELL search for max HC9N
;06JUL05 GIL check for "standard" HC13N frequency and set up labels
;06JUN30 GIL make more general purpose, by allowing several indexs
;06MAY23 GIL initial version
; fourVelocity takes an input start index, 
; and assume the x and y ranges have already been set
; 

pro opacity, zenithTau, opacityFactor, elDeg

  if (not keyword_set( zenithTau)) then begin
    print,'usage: opacity, zenithTau, opacityFactor, elDeg'
    print,'where zenithTau: is the zenith tau factor'
    print,'opacityFactor  : returned scale factor (> 1) atmosphere'
    print,'where elDeg: optional source elDeg (degrees)'
    return
  endif

  opacityFactor = 1.
  if (zenithTau le 0.) then begin
    print, 'Illegal zenithTau:',zenithTau
    return
  endif

  ; use elevation in data header in not provide
  if (not keyword_set( elDeg)) then elDeg = !g.s[0].elevation

  nAtmos = 1.d0
  natm,elDeg,nAtmos                       ; get number of atmospheres at el
  opacityFactor = exp( zenithTau*nAtmos)
  return
end 
