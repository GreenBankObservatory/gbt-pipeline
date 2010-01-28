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
if (VERBOSE gt 2) then print,args

infile=args[0]
beginscan=args[1]
endscan=args[2]
sdfitsdir=args[3]
VERBOSE=fix(args[4])

infileOK    = FILE_TEST(infile)
sdfitsdirOK = FILE_TEST(sdfitsdir)

if (VERBOSE gt 2) then print,"infileOK    ",infileOK
if (VERBOSE gt 2) then print,"sdfitsdirOK ",sdfitsdirOK

check_for_sdfits_file,infileOK,sdfitsdirOK,infile,beginscan,endscan,VERBOSE
domap,infileOK,sdfitsdirOK,infile,beginscan,endscan,VERBOSE
