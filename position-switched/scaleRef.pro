;IDL Procedure to test cal noise diode based calibration
; JSM:  smooth the data and remove RFI
;HISTORY
; 09DEC16 GIL use a higher order SavGol filter and more channels
; 09DEC02 GIL reduce min cal values  and increase smooth width
; 09DEC01 GIL smooth reference with savgol filter and convolution
; 09NOV23 GIL found code error, now using smoothed cals
; 09NOV16 GIL clean up comments
; 09NOV13 GIL use getTau() to get the predicted tau for this date
; 09NOV12 GIL use only the on-off 3C48 scans to define the cal reference
; 09NOV11 GIL initial test of gainScanInt2
; 09NOV10 GIL use ratioScanInt2.pro 

pro scaleRef, dcRef, dcCal, dcScaleRef, dcScaleCal

   if (not keyword_set( dcRef)) then begin
      print, 'scaleRef: scale reference spectrum and cal on-off data '
      print, 'containers (dc) for use with scaleInts procedure. '
      print, 'usage: scaleRef, dcRef, dcCal, dcScaleRef, dcScaleCal'
      print, 'output dcScaleRef reference spectrum, average of cal ON and CAL off values'
      print, 'output dcScaleCal reference cal_on - cal_off spectrum'
      print, 'The model sky is subtracted from the reference spectrum and'
      print, 'the reciprical cal values are returned in the cal spectrum'
      print, 'scaleRef uses a median filter to mitigate RFI effects.
      print, ''
      print, '----- Glen Langston, 2009 November 23; glangsto@nrao.edu'
      return
   endif

   ; copy header values and compute the reciprical cal values
   data_copy, dcCal, dcScaleCal
   nChan = n_elements( *dcCal.data_ptr) -1
   bChan = nChan/32
   eChan = nChan - bChan
   calMin = 0.001

   ; Smooth the cal values
   smoothCal, dcScaleCal, calMin

   *dcScaleCal.data_ptr = dcRef.mean_tcal / *dcScaleCal.data_ptr

   dcScaleCal.units = 'K/Count'   ; kevins per spectrometer count

   data_copy, dcRef, dcScaleRef

   for i = 2, (nChan-3) do begin
      ; median to remove Narrow RFI
      (*dcScaleRef.data_ptr)[i] = median((*dcRef.data_ptr)[(i-2):(i+2)])
   endfor
   (*dcScaleRef.data_ptr)[0] = (*dcScaleRef.data_ptr)[2]
   (*dcScaleRef.data_ptr)[1] = (*dcScaleRef.data_ptr)[2]
   (*dcScaleRef.data_ptr)[nChan-2] = (*dcScaleRef.data_ptr)[nChan-3]
   (*dcScaleRef.data_ptr)[nChan-1] = (*dcScaleRef.data_ptr)[nChan-3]

   nSavGol = nChan/16
   savgolFilter = SAVGOL(nSavGol, nSavGol, 0, 5) 
   *dcScaleRef.data_ptr = CONVOL(*dcScaleCal.data_ptr, savgolFilter, $\
                                 /EDGE_TRUNCATE)
   *dcScaleRef.data_ptr = *dcScaleRef.data_ptr * *dcScaleCal.data_ptr 

   ; if full calibration, remove the Sky contribution to the reference
                                ; if doing full calibration, make the
                                ; first steps towards calibration
                                ;of individual integrations 

   tSkys = *dcScaleRef.data_ptr
   doPrint = 1
   setTSky, dcScaleRef, tSkys, doPrint
   *dcScaleRef.data_ptr = smooth( *dcScaleRef.data_ptr - tSkys, $\
                                  11, /edge_truncate)
   ; prepare to compute reference Tsys with the Sky removed
   bChan = round(nChan/10)
   eChan = nChan - bChan
   dcScaleRef.tsys  = avg( (*dcScaleRef.data_ptr)[bChan:eChan])
   dcScaleRef.units = 'K T_A' 
   dcScaleCal.tsys  = dcScaleRef.tsys
   return
end


