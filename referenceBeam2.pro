; IDL proceedure to generate a reference spectrum for Sig-Ref/Ref
; calibration.  Defines 2 reference locations for 
; HISTORY
; 08Aug12 Add feedNum
; 08Aug08 Check revise for Ku band 4 frequencies, 2 polarizations, 2 beams
; 08Aug07 Check reference spectrum for zeros and remove if present
; 08Aug05 GIL revise for X band observations of 4 spectral lines
; 08Jul18 Revise to select the important spectral line
; 07May31 KMC's version, to reduce channel number & smooth
; 07MAY30 GIL add comments
; 05MAY01 GIL initial version

pro referenceBeam2, scans, calScans, intCenters, intRadia, bandNum, feedNum, polNum, tau

if (not keyword_set( calScans)) then begin
   print,'referenceBeam2, dataScans, calScans, intCenters, intRadia, outFileName, bandNum, feedNum'
   print,'Reference scan for input to mapping calibration'
   print,'scans          List of all scans to be mapped'
   print,'calScans       Calibration scan list (required)'
   print,'intCenters     Center integration to be used for computing reference'
   print,'intRadia       Number of integrations from center to be used for ref'
   print,'outfileName    Output file containing reference spectra'
   print,'bandNum        Index to spectral band for processing'
   print,'feedNum        Index to feed for processing'
   print,'polNum         polarization number to process'
   return
endif

; default to first band of first feed
if (not keyword_set( bandNum)) then bandNum = 0
if (not keyword_set( feedNum)) then feedNum = 0
if (not keyword_set( tau))     then tau = 0.009

if (not keyword_set( outFileName)) then outFileName = 'outname.fits'
print, 'Processing Band, ', bandNum, ' Feed = ', feedNum, ' Pol = ', polNum

REFX=13 & REFY=12                    ; buffers for refernce spectra
OUTX=15 & OUTY=14                    ; buffers for refernce spectra
IX=1    & IY=0                       ; polarization indicies
MINK = .001                          ; minimum valid intensity in reference 
NMEDIAN=51
opacityFactor = 1.+ tau & tempAir = 0.D0
ave ; clear any accumlated scans

; create variables that are later reset during processing 
j=scan_info(scans[0])
h=j.n_integrations
h2=round(j.n_integrations/2)
nScans = n_elements( scans)
nCalScans = n_elements( calScans)
nAccum = 0.D0;
tempAirSum = 0.D0;
print, 'Starting reference scan accumulation for polarization: ', polNum
print, calscans, intCenters, intRadia

for cScan = 0, (nCalScans-1) do begin
  calScan = calScans[cScan]
  for iScan = 0, (nScans-1) do begin
    aScan = scans[iScan]
    dScan = abs(aScan-calScan)
    if (dScan lt intRadia[cScan]) then begin
      j=scan_info( aScan)
      nInts = j.n_integrations
      startInt = intCenters[cScan] - intRadia[cScan]
      stopInt  = intCenters[cScan] + intRadia[cScan]
      if (startInt lt 0) then startInt = 0
      if (stopInt gt (nInts-1)) then stopInt = nInts-1
;     now read and sum all reference ints     
      for iInt = startInt, stopInt do begin
;        print, aScan, iInt
        gettp, aScan, int=iInt, plnum=polNum, ifnum=bandNum, fdnum=feedNum
        tsysair, tau, opacityFactor, tempAir
        tempAirSum = tempAir + tempAirSum
        nAccum = nAccum + 1.D0
        accum
      endfor ; end for all integrations 
    endif ;  if scan is near a cal scan 
  endfor ;end for all scans
endfor ; end for all cal scans

ave & show
!g.s[0].tambient=tempAirSum/nAccum
; save spectrum before median filtering
copy,0,OUTY+polNum
data_copy,!g.s[0],spectrum
; transfere spectrum to a work array
dataValues=getdcdata(spectrum)
nchan = n_elements( dataValues)
medianValues = dataValues
print, 'Filter ',nchan,' Channels with median half width ',NMEDIAN
; check reference for values too small for good divid.
for i = 0,(nchan-1) do begin & $\
  if (dataValues[i] le MINK) then dataValues[i] = MINK & $\
endfor
endI = nchan - NMEDIAN - 1
for i = NMEDIAN,endI do begin & $\
  medianValues[i]=median(dataValues[(i-NMEDIAN):(i+NMEDIAN)]) & $\
endfor
; transfer data back to spectrum
setdcdata, spectrum, medianValues
set_data_container, spectrum, buffer=0, /ignore_line
show
keep
copy,0,REFY+polNum
; clean up work values
data_free,spectrum

RETURN
END





