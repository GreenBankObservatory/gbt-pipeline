; scaleInt fully calibrates one polarization of a set of map scans
; all integrations
; HISTORY
; 09Nov20 GIL  add bChan, eChan to in and output
; 09Nov19 GIL  add beam offset calculation
; 09Nov17 GIL  clean up the show process
; 09Nov16 GIL  clean up comments
; 09Nov14 GIL  check factors
; 09Nov13 GIL  initial version based scaleScanInt2
; 09Nov12 GIL  further smooth values, remove unused indicies
; 09Nov11 GIL  initial version based on ratioScanInt2
; 09Nov09 GIL  initial version based on calScanInt2

pro scaleInts, scans, iPol, iBand, iFeed, dcSCal, bChan, eChan

   if (not keyword_set( scans)) then begin
      print, 'scaleInts: compute and return tsys/tcal for GBT scans.'
      print, 'The on-off'
      print, 'values must be pre-computed and scaled with scaleRef()'
      print, 'usage: scaleInts, scans, iPol, iBand, iFeed, dcSCal, doKeep'
      print, '      iPol   observation polarization number, range 0 to n-1'
      print, '      iBand  observation band number, range 0 to n-1'
      print, '      iFeed  observation feed number, range 0 to n-1'
      print, '      dcSCal  Average cal-on - cal-off value'
      print, '      doKeep Keep (doKeep>0) the calibrated scans integrations'
      print, 'Output is to a log file and a keep'
      print, '----- Glen Langston, 2009 November 13; glangsto@nrao.edu'
      return
   endif

   if (not keyword_set( iPol)) then iPol = 0
   if (not keyword_set( iBand)) then iBand = 0
   if (not keyword_set( iFeed)) then iFeed = 0

   openw, wlun, 'scaleInts.txt', /append, /get_lun

   etaA = 1.0 &  etaB = 1.0
   for iScan = 0, n_elements( scans) - 1 do begin 
     !g.frozen = 1
     gettp, scans[iScan], int=0, plnum=iPol, ifnum=iBand, fdnum=iFeed
     if (!g.s[0].polarization ne dcSCal.polarization) then begin
        print,'Obs/Cal Pol. miss match: ', !g.s[0].polarization, ' ne ', $\ 
          dcSCal.polarization
        return
     endif
     printf, wlun, '#Scan:', scans[iScan], 'Band:', iBand, 'Feed:', iFeed, $\
       strtrim(!g.s[0].timestamp,2), $\
       format='(A-6, I-5, A-6, I-3, A-6, I-3, A-25)'
     printf, wlun, '#Obj :', !g.s[0].source, !g.s[0].procedure, $\
       !g.s[0].procseqn, '/', !g.s[0].procsize, $\
       format='(A-6, A-12, A-9, X, I-4, A-1, I-4)'
     printf, wlun, '#Ref 0: Tcal, Tsys', dcSCal.mean_tcal, dcSCal.tsys, $\
       !g.s[0].polarization, $\
       format='(A-20, F-8.3, F9.3, X, A-4)'
     tSkys = *!g.s[0].data_ptr  ; prepare for sky correction 

     aScanInfo=scan_info(scans[iScan])
; retrieve counts of different spectra types
     nInt = aScanInfo.n_integrations & nPol = aScanInfo.n_polarizations
     nFeed = aScanInfo.n_feeds       & nIf = aScanInfo.n_ifs
     nChan = aScanInfo.n_channels    & nSample = aScanInfo.n_samplers
; default trimming of channels 
     if (not keyword_set( bchan)) then bChan = 12 * (nChan/1024);
     if (not keyword_set( echan)) then eChan = nChan - (bChan + 1)
     oChan = eChan - bChan + 1       & oChan1 = eChan - bChan

   ; trip off ends of spectra to save some computations of the average
   calMids = (*dcSCal.data_ptr)[bChan:eChan]

                                ; now select all integrations for this
                                ; scan; separate cal on/off and pol A/B
   calOns = getchunk(scan=scans[iScan], count=count, cal="T", $\
                     plnum=iPol, ifnum=iBand, fdnum=iFeed)
   calOfs = getchunk(scan=scans[iScan], count=countOff, cal="F", $\
                     plnum=iPol, ifnum=iBand, fdnum=iFeed)
   if (count le 0) then begin $\
     print,'Error reading scan: ', scans[iScan], ', No integrations' & $\
     return & endif

;   gains = fltarr( count)  ; prepare to collect an array of gains
   count=count-1; correct for 0 based counting
   countOff = countOff - 1
   opacityA = 1.0 & opacityB = 1.0

   ; for all integrations in a scan; apply gain correction
   doPrint = 0
   nInt2 = round(count / 2) 
   sCals = (*dcSCal.data_ptr)[bchan:eChan] ; selecte useful cal values
   nKeep = eChan - bChan
   nKeep16 = round(nKeep/16)
   tsysInds = indgen(2*nKeep16) + nKeep16
   tsysInds[nKeep16:(2*nKeep16-1)] = tsysInds[nKeep16:(2*nKeep16-1)] + $\
     (12*nKeep16)
   for iInt= 0, count do begin
      etaGBT, 1.E-6*calOns[0].observed_frequency, etaA, etaB
      setTSky, calOns[count], tSkys, doPrint, opacityA, opacityB
                                ; now create an opacity array for this scan
      tSkys = tSkys[bChan:eChan]
      factors = tSkys
      ; scale opacities to avoid division in array calculation
      opacityA = 0.5*opacityA/etaB
      opacityB = 0.5*opacityB/etaB
      if (countOff le iInt) then begin
         opacityA = 2.*opacityA
         opacityB = 2.*opacityB
      endif
      dOpacity = (opacityB - opacityA)/float(nChan)
      ; compute frequency dependent opacity factor (no eta B dependence yet)
      for i = 0, oChan1 do begin $\
        factors[i]=(opacityA+((i+bChan)*dOpacity)) & endfor

      if (doprint gt 0) then $\
        print,'factors: ',factors[0], factors[nChan-1], opacityA, opacityB, $\
        dOpacity    

      if (countOff le iInt) then begin
         aves = (*calOns[iInt].data_ptr)[bChan:eChan] + $\
           (*calOfs[iInt].data_ptr)[bChan:eChan] ;
      endif else begin
         aves = (*calOns[iInt].data_ptr)[bChan:eChan];
      endelse
      scales = factors * ((aves * sCals) - tSkys)
      setdcdata, calOns[iInt], scales
      middleT = avg( scales[tsysInds])
      rmsT = stddev( scales[tsysInds])
      calOns[iInt].units = 'T_B*'
      ; tsys is composed of source, sky and reference (without sky).
      calOns[iInt].tsys = middleT + tSkys[round(oChan/2)]
      calOns[iInt].reference_channel = calOns[iInt].reference_channel - bChan
      calcRms = calOns[iInt].tsys/sqrt(calOns[iInt].exposure*calOns[iInt].frequency_resolution)
      set_data_container, calOns[iInt]
      refbeamposition, 1
      keep   ; finally keep the data for mapping

      if ((iInt eq 0) or (iInt eq nInt2)) then begin unfreeze & $\
        !g.frozen = 0 & show,calOns[iInt] & molecule & $\
        !g.frozen = 1 & freeze & endif

      ; report
      printf, wlun, scans[iScan], iInt, calOns[iInt].utc, $\
         middleT, (*calOns[iInt].data_ptr)[round(nChAn/2)], $\
         calOns[iInt].tsys, rmsT, calcRms, $\
         format='(I-5, I-5, F-10.3, x, F-10.4, F-10.4, F-10.4, F-7.3, F-7.3)'
    endfor             

;   clean up to avoid memory disaster
   for i = 0, count do begin data_free, calOns[i] & endfor
   for i = 0, countOff do begin data_free, calOfs[i] & endfor

endfor
!g.frozen = 0 & unfreeze
; close report file
close,wlun

RETURN
END

