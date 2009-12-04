;IDL Procedure to test cal noise diode based calibration
;HISTORY
; 09NOV13 GIL use getTau() to get the predicted tau for this date
; 09NOV12 GIL use only the on-off 3C48 scans to define the cal reference
; 09NOV11 GIL initial test of gainScanInt2
; 09NOV10 GIL use ratioScanInt2.pro 

pro aveDcs, dcs, dcOut, doShow

   if (not keyword_set( dcs)) then begin
      print, 'avedcs: average data containers, weight by integration time'
      print, 'avedcs: dcs, dcOut, doShow'
      print, 'input   dcs   array of data containers to average'
      print, 'output dcOut  average data container'
      print, 'input  doShow optionally show (doShow=1) data containers
      print, ''
      print, '----- Glen Langston, 2009 November 13; glangsto@nrao.edu'
      return
   endif

   if (not keyword_set( doShow)) then doShow = 0

   ; prepare to compute sums 
   tSum = 0.0 & elSum = 0.0 & azSum = 0.0 & lonSum = 0.0 & latSum = 0.0 
   tLatSum = 0.0 & tLonSum = 0.0 & tSysSum = 0.0

   a = {accum_struct}  ; structure to hold the ongoing sum
   accumclear, a       ; clear it

   for i=0,(n_elements(dcs) - 1) do begin dcaccum, a, dcs[i] & $\
     if (doShow) then show, dcs[i] & endfor

   accumave, a, dcOut  ; get the average

   ; get average coordiate and system temps
   for i=0,n_elements(dcs)-1 do begin & $\
     tInt=dcs[i].exposure & $\
     tSum=tSum+tInt &$\
     tSysSum=tSysSum + (tInt*dcs[i].tsys) & $\
     elSum=elSum+(tInt*dcs[i].elevation) & $\
     azSum=azSum+(tInt*dcs[i].azimuth) & $\
     lonSum=lonSum+(tInt*dcs[i].longitude_axis) & $\
     latSum=latSum+(tInt*dcs[i].latitude_axis) & $\
     tLonSum=tlonSum+(tInt*dcs[i].target_longitude) & $\
     tLatSum=tlatSum+(tInt*dcs[i].target_latitude) & endfor

   ; normalize sums
   dcOut.elevation = elSum/tSum
   dcOut.tsys      = tSysSum/tSum
   dcOut.azimuth   = azSum/tSum
   dcOut.longitude_axis = lonSum/tSum
   dcOut.latitude_axis  = latSum/tSum
   dcOut.target_longitude = tLonSum/tSum
   dcOut.target_latitude  = latSum/tSum
   dcOut.exposure  = tSum

   ; now clean up
   accumclear, a 
   return
end


