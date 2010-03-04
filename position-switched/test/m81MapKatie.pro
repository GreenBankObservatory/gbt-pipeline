;IDL Procedure to calibrate map scans for a 2x2x degree region around M81
;HISTORY
; 09DEC17 GIL revised for a 2x2 degree map
; 09DEC02 GIL revised for a 2x2 degree map
; 09NOV30 GIL initial version

@compilePipeline.pro

;Load 31 mapping scans from a 2x2 degree region around M81
;From the Unix prompt type
firstScan=73
lastScan=93 
scanStr = '-scans=' + strtrim(string(firstScan),2) + ':' + strtrim(string(lastScan),2)
sdfitsStr = '/opt/local/bin/sdfits -fixbadlags -backends=acs '
dataDir = '/home/archive/science-data/tape-0030/'
projectId = 'AGBT09A_046_13'
sdfitsCmd = sdfitsStr + scanStr + ' ' + dataDir+projectId

; or spawn within IDL (uncomment the line below)
;spawn, sdfitsCmd

mapDataName=projectId + '.raw.acs.fits'
filein,mapDataName

refscans = [firstScan,lastScan]
allscans = indgen(1+lastScan-firstScan) + firstScan
refscans = allscans
print,allscans

; observation is for one feed and two polarizations
nFeed=1 & nPol=2 
; do not wait for observer to check the calibration 
doWait = 0

for iBand = 0, 0 do begin $\
  gettp,refScans[0], int=0, ifnum=iBand & $\
  calBand, allscans, refscans, iBand, nFeed, nPol & endfor 

idlToSdfitsStr = '/users/glangsto/bin/idlToSdfits '
; average 32 channels and compute the RMS based on selected channels
parameters = '-a 32 -b 100:200 -w 200'

;convert the file to aips input file format
idlToSdfitsCmd = idlToSdfitsStr + parameters + ' ' + !g.line_fileout_name

;convert calibrated data for input to AIPS
spawn, idlToSdfitsCmd
