;
;   Compute the GBT efficiencies, etaA and etaB for a given frequency
;           The model is based on a memo by Jim Condon, provided by
;           Ron Maddalena
;
;   etaGBT, freqMHz, etaA, etaB
;   -------        
; HISTORY
; 06JUN28 GIL initial version
pro etaGBT, freqMHz, etaA, etaB, doPrint
;
  on_error,2
  if (not keyword_set(freqMHz)) then begin
    print,'usage: etaGBT, freqMHz, etaA, etaB, [doPrint]'
    print,'where: freqMHz - input frequency in MHz'
    print,'where: etaA    - output point source efficiency (range 0 to 1)'
    print,'where: etaB    - output extended source efficiency (range 0 to 1)'
    print,'where: [doPrint] - optionally print values if doPrint > 0'
    print,'EtaA,B model is from memo by Jim Condon, provided by Ron Maddalena'
    return
  endif 

  if (not keyword_set(doPrint)) then doPrint = 0.

  freqGHz = double(freqMHz)*0.001
  freqScale = 0.0163 * freqGHz
  etaA = double(0.71) * exp( - freqScale*freqScale)
  etaB = double(1.37) * etaA

  if (doPrint gt 0.) then print,freqGHz,' (GHz) -> eta A, B:', etaA, etaB
return
end
