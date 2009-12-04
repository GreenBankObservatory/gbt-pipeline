; scaleInt fully calibrates one polarization of a set of map scans
; all integrations
; HISTORY
; 09Nov19 GIL  add beam offset calculation
; 09Nov17 GIL  clean up the show process
; 09Nov16 GIL  clean up comments
; 09Nov14 GIL  check factors
; 09Nov13 GIL  initial version based scaleScanInt2
; 09Nov12 GIL  further smooth values, remove unused indicies
; 09Nov11 GIL  initial version based on ratioScanInt2
; 09Nov09 GIL  initial version based on calScanInt2

pro scaleIntsRef, scans, iPol, iBand, iFeed, dcBRef, dcERef, $\
                   dcSCal, doKeep

   if (not keyword_set( scans)) then begin
      print, 'scaleIntsRef: compute and write the tsys/ref and tsys/tcal'
      print, 'for GBT scans.   The references and cal on-off'
      print, 'values must be pre-computed and scaled with scaleRef()'
      print, 'usage: scaleIntsRef, scans, iPol, iBand, iFeed, dcBRef, dcERef, dcSCal, doKeep'
      print, '      iPol   observation polarization number, range 0 to n-1'
      print, '      iBand  observation band number, range 0 to n-1'
      print, '      iFeed  observation feed number, range 0 to n-1'
      print, '      dcBRef begin reference spectrum for polarization'
      print, '      dcERef end reference spectrum for polarization'
      print, '      dcSCal  Average cal-on - cal-off value'
      print, '      doKeep Keep (doKeep>0) the calibrated scans integrations'
      print, 'Output is to a log file and a keep'
      print, '----- Glen Langston, 2009 November 19; glangsto@nrao.edu'
      return
   endif

   if (not keyword_set( iPol)) then iPol = 0
   if (not keyword_set( iBand)) then iBand = 0
   if (not keyword_set( iFeed)) then iFeed = 0
   if (not keyword_set( doKeep)) then doKeep = 0

   openw, wlun, 'scaleIntsRef.txt', /append, /get_lun

   ; now get reference times for linear interpolation
   tBegRef = dcBRef.utc & tEndRef = dcERef.utc
   ; if past ut midnight 
   if (tBegRef gt tEndRef) then tEndRef = tEndRef + 86400.
   dT = tEndRef - tBegRef   ; also need time between scans
   if (dT eq 0) then begin
       print,'Reference Times the same: ', dT, $\
         ' ', dcBRef.timestamp, ' ', dcERef.timestamp
       dT = 1;
   endif

   if (dcERef.polarization ne dcBRef.polarization) then begin
      print,'Ref. Polarization miss match: ', dcBRef.polarization, ' ne ', $\ 
         dcERef.polarization
     return
   endif

   printf, wlun, '#Tim 1: Tim 2: Dt: ', tBegRef, tEndRef, dT, $\
     format='(A-25, F9.3, x, F9.3, x, F8.3)'

   for iScan = 0, n_elements( scans) - 1 do begin 
     !g.frozen = 1
     gettp, scans[iScan], int=0, plnum=iPol, ifnum=iBand, fdnum=iFeed
     if (!g.s[0].polarization ne dcBRef.polarization) then begin
        print,'Obs/Ref Pol. miss match: ', !g.s[0].polarization, ' ne ', $\ 
          dcBRef.polarization
        return
     endif
     printf, wlun, '#Scan:', scans[iScan], 'Band:', iBand, 'Feed:', iFeed, $\
       strtrim(!g.s[0].timestamp,2), $\
       format='(A-6, I-5, A-6, I-3, A-6, I-3, A-25)'
     printf, wlun, '#Obj :', !g.s[0].source, !g.s[0].procedure, $\
       !g.s[0].procseqn, '/', !g.s[0].procsize, $\
       format='(A-6, A-12, A-9, X, I-4, A-1, I-4)'
     printf, wlun, '#Ref 0: Tcal, Tsys', dcBRef.mean_tcal, dcBRef.tsys, $\
       !g.s[0].polarization, $\
       format='(A-20, F-8.3, F9.3, X, A-4)'
     tSkys = *!g.s[0].data_ptr  ; prepare for sky correction 

     aScanInfo=scan_info(scans[iScan])
; retrieve counts of different spectra types
     nInt = aScanInfo.n_integrations & nPol = aScanInfo.n_polarizations
     nFeed = aScanInfo.n_feeds       & nIf = aScanInfo.n_ifs
     nChan = aScanInfo.n_channels    & nSample = aScanInfo.n_samplers
     bChan=round(nChan/10)           & eChan=round(9*nChan/10)

   ; trip off ends of spectra to save some computations of the average
   calMids = (*dcSCal.data_ptr)[bChan:eChan]

                                ; now select all integrations for this
                                ; scan; separate cal on/off and pol A/B
   calOns = getchunk(scan=scans[iScan], count=count, cal="T", plnum=iPol, $\
                      ifnum=iBand, fdnum=iFeed)
   calOfs = getchunk(scan=scans[iScan], cal="F", plnum=iPol, ifnum=iBand, $\
                      fdnum=iFeed)
   if (count le 0) then begin $\
     print,'Error reading scan: ', scans[iScan], ', No integrations' & $\
     return & endif

;   gains = fltarr( count)  ; prepare to collect an array of gains
   count=count-1; correct for 0 based counting
   opacityA = 1.0 & opacityB = 1.0

   ; for all integrations in a scan collect arrays of gains
;   for iInt= 0, count do begin
;      subs = (*calOns[iInt].data_ptr)[bchan:eChan] - $\ 
;        (*calOfs[iInt].data_ptr)[bchan:eChan] ;

;      ratios = subs*calMids
;      gain = avg( ratios)
;      gains[iInt] = gain
;   endfor             

   ; Now boxcar smooth gains, a few samples wide 
 ;  gainSmooths = smooth( gains, 7, /edge_truncate)

   ; for all integrations in a scan; apply gain correction
   doPrint = 0
   nInt2 = round(count / 2) 
   for iInt= 0, count do begin
      setTSky, calOns[count], tSkys, doPrint, opacityA, opacityB
                                ; now create an opacity array for this scan
      factors = tSkys
      dOpacity = (opacityB - opacityA)/float(nChan)
      etaA = 1.0 &  etaB = 1.0
      etaGBT, 1.E-6*calOns[0].reference_frequency, etaA, etaB
      ; compute frequency dependent opacity factor (no eta B dependence yet)
      for i = 0, (nChan -1) do begin $\
        factors[i]=(opacityA+(i*dOpacity))/etaB & endfor
      if (doprint gt 0) then $\
        print,'factors: ',factors[0], factors[nChan-1], opacityA, opacityB, $\
        dOpacity    

      aves = (*calOns[iInt].data_ptr + *calOfs[iInt].data_ptr)*.5;
      t = calOns[iInt].utc
      ; compute interpolated reference
      a = (dcERef.utc-t)/dT
      b = (t - dcBRef.utc)/dT
      ; interpolate reference spectrum (sky has been removed)
      refs = (a*(*dcBRef.data_ptr)) + (b*(*dcERef.data_ptr))
      tSys  = (a*dcBRef.tsys) + (b*dcERef.tsys)
      *calOns[iInt].data_ptr = factors*(((aves * *(dcSCal.data_ptr)) - (tSkys + refs)))
;      *calOns[iInt].data_ptr = aves * *(dcSCal.data_ptr)
      middleT = avg( (*calOns[iInt].data_ptr)[bChan:eChan])
      rmsT = stddev( (*calOns[iInt].data_ptr)[bChan:eChan])
      calOns[iInt].units = 'T_B*'
      ; tsys is composed of source, sky and reference (without sky).
      calOns[iInt].tsys = middleT + tSkys[round(nChan/2)] + dcSCal.tsys
      calcRms = calOns[iInt].tsys/sqrt(calOns[iInt].exposure*calOns[iInt].frequency_resolution)
      set_data_container, calOns[iInt]
      refbeamposition, 1
;      if (iInt eq 0) then show else oshow
      if (doKeep gt 0) then keep

      if ((iInt eq 0) or (iInt eq nInt2)) then begin unfreeze & $\
        !g.frozen = 0 & show,calOns[iInt] & !g.frozen = 1 & freeze & endif

      ; report
      printf, wlun, scans[iScan], iInt, calOns[iInt].utc, $\
         middleT, (*calOns[iInt].data_ptr)[round(nChAn/2)], tSys,  $\
         calOns[iInt].tsys, rmsT, calcRms, $\
         format='(I-5, I-5, F-10.3, x, F-10.4, F-10.4, F-10.4, F-10.4, F-7.3, F-7.3)'
    endfor             

;   clean up to avoid memory disaster
   for i = 0, count do begin
      data_free, calOns[i]
      data_free, calOfs[i]
  endfor

endfor
!g.frozen = 0 & unfreeze
; close report file
close,wlun

RETURN
END

