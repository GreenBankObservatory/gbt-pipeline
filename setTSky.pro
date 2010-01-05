;IDL Procedure to generate an array of Tsky values based on a spectrum
;values
;HISTORY
; 09NOV13 GIL initial version

pro setTSky, dc, tSkys, doPrint, opacityA, opacityB, zenithTauA, zenithTauB

   if (not keyword_set( dc)) then begin
      print, 'setTSky: compute sky temperature contribution to a spectrum'
      print, 'usage: setTSky, dc, tSkys'
      print, 'input   dc    data container describing the observation'
      print, 'output  tSkys array of tSky values (K)'
      print, '---- Glen Langston, 2009 November 13; glangsto@nrao.edu'
      return
   endif
 
   if (not keyword_set( doPrint)) then doPrint = 0
   if (not keyword_set( opacityA)) then opacityA = 1.0
   if (not keyword_set( opacityB)) then opacityB = 1.0

                                ; there has to be a better way to do
                                ; this, even here, freqMHzA and B are
                                ; calculated twice assuming zenithTau*
                                ; are supplied by the user to save time

   refChan = dc.reference_channel
   nChan   = n_elements( *dc.data_ptr)
   delChan = dc.frequency_interval
   freqMHzA = (dc.observed_frequency + ((0 - refChan)*delChan))  * 1.E-6
   freqMHzB = (dc.observed_frequency + ((nChan - refChan)*delChan))  * 1.E-6
   if (not keyword_set(zenithTauA)) or (not keyword_set(zenithTauB)) then begin

       if (not keyword_set(zenithTauA)) then zenithTauA = getTau( dc.mjd, freqMHzA)
       if (not keyword_set(zenithTauB)) then zenithTauB = getTau( dc.mjd, freqMHzB)
       ;report tau?
       if (doPrint gt 0) then $\
         print,dc.projid,dc.timestamp, freqMHzA, freqMHzB, zenithTauA, zenithTauB, $\
         format='(%"Obs: %s %s Freq: %10.3f-%10.3f (MHz) Tau:%7.4f-%7.4f")'
   endif

   tSkys = *dc.data_ptr & airTempKA = 300. & airTempKB = 300. ; int array, values
   tatm, freqMHzA/1000., dc.tambient-273.15, airTempKA
   tatm, freqMHzB/1000., dc.tambient-273.15, airTempKB
   ; now get opacity factors at the band edges
   opacity, zenithTauA, opacityA, dc.elevation
   opacity, zenithTauB, opacityB, dc.elevation
   ; compute sky temps at band edges
   tSkyA = airTempKA * (opacityA - 1.) 
   tSkyB = airTempKB * (opacityB - 1.) 
   nChan = n_elements( *dc.data_ptr)
   ; now perform linear interpolation across the band
   dT = (tSkyB-tSkyA)/float(nChan )
   nChan = nChan - 1
   for i = 0, nChan do begin tSkys[i] = tSkyA + (i*dT) & endfor 

   if (doPrint gt 0) then $\
     print, tSkys[0],tSkys[nChan],dc.elevation, $\
     format='(%"tSkys:%8.3f-%8.3f (K) for El:%8.3f (d)")'

   return
end                      ; end of setTSky

