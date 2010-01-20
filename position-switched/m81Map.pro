;IDL Procedure to calibrate map scans for a 2x2x degree region around M81
;HISTORY
; 09DEC02 GIL revised for a 2x2 degree map
; 09NOV30 GIL initial version

@compilePipeline.pro

;Load 31 mapping scans from a 2x2 degree region around M81
;From the Unix prompt type
; sdfitsStr =  scans=61:91 /home/archive/science-data/tape-0001/AGBT03B_034_01'
; note the following line will only work in Green Bank, possibly only on colossus
;mapDataName='/home/sandboxes/jmasters/data/AGBT03B_034_01.raw.acs.fits'
;filein,mapDataName

; arguments:
;   0 -- infile
;   1 -- begin-scan
;   2 -- end-scan
;   3 -- sdfits-dir
;   4 -- debug

args = command_line_args()
print,args

infile=args[0]
beginscan=args[1]
endscan=args[2]
sdfitsdir=args[3]
VERBOSE=fix(args[4])

infileOK    = FILE_TEST(infile)
sdfitsdirOK = FILE_TEST(sdfitsdir)

if (VERBOSE gt 2) then print,"infileOK    ",infileOK
if (VERBOSE gt 2) then print,"sdfitsdirOK ",sdfitsdirOK

; if the SDFITS input file doesn't exist, generate it
if ( infileOK ne 1 ) and ( sdfitsdirOK eq 1 ) and ( beginscan lt endscan ) then begin

   if (VERBOSE gt 0) then begin
      print,"SDFITS input file does not exist; generating it"
      print,"  from sdfits-dir input parameter directory and"
      print,"  user-provided begin and end scan numbers"
   endif

   sdfitsstr = '/opt/local/bin/sdfits -fixbadlags -backends=acs' + $
       ' -scans=' + beginscan + ':' + endscan + ' ' + sdfitsdir

   if (VERBOSE gt 0) then print,sdfitsstr

   spawn, sdfitsstr

   infile = FILE_BASENAME(sdfitsdir) + ".raw.acs.fits"
   infileOK = FILE_TEST(infile)

endif

; if the SDFITS input file exists, then use it to create the map
if ( infileOK eq 1 ) then begin
   print,"infile OK"
   exit
   
   mapDataName = infile

   firstScan = fix(beginscan)
   lastScan  = fix(endscan)

   refscans = [firstScan,lastScan]
   allscans = indgen(1+lastScan-firstScan) + firstScan

   if (VERBOSE gt 2) then print,"allscans ",allscans

   scanInfo = scan_info(allscans[0])
   nFeed = scanInfo.n_feeds
   nPol = scanInfo.n_polarizations
   nBand = scanInfo.n_ifs

   ; for a single spectral window
   band = 0
   wait = 1
   calBand, scanInfo, allscans, refscans, band, nFeed, nPol, wait
endif
