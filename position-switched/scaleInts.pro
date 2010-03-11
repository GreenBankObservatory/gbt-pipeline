; scaleInt fully calibrates one polarization of a set of map scans
; all integrations
; HISTORY
; 10Jan22 GIL  transfere rest frequency from reference
; 09Dec10 GIL  deal with all cal off or all cal on signals
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
     if (eChan gt nChan) then eChan = nChan
     if (bChan lt 0) then bChan = 0
     oChan = eChan - bChan + 1       & oChan1 = eChan - bChan

   ; trim off ends of spectra to save some computations of the average
   calMids = (*dcSCal.data_ptr)[bChan:eChan]

                                ; now select all integrations for this
                                ; scan; separate cal on/off and pol A/B
   ; its cheaper to get both in one call and use a mask here
   data = getchunk(scan=scans[iScan], count=count, $\
                   plnum=iPol, ifnum=iBand, fdnum=iFeed)
   if (count le 0) then begin $\
     print,'Error reading scan: ', scans[iScan], ', No integrations' & $\
     return & endif

   calOns = where(data.cal_state eq 1, countOn)
   calOfs = where(data.cal_state eq 0, countOff)

   ; track whether there are is only cal Off data in this scan
   if (countOn le 0) then onlyOff = 1 else onlyOff = 0

;   gains = fltarr( count)  ; prepare to collect an array of gains
   countOn=countOn-1; correct for 0 based counting
   countOff = countOff - 1
   opacityA = 1.0 & opacityB = 1.0

   ; get zenith opacities at the band edges to be passed to setTSky
   ; cheaper to bundle getTau calls here in one call rather than 
   ; in setTSky as before.
   refChan = data[calOfs].reference_channel
   nChan = n_elements(*(data[calOfs[0]]).data_ptr)
   delChan = data[calOfs].frequency_interval
   freqMHzA = (data[calOfs].observed_frequency + ((0-refChan)*delChan)) * 1.E-6
   freqMHzB = (data[calOfs].observed_frequency + ((nChan - refChan)*delChan)) * 1.E-6
   mjd = data[calOfs].mjd

   tauArray = getTau(mjd, [freqMHzA,freqMHzB])
   ; decompose it - many unused values
   nMJD = n_elements(mjd)
   tauZenithsA = dblarr(nMJD)
   tauZenithsB = tauZenithsA
   for i=0,(nMJD-1) do begin
      tauZenithsA[i] = tauArray[i,i]
      tauZenithsB[i] = tauArray[i,i+nMJD]
   endfor

                                ; create an array of data containers
                                ; to hold the results, one for each
                                ; integration
   keepArray = make_array(countOff+1,value={spectrum_struct})

   ; for all integrations in a scan; apply gain correction
   doPrint = 0
   ; use the larger number of integrations (cal On or cal Off)
   count = countOff
   ; handle rare occurance of only cal On data
   if (countOn gt countOff) then count = countOn
   nInt2 = round(count / 2) 
   sCals = (*dcSCal.data_ptr)[bchan:eChan] ; selecte useful cal values
   nKeep = eChan - bChan
   nKeep16 = round(nKeep/16)
   ; create array of indexs for computing RMS and TSYS
   tsysInds = indgen(2*nKeep16) + nKeep16
   tsysInds[nKeep16:(2*nKeep16-1)] = tsysInds[nKeep16:(2*nKeep16-1)] + $\
     (12*nKeep16)
   ; need the observing info to compute etaA and etaB
   etaGBT, 1.E-6*dcSCal.observed_frequency, etaA, etaB
                                ; for all integrations, get average
                                ; (or cal Off) values and scale to T_B
   for iInt= 0, countOff do begin
      setTSky, data[calOfs[iInt]], tSkys, doPrint, opacityA, opacityB, tauZenithsA[iInt], tauZenithsB[iInt]
                                ; now create linear opacity array for this scan
      tSkys = tSkys[bChan:eChan]; work only with output channels
      factors = tSkys
      ; scale opacities to avoid division in array calculation
      if (onlyOff) then begin
         opacityA = opacityA/etaB
         opacityB = opacityB/etaB
      endif else begin
         ; else both cal ON and cal Off data, average (below)
         opacityA = 0.5*opacityA/etaB
         opacityB = 0.5*opacityB/etaB
      endelse

      dOpacity = (opacityB - opacityA)/float(nChan)
      ; linear interpolate frequency dependent opacity (no etaB dependence yet)
      for i = 0, oChan1 do begin $\
        factors[i]=(opacityA+((i+bChan)*dOpacity)) & endfor

      if (doprint gt 0) then $\
        print,'factors: ',factors[0], factors[nChan-1], opacityA, opacityB, $\
        dOpacity    

      ; if both cal On and Cal Off data, then just average 
      if (onlyOff eq 0) then begin
         aves = (*(data[calOns[iInt]]).data_ptr)[bChan:eChan] + $\
           (*(data[calOfs[iInt]]).data_ptr)[bChan:eChan];
         data[calOfs[iInt]].exposure = data[calOfs[iInt]].exposure + $\
           data[calOns[iInt]].exposure
      endif else begin
         aves = (*(data[calOfs[iInt]]).data_ptr)[bChan:eChan]
      endelse
      scales = factors * ((aves * sCals) - tSkys)
      setdcdata, data[calOfs[iInt]], scales
      middleT = avg( scales[tsysInds])
      rmsT = stddev( scales[tsysInds])
      data[calOfs[iInt]].units = 'TB*'
      ; tsys is composed of source, sky and reference (without sky).
      data[calOfs[iInt]].tsys = middleT + tSkys[round(oChan/2)]
      data[calOfs[iInt]].reference_channel = data[calOfs[iInt]].reference_channel - bChan
      calcRms = data[calOfs[iInt]].tsys/sqrt(data[calOfs[iInt]].exposure*data[calOfs[iInt]].frequency_resolution)
      data[calOfs[iInt]].line_rest_frequency = dcSCal.line_rest_frequency
      set_data_container, data[calOfs[iInt]]
      refbeamposition, 1
      ; because of the way IDL passes array elements you can't use
      ; data copy as: data_copy,!g.s[0],keepArray[iInt]
      ; But this works
      spectrumToKeep = 0 ; ensure that any previous pointer here isn't reused incorrectly
      data_copy,!g.s[0],spectrumToKeep
      keepArray[iInt] = spectrumToKeep ; this pointer gets deleted later

      if !g.has_display then begin
         if ((iInt eq 0) or (iInt eq nInt2)) then begin 
            show,data[calOfs[iInt]]
            molecule
         endif
      endif

      ; report
      printf, wlun, scans[iScan], iInt, data[calOfs[iInt]].utc, $\
         middleT, (*(data[calOfs[iInt]]).data_ptr)[round(oChan/2)], $\
         data[calOfs[iInt]].tsys, rmsT, calcRms, $\
         format='(I-5, I-5, F-10.3, x, F-10.4, F-10.4, F-10.4, F-7.3, F-7.3)'
    endfor             

   ; actually write the keep array to disk
   putchunk, keepArray
   ; and delete all of those pointers
   data_free, keepArray

;   clean up to avoid memory disaster
    data_free, data

 endfor

; close report file
free_lun,wlun

RETURN
END

