;IDL Procedure to test cal noise diode based calibration
;HISTORY
; 09DEC14 JSM comment: this is an enhancement of gettp in GBTIDL
; 09NOV30 GIL get integrations one scan at a time, to avoid overflow problem
; 09NOV13 GIL use getTau() to get the predicted tau for this date
; 09NOV12 GIL use only the on-off 3C48 scans to define the cal reference
; 09NOV11 GIL initial test of gainScanInt2
; 09NOV10 GIL use ratioScanInt2.pro 

pro getRef, scans, iPol, iBand, iFeed, dcRef, dcCal, doShow

   if (not keyword_set( scans)) then begin
      print, 'getRef: average integrations to calc. reference and cal on-off spectra'
      print, 'usage: getRef, scanlist, iPol, iBand, iFeed, dcRef, dcDCal, doShow'
      print, '      scans  integer array of scan numbers to average'
      print, '      iPol   observation polarization number, range 0 to n-1'
      print, '      iBand  observation band number, range 0 to n-1'
      print, '      iFeed  observation feed number, range 0 to n-1'
      print, '      Outputs are data containers'
      print, 'output dcRef reference spectrum, average of cal ON and CAL off values'
      print, 'output dcCal reference cal_on - cal_off spectrum'
      print, '      doShow optionally (doShow=1) show spectra accumulated'
      print, ''
      print, 'getRef does not include the T-Sky correction, use scaleRef.pro'
      print, 'getRef performs no smoothing or RFI rejection'
      print, ''
      print, '----- Glen Langston, 2009 November 13; glangsto@nrao.edu'
      return
   endif

   ; prepare to compute sums 
   tSum = 0.0 & elSum = 0.0 & azSum = 0.0 & lonSum = 0.0 & latSum = 0.0 
   tLatSum = 0.0 & tLonSum = 0.0

;   print, 'GetRef: s,p,b,f: ',scans[0], iPol, iBand, iFeed
;   JSM: the following lines don't seem to add anything
;   gettp, scans[0], int=0, plnum=iPol, ifnum=iBand, fdnum=iFeed

   ; copy most parameters to outputs
;   data_copy, !g.s[0], dcRef
;   data_copy, !g.s[0], dcCal

   aOn = {accum_struct}         ; structure to hold the ongoing calOn sum
   accumclear, aOn              ; clear it
   aOff = {accum_struct}        ; structure to hold the ongoing calOf sum
   accumclear, aOff             ; clear it

   nScans = n_elements( scans )

   ;for each scan
   for iScan=0, (nScans-1) do begin

     ;get all integrations for a scan at the given polarization, band and feed
     scan=scans[iScan]
     plnum=iPol
     ifnum=iBand
     fdnum=iFeed
     data = getchunk(scan, plnum, ifnum, fdnum)

     ;split the integration spectra into calOn's and calOff's
     calOns = where(data.cal_state eq 1,onCount)
     calOffs = where(data.cal_state eq 0,offCount)
     
;     if (doShow le 0) then freeze
     
     ;accumulate all calOn integrations for the scan
     ; (adding to prev. scans)
     for i=0,onCount-1 do begin dcaccum, aOn, data[calOns[i]] & $\
       if (doShow) then show, data[calOns[i]] & endfor

     ; get average coordiates and exposure time for the scan
     for i=0,onCount-1 do begin & $\
       tInt=data[calOns[i]].exposure & tSum=tSum+tInt &$\
       elSum=elSum+(tInt*data[calOns[i]].elevation) & $\
       azSum=azSum+(tInt*data[calOns[i]].azimuth) & $\
       lonSum=lonSum+(tInt*data[calOns[i]].longitude_axis) & $\
       latSum=latSum+(tInt*data[calOns[i]].latitude_axis) & $\
       tLonSum=tlonSum+(tInt*data[calOns[i]].target_longitude) & $\
       tLatSum=tlatSum+(tInt*data[calOns[i]].target_latitude) & endfor
         
     ;accumulate all calOff integrations for the scan
     ; (adding to prev. scans)
     for i=0,offCount-1 do begin dcaccum, aOff, data[calOffs[i]] & $\
       if (doshow gt 0) then show, data[calOffs[i]] & endfor

     ; now clean up
     data_free, data
   endfor

   accumave, aOn, calOnAve   ; get the cal ON average
   accumave, aOff, calOffAve   ; get the cal OFF average

   ; this clears any memory in the accumulators
   accumclear, aOn
   accumclear, aOff

   ;now complete cal on - cal off spectrum and store as a data container
   setdcdata, dcCal, (*calOnAve.data_ptr - *calOffAve.data_ptr)

   ;now complete (cal on + cal off)/2 spectrum and store as a data container
   setdcdata, dcRef, (*calOnAve.data_ptr + *calOffAve.data_ptr)*0.5

   ; normalize the sums and transfer to output
   dcCal.elevation = elSum/tSum
   dcCal.azimuth   = azSum/tSum
   dcCal.longitude_axis = lonSum/tSum
   dcCal.latitude_axis  = latSum/tSum
   dcCal.target_longitude = tLonSum/tSum
   dcCal.target_latitude  = latSum/tSum
   dcCal.exposure  = tSum

   dcRef.elevation = elSum/tSum
   dcRef.azimuth   = azSum/tSum
   dcRef.longitude_axis = lonSum/tSum
   dcRef.latitude_axis  = latSum/tSum
   dcRef.target_longitude = tLonSum/tSum
   dcRef.target_latitude  = latSum/tSum
   dcRef.exposure  = tSum

   ; prepare to compute system temperature sums
   nChan = n_elements( *dcRef.data_ptr)
   bChan = round(nChan/10)
   eChan = nChan - bChan

   ; compute spectrum in units of cal
   ratios = (*dcRef.data_ptr)[bChan:eChan] / (*dcCal.data_ptr)[bchan:echan] 
   
   tSys = avg( ratios ) * dcRef.mean_tcal
   
   ; returned via the dcCal and dcRef structures, which are passed parameters
   ; from the calling routine
   dcCal.tsys = tSys
   dcRef.tsys = tSys

;   unfreeze

   ; cleanup memory
   ;data_free, calOffAve & data_free, calOnAve
   data_free, calOffAve & data_free, calOnAve

   return

end


