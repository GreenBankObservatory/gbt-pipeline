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
; note the following line will only work in Green Bank, possibly only on colossus
;mapDataName='/home/sandboxes/jmasters/data/AGBT03B_034_01.raw.acs.fits'
;filein,mapDataName

args = command_line_args()

mapDataName = args[0]

;firstScan=61
;lastScan=91

firstScan = fix(args[1])
lastScan  = fix(args[2])

refscans = [firstScan,lastScan]
allscans = indgen(1+lastScan-firstScan) + firstScan
;print,allscans

scanInfo = scan_info(allscans[0])
nFeed = scanInfo.n_feeds
nPol = scanInfo.n_polarizations
nBand = scanInfo.n_ifs

; for a single spectral window
band = 0
wait = 1
calBand, scanInfo, allscans, refscans, band, nFeed, nPol, wait
