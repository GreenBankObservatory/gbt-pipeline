;IDL Procedure to calibrate map scans
;HISTORY
; 10JAN24 GIL reduces source width to reduce number of output channels
; 10JAN23 GIL use toaips to prepare data for AIPS imaging
; 10JAN22 GIL add code for selecting line emitting region
; 09DEC16 GIL break up sdfits call for clarity
; 09DEC15 GIL revised for tmc map
; 09DEC02 GIL revised for a 2x2 degree map
; 09NOV30 GIL initial version

@compilePipeline.pro

;The data can be loaded from inside idl, so that when the data are
;transformed to an sdfits file, they will be immediately calibrated
sdfitsStr = '/opt/local/bin/sdfits -fixbadlags -backends=acs'
;specify scan list, if all spectra are needed
scansList = ' '
;else specify only the desired scans
scansList = '-scans=49:83'
dataDir = '/home/archive/science-data/tape-0028/'
dataDir = '/home/gbtdata/'
projectName = 'T_09NOV27'
;From the Unix prompt type
sdfitsCmd = sdfitsStr + ' ' + scansList + ' ' + dataDir + projectName
;Tell observer what's being done
print, sdfitsCmd
; or spawn within IDL (uncomment the line below)
spawn, sdfitsCmd

mapDataName=projectName + '.raw.acs.fits'
filein,mapDataName

;now specify first and last scans, to guide mapping
firstScan=51
lastScan=82
refscans = [50,83]
;use all map scans as ref scans
allscans = indgen(1+lastScan-firstScan) + firstScan
refscans = allscans
print,allscans

; observation is for two feeds and two polarizations
nPol=2

; set velocity parameters for selecting relevant channels
vSource = 10.0        ; km/sec - defines center channel to select
vSourceWidth  =   5.0 ; km/sec - defines median filter width
vSourceBegin  = -20.0 ; km/sec - defines beginning channel to select
vSourceEnd    = 40.0            ; km/sec - defines endding channel to select
; The rest frequency frequencies guide the selection of data to be
; converted to AIPS format.   If no rest frequencies are provided,
; The rest frequencies in the observation header are used.
;            NH3 1-1 and 2-2, H2O,         CH3OH+CCCS,   NH3 3-3
restFreqHzs = [ 23694.5060D6, 22235.120D6, 23121.024D6,  23870.1296D6]
;below the line rest frequency for each band is set.
;There are many-many NH3 lines, so to set the velocity the strong line 
;must be identified.  

for iFeed = 0, 1 do begin $\
for iBand = 0, 3 do begin $\
  gettp,refScans[0], int=0, ifnum=iBand & $\
  calBand, allscans, refscans, iBand, iFeed, nPol & $\
  data_copy, !g.s[0], myDc & $\
;change rest frequency for computation of velocities in AIPS
  myDc.line_rest_frequency = restFreqHzs[iBand] & $\
;select channels and write the AIPS compatible data 
  toaips,myDc,vSource,vSourceWidth,vSourceBegin,vSourceEnd & endfor&endfor


