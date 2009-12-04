;IDL Procedure to calibrate map scans for a 2x2x degree region around M81
;HISTORY
; 09DEC02 GIL revised for a 2x2 degree map
; 09NOV30 GIL initial version

@compilePipeline.pro

;Load 31 mapping scans from a 2x2 degree region around M81
;From the Unix prompt type
sdfitsStr = '/opt/local/bin/sdfits -fixbadlags -backends=acs scans=61:91 /home/archive/science-data/tape-0001/AGBT03B_034_01'

; or spawn within IDL (uncomment the line below)
; spawn, sdfitsStr

mapDataName='AGBT03B_034_01.raw.acs.fits'
filein,mapDataName

firstScan=61
lastScan=91
refscans = [firstScan,lastScan]
allscans = indgen(1+lastScan-firstScan) + firstScan
print,allscans

; observation is for one feed and two polarizations
nFeed=1 & nPol=2

for iBand = 0, 0 do begin $\
  gettp,refScans[0], int=0, ifnum=iBand & $\
  calBand, allscans, refscans, iBand, nFeed, nPol & endfor 

