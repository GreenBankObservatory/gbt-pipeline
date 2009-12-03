; calibatrateit assumes that the reference X and Y spectra are in
; the global data containers REFX and REFY.
; These containers are used to do a signal-reference/reference calibration
; HISTORY
; 08Dec23 GIL  process 1 polarization at a time
; 08Dec18 GIL  add an update of reference beam position
; 08Aug05 GIL  really do not decimate data
; 08Jul18 GIL  do not decimate data
; 07Jul02 GIL  convert frequency axis
; 07Jun15 GIL  add opacity and etaA correction
; 07May31 KMC  reduce channel number & smooth

pro calScanInt2, aScan, aInt, bandNum, feedNum, polNum, tau

if (not keyword_set( bandNum)) then bandNum = 0
if (not keyword_set( feedNum)) then feedNum = 0
if (not keyword_set( polNum))  then polNum = 0
if (not keyword_set( tau))     then tau = 0.01

REFX=13 & REFY=12; define GBT IDL slots to contain ref scans 

REFI = REFY+polNum; determine slot to use for reference
; reference Scans have estimated Tsys and Air component of Tsys
TSYSI   = !g.s[REFI].tsys        
tAirRef = !g.s[REFI].tambient 

etaA = 0.71 & etaB = 0.90 & opacityFactor = 1.+tau & tempAir = 1.

gettp, aScan, int=aInt, plnum=polNum, ifnum=bandNum, fdnum=feedNum
;    resetFrame, 'HEL'
; compute efficiency and air temperature contribution to Tsys
tsysair, tau, opacityFactor, tempAir
freqMHz = !g.s[0].center_frequency / 1000000.
etaGBT, freqMhz, etaA, etaB
; now start (sig-ref)/ref calibrations
subtract,0,REFI,0
divide,0,REFI
if (etaA le 0.01) then begin
  print, 'Eta A out of range: ', etaA, ', Freq = ',freqMHz
  etaA = 0.71 
endif
scale,TSYSI*opacityFactor/etaA
; subtract out the air contribution to tsys
*(!g.s[0].data_ptr) = *(!g.s[0].data_ptr) - (tempAir-tAirRef)
; update labels for calibration
!g.s[0].CALTYPE = 'T_A*'
!g.s[0].UNITS = 'K'
if (feedNum gt 0) then refbeamposition,1
keep 

RETURN
END





