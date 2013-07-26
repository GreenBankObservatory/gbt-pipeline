pro average_source_scans, scans, sourcename, do_flag_broad_rfi=do_flag_broad_rfi, naccum=naccum
    compile_opt idl2

    ; average both polarizations for all scans in the given scan list
    ; for the default ifnum=0.
    ; The result is in units of "Jy".
    ; The individual integrations are flagged for broad 
    ; RFI using flag_broad_rfi.  Flagged integrations are not 
    ; usded in the average.  The raw data file is flagged so these
    ; flags are preserved beyond their use in this code.

    ; the final average ends up in buffer 0

    ; make sure the accum buffer is empty
    sclear
    naccum = 0

    keep_ints = keyword_set(do_flag_broad_rfi)

    if keep_ints then begin
       ; set things up for keeping calibrated individual integrations
       ; to disk so that they can be processed by do_flag_broad_rfi

       ; the output (keep) file is going to be used to store temporary
       ; values, remember what the current output file 
       ; is so that it can be restored at the end.
       ; remember what the current output file is - to be replaced at end
       currFileOut = !g.line_fileout_name

       ; this is a hack.  We're going to use two temporary output files.
       ; one to actually write to, the other as a dummy because there is
       ; no way to close the current fileout without opening another one and
       ; reopening the original fileout might be time consuming if the
       ; index is really large.

       ; use systime to get a hopefully unique file name
       tmpFileTag = string(bin_date(systime()),format='(I4,5I2.2)')
       ; the actual files we write to 
       tmpFitsFile = "sPipeTmp_" + tmpFileTag + ".fits"
       tmpIndexFile = "sPipeTmp_" + tmpFileTag + ".index"
       ; the dummy files - which I don't believe are created until
       ; necessary, so this should be painless
       dummyFitsFile = "sPipeDummy_" + tmpFileTag + ".fits"
       dummyIndexFile = "sPipeDummy_" + tmpFileTag + ".index"
    endif

    for ii=0, n_elements(scans)-1 do begin
       if keep_ints then fileout,tmpFitsFile

       si = scan_info(scans[ii])
       if si.procedure eq 'Nod' then begin

           getnod, scans[ii], plnum=0, units='Jy',status=stat0, keepints=keep_ints
           ; accum here if no integration flagging is going to happen
           if stat0 ge 0 and not keep_ints then accum

           getnod, scans[ii], plnum=1, units='Jy',status=stat1, keepints=keep_ints
    
       endif else begin 

           getps, scans[ii], plnum=0, units='Jy',status=stat0, keepints=keep_ints
           ; accum here if no integration flagging is going to happen
           if stat0 ge 0 and not keep_ints then accum

           getps, scans[ii], plnum=1, units='Jy',status=stat1, keepints=keep_ints

       endelse

       ; accum here if no integration flagging is going to happen
       if stat1 ge 0 and not keep_ints then accum

       if keep_ints and (stat0 gt 0 or stat1 ge 0) then begin
          ; something was definitely written to the keep file
          ; status = -1 indicates something went very wrong, e.g.
          ; one of the scans expected for the PS pair was missing
          ; and nothing was written.

          ; Use getchunk to get the data from each polarization
          ; we know that getps had this all in memory - that's how
          ; it works - so no point in overthinking the access here
          ; and worrying about buffering it.  If it's a problem,
          ; getps will need to be modified as well. 
          ; one polariation at a time
          for ipol=0,1 do begin
             thisPol = getchunk(/keep,plnum=ipol)
             ; initialized to 0 - unflagged
             flagged_rec = intarr(n_elements(thisPol))
             flag_broad_rfi, thisPol, scans[ii], sourcename, flagged_rec
                                ; use returned flagged_rec to decide
                                ; which of these integrations are to
                                ; be averaged here
             for iInt=0,n_elements(thisPol)-1 do begin
                if not flagged_rec[iInt] then begin
                   accum, dc=thisPol[iInt]
                endif
             endfor
             data_free, thisPol
          endfor
          ; switch to the dummy file so we can remove the tmp files
          fileout,dummyFitsFile
          file_delete,tmpFitsFile,/allow_nonexistent,/noexpand_path
          file_delete,tmpIndexFile,/allow_nonexistent,/noexpand_path
        endif
    endfor

    ; either this is the ave of the 2 polarizations from the two calls
    ; to getps or it's the ave of all of the individual integrations
    ; ignoring any flags found here.
    ave, count=naccum

    if keep_ints then begin
       ; restore the original keep file
       fileout,currFileOut

       ; this shouldn't be necessary, but just in case
       file_delete,dummyFitsFile,/allow_nonexistent,/noexpand_path
       file_delete,dummyIndexFile,/allow_nonexistent,/noexpand_path
    endif
end

