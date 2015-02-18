;+
; A function to extract a range of channels from all of the spectra in
; an input SDFITS file and write the resulting spectra out to a second
; SDFITS file.  This also optionally does a boxcar smooth with
; decimation.  The boxcar smoothing happens after the region of
; interest has been extracted.
;
; <p>Any valid data selection arguments can also be given.
; See <a href="../../user/guide/select.html">select</a> for more details.
;
; <p>Uses <a href="../../user/toolbox/dcextract.html">dcextract</a> to extract the sub-spectra 
; and <a href="../../user/toolbox/dcboxcar.html">dcboxcar</a> to do the boxcar smoothing.
; See those reference pages for additional details of these two steps.
;
; <p>The input file must exist and be readable.  The output file must not
; exist or clobber must be set to remove an existing file.  If the
; output file already exists and is a directory it will not be
; removed, even if clobber is set.
;
; <p>Error checking on the startat and endat values happens in
; dcextract.  If that routine returns -1 at any time, this routine
; exits and any already processed data is written to sdfout.
;
; <p><B>Contributed By: Bob Garwood, NRAO-CV</B>
;
; @param sdfin {in}{required}{type=string} The intput FITS file.  This
; must already exist.
; @param sdfout {in}{required}{type=string} The output FITS file.  If
; this file exists then clobber must be set so that the file is
; deleted before being written to.  This routine always writes to an
; empty output file.  The file name must end in '.fits'
; @keyword startat {in}{optional}{type=integer}{default=0} The first
; channel to include in the extracted region (counting from 0).
; @keyword endat {in}{optional}{type=integer} The last channel to
; include in the extracted region (counting from 0).  If not supplied,
; the last channel is used.  endad must be greater than or equal to
; startat.
; @keyword boxwidth {in}{optional}{type=integer} The width of the boxcar,
; in channels, to apply to the data. The data is further reduced when
; this value is greater than 1 by taking every width channels starting
; at channel 0.  Boxcar smoothing happens after any region extraction
; specified by startat and endat have been done.
; @keyword clobber {in}{optional}{type=boolean} When set, if sdfout
; exists, it will first be deleted (including any associated index
; file).
;
; @uses <a href="../../user/toolbox/dcboxcar.html">dcboxcar</a>
; @uses <a href="../../user/toolbox/dcextract.html">dcextract</a>
;-
pro sdextract, sdfin, sdfout, startat=startat, endat=endat, $
               boxwidth=boxwidth, clobber=clobber, $
               _EXTRA=ex
  compile_opt idl2

  ; sdfin and sdfout are required
  if n_elements(sdfin) eq 0 or n_elements(sdfout) eq 0 then begin
     usage,'sdextract'
     return
  endif

  ; sdfin must not equal sdfout
  ; it would still be possible for these to be the same by
  ; using different paths to the same file, but that's harder
  ; to check for uniqueness 
  if sdfin eq sdfout then begin
     message,'input and output file names are the same',/info
     return
  endif

  ; sdfin must exist
  if (file_test(sdfin,/read) ne 1) then begin
     message,string(sdfin,format="(A,' does not exist or is not readable')"),/info
     return
  endif

  ; sdfout must end in .fits
  if strmid(sdfout,4,/reverse_offset) ne ".fits" then begin
     message,"output file name must end in .fits",/info
     return
  endif
  
  ; if sdfout exists, clobber must be set to true
  if (file_test(sdfout) eq 1) then begin
     if not keyword_set(clobber) then begin
        message,string(sdfout, $
                       format="(A,' exists, use /clobber to allow file deletion')"), $
                /info
        return
     endif

     ; /recursive is too dangerous, do not delete directories here
     if (file_test(sdfout,/directory)) then begin
        message,string(sdfout,"(A,' is a directory, it must be removed by hand')"), $
                /info
        return
     endif

     file_delete, sdfout
     if (file_test(sdfout) eq 1) then begin
        message,string(sdfout,"(A,' could not be removed')"),/info
        return
     endif
  endif
  ; must also check on the related index file
  parts=strsplit(sdfout,".",/extract)
  sdfout_index = strjoin(parts[0:n_elements(parts)-2],".")+".index"
  if file_test(sdfout_index) eq 1 then begin
     if not keyword_set(clobber) then begin
        message,string(sdfout_index, $
                       format="(A,' exists (index), use /clobber or remove it')"),$
                /info
        return
     endif
     file_delete, sdfout_index
     if file_test(sdfout_index) eq 1 then begin
        message,string(sdfout_index,"(A, ' could not be removed')"),/info
        return
     endif
  endif

  ; open the file IO objects
  iosdfin = sdfitsin(sdfin)
  if not obj_valid(iosdfin) then begin
     message,"Problems opening input file for reading",/info
     return
  endif
  ; make sure there's something there
  if (not iosdfin->is_data_loaded()) or (iosdfin->get_num_index_rows() eq 0) then begin
     message,'No data found in input file',/info
     return
  endif

  ; no canned routine like sdfitsin to do this
  iosdfout = obj_new('io_sdfits_writer')
  iosdfout->set_index_file_name, sdfout_index
  iosdfout->set_output_file, sdfout

  ; do the data selection
  indx = select_data(iosdfin,_EXTRA=ex)
  nrec = n_elements(indx)

  if nrec eq 0 then begin
     message,'No data was selected.  Nothing to extract or copy.',/info
     obj_destroy, iosdfin
     obj_destroy, iosdfout
     return
  endif
  
  ; some tuning of this might be wise
  nchunk = 50
  count = 0
  while count lt nrec do begin
     nextCount = count + nchunk
     if nextCount gt nrec then nextCount = nrec
     inIndex = indx[count:(nextCount-1)]
     thisChunk = iosdfin->get_spectra(nspec,indicies,index=inIndex)
     count = nextCount
     for i=0,(nspec-1) do begin
        ; first, extract any sub-spectra
        newSpec = dcextract(thisChunk[i],startat,endat)
        ; check for validity
        if size(newSpec,/type) ne 8 then begin
           message,'Problem extracting spectra',/info
           actualCount = count-nextCount+i
           if i gt 0 then begin
              ; write out what's already been extracted into this chunk
              iosdfout->write_spectra, thisChunk[0:(i-1)]
           endif
           if actualCount eq 0 then begin
              print,"No scans were extracted"
           endif else begin
              print,string(indx[0],inIndex[actualCount-1],$
                           format="('Extracted data for ',i2,' through ',i2)")
           endelse
           data_free, thisChunk
           obj_destroy, iosdfin
           obj_destroy, iosdfout
           return
        endif
        ; and any smoothing - don't bother unless the width is > 1
        if keyword_set(boxwidth) then begin
           if boxwidth gt 1 then begin
              ; dcboxcar requires a valid width, but 
              ; there's no way to check that it ran OK, so do it here
              nch = data_valid(newSpec)
              if boxwidth gt nch then begin
                 message,string(nch,format='("boxwidth must be between 1 and ",i)'),$
                         /info

                 ; this is unlikely to have happened after other scans
                 ; have already been processed, just clean up pointers
                 data_free, thisChunk
                 data_free, newSpec
                 obj_destroy, iosdfin
                 obj_destroy, iosdfout
                 return
              endif
              ; this is done in place
              dcboxcar, newSpec, boxwidth, /decimate
           endif
        endif

        ; replace the value in the chunk
        ; the current pointer gets overwritten by the copy, remember it
        oldPtr = thisChunk[i].data_ptr
        ; replace the values, including the pointer
        thisChunk[i] = newSpec
        ; free the old ptr
        if ptr_valid(oldPtr) then ptr_free, oldPtr
     endfor

     ; write the extracted and optionally smoothed data out
     iosdfout->write_spectra, thisChunk

     ; and free up the remaining pointers in this chunk
     data_free, thisChunk

  endwhile

  obj_destroy, iosdfin
  obj_destroy, iosdfout
end
