pro check_for_sdfits_file,infileOK,sdfitsdirOK,infile,beginscan,endscan,VERBOSE
  ; if the SDFITS input file doesn't exist, generate it
  if ( infileOK ne 1 ) and ( sdfitsdirOK eq 1 ) and ( beginscan lt endscan ) then begin

     if (VERBOSE gt 0) then print,"SDFITS input file does not exist; generating it from sdfits-dir input parameter directory and user-provided begin and end scan numbers"

     sdfitsstr = '/opt/local/bin/sdfits -fixbadlags -backends=acs' + $
         ' -scans=' + beginscan + ':' + endscan + ' ' + sdfitsdir

     if (VERBOSE gt 0) then print,sdfitsstr

     spawn, sdfitsstr

     infile = FILE_BASENAME(sdfitsdir) + ".raw.acs.fits"
     infileOK = FILE_TEST(infile)
  endif
  return
end

pro domap,infileOK,sdfitsdirOK,infile,beginscan,endscan,VERBOSE
; if the SDFITS input file exists, then use it to create the map
if ( infileOK eq 1 ) then begin
   
   if (VERBOSE gt 2) then print,"infile OK"
   
   firstScan = fix(beginscan)
   lastScan  = fix(endscan)

   refscans = [firstScan,lastScan]
   allscans = indgen(1+lastScan-firstScan) + firstScan

   if (VERBOSE gt 2) then print,"allscans ",allscans

   ; read in the input file
   filein,infile

   scanInfo = scan_info(allscans[0])
   nFeed = scanInfo.n_feeds
   nPol = scanInfo.n_polarizations
   nBand = scanInfo.n_ifs

   ; for a single spectral window
   band = 0
   wait = 0 ; optionally wait for user input to continue cal
   calBand, scanInfo, allscans, refscans, band, nFeed, nPol, wait
   return
endif
end
