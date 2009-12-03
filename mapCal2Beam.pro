; IDL proceedure to process TMC Ku band observation and export data 
; for further processing in AIPS
; HISTORY
; 08Dec23 GIL process one polarization at a time
; 08Dec18 GIL compute second beam offset
; 08Aug05 GIL modify for HC5N X band map
; 08Aug04 GIL modify for HC5N Ku band map
; 08Jul18 GIL modify galaxy map for X band
; 08Jun08 KMC modifies for N2403 group
; 07Jul10 KMC added startM81.pro to the beginning so it's all one script
; 07May31 KMC's version, to reduce channel number


pro mapCal2Beam, mapDataName, scans, calScans, bandNum, tau

  on_error,2
  if (not keyword_set(scans)) then begin
    print,'mapCal2Beam: calibrate both beams and polarizations of 2 beam obs'
    print,'usage: mapCal2Beam, mapDataName, scans, calScans, bandNum, tau'
    print,'scans    list of scans to calibrate'
    print,'calScans list of scans to generate the reference spectra'
    print,'bandNum  frequency band of spectrometer to calibrate'
    print,'tau      estimated atmospheric attenuation during the observation'
    print,'Glen Langston, 2008 December 24'
  endif

  if (not keyword_set( bandNum)) then bandNum = 0
  if (not keyword_set( tau)) then tau = 0.01
  if (not keyword_set( calScans)) then calScans = scans

REFX=13 & REFY=12  ; define GBT IDL slots to contain ref scans
OUTX=15 & OUTY=14  ; define slot with last calibrated spectra
IX = 1  & IY = 0   ; define polarization numbers

; for both feeds of 2 beam receiver
  for feedNum = 0, 1 do begin
; Now get the first scan
;open file for reading raw data
    filein,mapDataName

    nScans = n_elements( scans)
    startScan = scans[0]  & stopscan = scans[nScans-1]

; this script assumes all map scans have the same shape
    j=scan_info(startScan)
    nInts = j.n_integrations
    intCenters = [0, (nInts-1)]
    nRadius = nInts/10
    if (nRadius lt 2) then nRadius = 2
    if (nRadius gt nInts) then nRadius = nInts
    intRadia   = [nRadius, nRadius]

; use first scan to get source info and band center frequency
    gettp, startScan, ifnum=bandNum, fdnum=feedNum
    bandCenter =  strtrim( string( round(!g.s[0].center_frequency*1E-6)),2)
    object = strtrim( !g.s[0].source, 2)
    header
    bandName = bandCenter
    sigFileName = 'sig-' + object + '-' + $\
              strtrim( string( round(STARTSCAN)),2) + $\
              '-' + strtrim( string( round( STOPSCAN)),2) + '-' + $\
              bandCenter + '-' + $\
              strtrim( string( round( feedNum)),2) + '.fits'

    refFileName = 'ref-' + object + '-' + bandCenter + '-' + $\
              strtrim( string( round(feedNum)),2) + '.fits'
    fileout,refFileName

; compute reference scans for a feed and both polarizations
    referenceBeam2,scans,calScans,intCenters,intRadia,bandNum,feedNum, IX,tau
    referenceBeam2,scans,calScans,intCenters,intRadia,bandNum,feedNum, IY,tau

    print,'Reference scans are in file:', refFileName

; prepare to write 
   fileout, sigFileName
   filein, refFileName
   print, 'Writing calibrated data to: ', sigFileName
   print, 'Showing raw spectra for band,feed:', bandNum, feedNum

   !g.frozen=0 & setplotterautoupdate
   show,REFX & oshow, REFY
   !g.frozen=1 & setplotterautoupdate

   ;produce reference for (Signal-Ref)/Ref Calibration
   filein,  mapDataName
   fileout, sigFileName
   calibrateBeam2, scans, bandNum, feedNum, IX, tau
   calibrateBeam2, scans, bandNum, feedNum, IY, tau
endfor 

return
end
