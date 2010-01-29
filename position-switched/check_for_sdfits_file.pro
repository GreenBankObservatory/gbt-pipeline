pro check_for_sdfits_file,infileOK,sdfitsdirOK,infile,sdfitsdir,beginscan,endscan,VERBOSE
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

  ; if the SDFITS input file exists, then use it to create the map
  if ( infileOK eq 1 ) then begin
     if (VERBOSE gt 2) then print,"infile OK"
  endif else begin
     print,"infile not OK"
     exit
  endelse

  return
end

