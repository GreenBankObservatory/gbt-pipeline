; calibatrateit assumes that the reference X and Y spectra are in
; the global data containers REFX and REFY.
; These containers are used to do a signal-reference/reference calibration
; HISTORY
; 08Dec21 GIL  input an array of scans
; 08Dec21 GIL  input an array of scans
; 08Aug12 GIL  add feed number
; 08Aug08 GIL  revised for Ku band again
; 08Aug05 GIL  improved TMC x band version
; 08Jul17 GIL  TMC x band version
; 07Jul09 KMC  use one reference frame for all data
; 07Jul06 GIL  shift all data to same channels
; 07Jul02 GIL  convert frequency axis
; 07Jun15 GIL  add opacity and etaA correction
; 07May31 KMC  reduce channel number & smooth

pro calibrateBeam2, scans, bandNum, feedNum, polNum, tau

  on_error,2
  if (not keyword_set(scans)) then begin
    print,'calibrateBeam2: calibrate a spectral line map: Tref*(sig-ref)/ref'
    print,'usage: calibrateBeam2, scans, bandNum, feedNum, polNum, tau'
    print,'scans   list of scans to calibrate'
    print,'bandNum spectrometer frequency band to calibrate'
    print,'feedNum receiver feed (beam) to calibrate'
    print,'polNum  polarization (ie 0 or 1) to calibrate'
    print,'tau     estimated atmospheric attenuation during the observation'
    print,'calibrateBeam2 assumes previously computed reference scans are'
    print,'already stored in GBTIDL spectral slots 12 and 13.'
    print,'Use referenceBeam2 to compute these raw spectra'
    print,'Glen Langston, 2008 December 21'
  endif

  if (not keyword_set( bandNum)) then bandNum = 0
  if (not keyword_set( feedNum)) then feedNum = 0
  if (not keyword_set( polNum))  then polNum = 0
  if (not keyword_set( tau)) then tau = 0.01

  nScans = n_elements( scans)
  startScan = scans[0]  & stopscan = scans[nScans-1]
;  print, 'Scans :',startscan,stopscan,',band=',bandNum, ', feed=',feedNum
 
  REFX=13 & REFY=12         ; define GBT IDL slots to contain ref scans

  !g.frozen = 0 & setplotterautoupdate
  freey & sety, -1., 4. 
  show,(REFY+polNum)
  !g.frozen = 1 & setplotterautoupdate

;defines reference position, velocity, and reference frame
a={accum_struct}
;dcaccum, a, dcDREF
;vFrame = dcDREF.FRAME_VELOCITY
;print,'Reference v Frame: ',dcDREF.FRAME_VELOCITY
;!g.frozen = 1 & setplotterautoupdate

freey & sety, -5., 5. 
FOR iScan = 0, (nScans-1) do BEGIN
  aScan = scans[iScan];
  j=scan_info(aScan)
  h=j.n_integrations
  h2 = h/2
  print, 'Scan: ',aScan,' Number Integrations: ', h
  FOR d = 0, h-1 do BEGIN
    if ((d eq 0) or (d eq h2)) then !g.frozen = 0 & setplotterautoupdate
    calScanInt2, aScan, d, bandNum, feedNum, polNum, tau
    if ((d eq 0) or (d eq h2)) then !g.frozen = 1 & setplotterautoupdate
  ENDFOR

  ; free up display and show last calibration for each scan
  !g.frozen = 0 & setplotterautoupdate & show
  
ENDFOR

RETURN
END





