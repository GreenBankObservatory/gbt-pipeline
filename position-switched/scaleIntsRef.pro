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
                                ; scan; separate cal on/off and pol
                                ; A/B
   ; its cheaper to get both in one call and use a mask here
   scan=scans[iScan]
   count=count
   plnum=iPol
   ifnum=iBand
   fdnum=iFeed
   data = getchunk(scan, count, plnum, ifnum, fdnum)
   if (count le 0) then begin $\
     print,'Error reading scan: ', scans[iScan], ', No integrations' & $\
     return & endif

   calOns = where(data.cal_state eq 1, count)
   calOfs = where(data.cal_state eq 0)


;   gains = fltarr( count)  ; prepare to collect an array of gains
   count=count-1; correct for 0 based counting
   opacityA = 1.0 & opacityB = 1.0

   ; for all integrations in a scan collect arrays of gains
;   for iInt= 0, count do begin
;      subs = (*(data[calOns[iInt]]).data_ptr)[bchan:eChan] - $\ 
;        (*(data[calOfs[iInt]]).data_ptr)[bchan:eChan] ;

;      ratios = subs*calMids
;      gain = avg( ratios)
;      gains[iInt] = gain
;   endfor             

   ; Now boxcar smooth gains, a few samples wide 
 ;  gainSmooths = smooth( gains, 7, /edge_truncate)

   ; get the zenith opacities at the band edges
   refChan = data[calOns].reference_channel
    nChan = n_elements(*(data[calOns[0]]).data_ptr)
    delChan = data[calOns].frequency_interval
    freqMHzA = (data[calOns].observed_frequency + ((0-refChan)*delChan)) * 1.E-6
    freqMHzB = (data[calOns].observed_frequency + ((nChan - refChan)*delChan)) * 1.E-6
    mjd = data[calOns].mjd

    tauArray = getTau(mjd, [freqMHzA,freqMHzB])
    ; decompose it - many unused values
    nMJD = n_elements(mjd)
    tauZenithsA = dblarr(nMJD)
    tauZenithsB = tauZenithsA
    for i=0,(nMJD-1) do begin
        tauZenithsA[i] = tauArray[i,i]
        tauZenithsB[i] = tauArray[i,i+nMJD]
    endfor

                                ; if we're going to be keeping
                                ; something, we need an array of data
                                ; containers, one for each integration

    if doKeep then begin
        ; all elements here are undefined
        keepArray = make_array(count+1,value={spectrum_struct})
    endif

   ; for all integrations in a scan; apply gain correction
   doPrint = 0
   nInt2 = round(count / 2) 
   for iInt= 0, count do begin
      setTSky, data[calOns[iInt]], tSkys, doPrint, opacityA, opacityB, tauZenithsA[iInt], tauZenithsB[iInt]
                                ; now create an opacity array for this scan
      factors = tSkys
      dOpacity = (opacityB - opacityA)/float(nChan)
      etaA = 1.0 &  etaB = 1.0
      etaGBT, 1.E-6*data[calOns[0]].reference_frequency, etaA, etaB
      ; compute frequency dependent opacity factor (no eta B dependence yet)
      for i = 0, (nChan -1) do begin $\
        factors[i]=(opacityA+(i*dOpacity))/etaB & endfor
      if (doprint gt 0) then $\
        print,'factors: ',factors[0], factors[nChan-1], opacityA, opacityB, $\
        dOpacity    

      aves = (*(data[calOns[iInt]]).data_ptr + *(data[calOfs[iInt]]).data_ptr)*.5;
      t = data[calOns[iInt]].utc
      ; compute interpolated reference
      a = (dcERef.utc-t)/dT
      b = (t - dcBRef.utc)/dT
      ; interpolate reference spectrum (sky has been removed)
      refs = (a*(*dcBRef.data_ptr)) + (b*(*dcERef.data_ptr))
      tSys  = (a*dcBRef.tsys) + (b*dcERef.tsys)
      *(data[calOns[iInt]]).data_ptr = factors*(((aves * *(dcSCal.data_ptr)) - (tSkys + refs)))
;      *(data[calOns[iInt]]).data_ptr = aves * *(dcSCal.data_ptr)
      middleT = avg( (*(data[calOns[iInt]]).data_ptr)[bChan:eChan])
      rmsT = stddev( (*(data[calOns[iInt]]).data_ptr)[bChan:eChan])
      data[calOns[iInt]].units = 'T_B*'
      ; tsys is composed of source, sky and reference (without sky).
      data[calOns[iInt]].tsys = middleT + tSkys[round(nChan/2)] + dcSCal.tsys
      calcRms = data[calOns[iInt]].tsys/sqrt(data[calOns[iInt]].exposure*data[calOns[iInt]].frequency_resolution)
      set_data_container, data[calOns[iInt]]
      refbeamposition, 1
;      if (iInt eq 0) then show else oshow
      if (doKeep gt 0) then begin
          ; because of the way IDL passes array elements, you
          ; can do data_copy,!g.s[0],keepArray[iInt]
          ; This works.
          data_copy,!g.s[0],spectrumToKeep
          keepArray[iInt] = spectrumToKeep
      endif

;      if ((iInt eq 0) or (iInt eq nInt2)) then begin unfreeze & $\
;        !g.frozen = 0 & show,data[calOns[iInt]] & !g.frozen = 1 & freeze & endif

      ; report
      printf, wlun, scans[iScan], iInt, data[calOns[iInt]].utc, $\
         middleT, (*(data[calOns[iInt]]).data_ptr)[round(nChAn/2)], tSys,  $\
         data[calOns[iInt]].tsys, rmsT, calcRms, $\
         format='(I-5, I-5, F-10.3, x, F-10.4, F-10.4, F-10.4, F-10.4, F-7.3, F-7.3)'
    endfor             

   if doKeep then begin
       putchunk, keepArray
       data_free, keepArray
   endif

;   clean up to avoid memory disaster
   data_free, data

endfor
;!g.frozen = 0 & unfreeze
; close report file
close,wlun

RETURN
END

