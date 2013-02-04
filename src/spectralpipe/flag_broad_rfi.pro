
pro flag_broad_rfi, scans, sourcename
    compile_opt idl2

    ; check every integration on the source for
    ;   wavy RFI using a FFT to find low frequency components
    ; for each scan pair

    ; this also averages every non-flagged integration 
    ; and puts the result into buffer 0
    ; clear the accum buffer at the start
    sclear

    ; remember what the current output file is - to be replaced at end
    currFileOut = !g.line_fileout_name

    ; this is a hack.  We're going to use two temporary output files.
    ; one to actually write to, the other as a dummy because there is
    ; way to close the current fileout without opening another one and
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
   
    for ii=0, n_elements(scans)-1 do begin
       ; use getps to process and keep each integrations results
       ; integrations are kept to the current keep file
       fileout,tmpFitsFile
       getps,scans[ii],plnum=0,units='Jy',/keepints,status=stat0
       getps,scans[ii],plnum=1,units='Jy',/keepints,status=stat1

       if stat0 ge 0 or stat1 ge 0 then begin
          ; something was definitely written
          ; status = -1 indicates something went wrong, e.g.
          ; one of the scans expected for the PS pair was missing
          ; and nothing was written.
        
          ; Use getchunk to get the data from each polarization
          ; we know that getps had this all in memory - that's how
          ; it works - so no point in overthinking the access here
          ; and worrying about buffering it.  If it's a problem,
          ; getps will need to be modified as well.
         
          for ipol=0,1 do begin
             thisPol = getchunk(/keep,plnum=ipol)
             ; each element of thisPol corresponds to the calibrated
             ; data container for that integration number at 
             ; polarization ipol.  
             for jj=0,n_elements(thisPol)-1 do begin
                fft_flag, thisPol[jj], scans[ii], jj, sourcename, isflagged=isflagged
                if not isflagged then accum,dc=thisPol[jj]
             endfor
             data_free, thisPol
          endfor
       endif

       ; switch to the dummy file so we can remove the tmp files
       fileout,dummyFitsFile
       file_delete,tmpFitsFile,/allow_nonexistent
       file_delete,tmpIndexFile,/allow_nonexistent
    endfor

    ave

    ; restore the original keep file
    fileout,currFileOut

    ; this shouldn't be necessary, but just in case
    file_delete,dummyFitsFile,/allow_nonexistent
    file_delete,dummyIndexFile,/allow_nonexistent
end

