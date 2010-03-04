;IDL Procedure to calibrate map scans
;HISTORY
; 10JAN23 GIL use toaips to prepare for AIPS processing
; 10JAN21 GIL process Ku band dual beam scans for RaLong Map scan
; 10JAN19 GIL process Ku band dual beam scans for a map
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
scansList = '-scans=14:51'
scansList = '-scans=52:88'
dataDir = '/home/archive/science-data/tape-0028/'
projectName = 'AGBT08B_040_03'
;From the Unix prompt type
sdfitsCmd = sdfitsStr + ' ' + scansList + ' ' + dataDir + projectName
;Tell observer what's being done
print, sdfitsCmd
; or spawn within IDL (uncomment the line below)
;spawn, sdfitsCmd

mapDataName=projectName + '.raw.acs.fits'
filein,mapDataName

;now specify first and last scans, to guide mapping
firstScan=16 & lastScan=49 & refscans = [15,51]
firstScan=54 & lastScan=86 & refscans = [53,88]
;use all map scans as ref scans
allscans = indgen(1+lastScan-firstScan) + firstScan
refscans = allscans
print,allscans

; observation is for one feed and two polarizations
nFeed=2 & nPol=2

; set velocity parameters for selecting relevant channels
vSource = 5.8        ; km/sec - defines center channel to select
vSourceWidth  = 2.0  ; km/sec - defines median filter width
vSourceBegin  = -.2  ; km/sec - defines beginning channel to select
vSourceEnd    = 11.8 ; km/sec - defines endding channel to select

; only process selected lines
for iFeed = 0, 1 do begin $\
for iBand = 0, 3 do begin $\
  gettp,refScans[0], int=0, ifnum=iBand & $\
  calBand, allscans, refscans, iBand, iFeed, nPol & $\
  data_copy, !g.s[0], myDc & $\
;select channels and write the AIPS compatible data 
  toaips,myDc,vSource,vSourceWidth,vSourceBegin,vSourceEnd & endfor & endfor
