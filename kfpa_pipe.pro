; IDL proceedure to process TMC Ku band observation and export data 
; for further processing in AIPS
; HISTORY
; 08Dec24 GIL process both beams and and polarizations of a 2 beam obs

.compile etaGBT.pro
.compile opacity.pro
.compile natm.pro
.compile tatm.pro
.compile calScanInt2.pro
.compile referenceBeam2.pro
.compile calibrateBeam2.pro
.compile mapCal2Beam.pro
.compile refbeamposition.pro
.compile tsysair.pro

STARTSCAN=16 & STOPSCAN=49
CALSCANa=16  & CALSCANb=49
calScans = [ CALSCANa, CALSCANb]
scans = indgen( STOPSCAN-STARTSCAN+1) + STARTSCAN

mapDataName='tmcKuMaps.raw.acs.fits'

bandNum = 0

REFX=13 & REFY=12  ; define GBT IDL slots to contain ref scans
OUTX=15 & OUTY=14  ; define slot with last calibrated spectra
IX = 1  & IY = 0   ; define polarization numbers

;estimate atmospheric opacity for observations
tau = 0.02

mapCal2Beam, mapDataName, scans, calScans, bandNum, tau

STARTSCAN=54 & STOPSCAN=86
CALSCANa=54  & CALSCANb=86
calScans = [ CALSCANa, CALSCANb]
scans = indgen( STOPSCAN-STARTSCAN+1) + STARTSCAN

mapCal2Beam, mapDataName, scans, calScans, bandNum, tau



