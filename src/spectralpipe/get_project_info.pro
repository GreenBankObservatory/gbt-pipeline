function get_project_info
  compile_opt idl2
  if nrecords() le 0 then begin
     print,"Nothing seen in the input data file.  Use filein first."
     return,-1
  endif
  ; summarize information about all of the position switch scans in the 
  ; current filein presumably a raw project file
  ; returns -1 on failure, else a structure of this form:
  ; Note that all of the scan numbers here actually exist and 
  ; are all the PROCSEQN==1 scan of an OnOff or OffOn procedure.
  ;                           
  ; {sources:[array of source names],
  ;  s0:{source:sourceName,
  ;      scans:[scanList],
  ;      duplicates:[duplicateScans],
  ;      missing:[missingScans]},
  ;      srctype:sourceType,
  ;  s1:{...}
  ;  through s<N-1>
  ; }
  ; Where N is the number of sources. 
  ;
  ; This summarizes info for each source with at least one 
  ; position switched scan having PROCSEQN=1.  For each
  ; source there is a tag in the main structure named s<n> where
  ; <n> is an integer.  It would have been more convenient to simply
  ; use the source name as the tag name but tag names must follow IDL
  ; variable naming conventions and source names may not.  The sources
  ; field is present to make it easier to get a list of all sources
  ; described by this structure.
  ; For each of the source structure fields, a value of -1 indicates
  ; that there were no scans of that type found for this source.
  ; The scans field contains the array of valid scans (both scans are
  ; present and are not duplicated elsewhere).
  ; The duplicates field contains the list of PROCSEQN=1 scans that 
  ; have any duplicate or where the companion PROCSEQN=2 scan is a
  ; duplcated in this file.  
  ; The missing field is the list of PROCSEQN=1 scans that where the
  ; accompanying PROCSEQN=2 scan was not found.

  ; the index fields we're interested in
  sources=!g.lineio->get_index_values('SOURCE')
  procedure=!g.lineio->get_index_values('PROCEDURE')
  restfreq=!g.lineio->get_index_values('RESTFREQ')
  scans=!g.lineio->get_index_values('SCAN')
  timestamp=!g.lineio->get_index_values('TIMESTAMP')
  procseqn=!g.lineio->get_index_values('PROCSEQN')

  ; It's useful to identify all of the duplicate scans first
  ; they might be associated with any procedure or procseqn or
  ; restfreq so the downstream selections really aren't a help
  ; in finding them.
  
  ; timestamps are sorted already, so this identifies the unique scans
  uniqScanIndices = uniq(timestamp)
  possUniqScans = scans[uniqScanIndices]
  uniqueScans = scans[uniq(possUniqScans,sort(possUniqScans))]
  hasDupScans = 0
  if n_elements(uniqueScans) ne n_elements(possUniqScans) then begin
     ; there are duplicates, find them by sorting
     ; then differencing them and watching for 0s
     hasDupScans = 1
     sortedScans = possUniqScans[sort(possUniqScans)]
     nScans = n_elements(sortedScans)
     diffScans = sortedScans[1:(nScans-1)] - sortedScans[0:(nScans-2)]
     dupScans = sortedScans[where(diffScans eq 0)]
     ; might be more than once, final step
     dupScans = dupScans[uniq(dupScans)]
  endif

  H1restFreqLimits = [1.419e+09, 1.421e+09]
  H2OrestFreqLimits = [22.234080e+09, 22.236080e+09]

  ; do the frequency selection first
  restfreqSel = (restfreq gt H1restFreqLimits[0] and restfreq lt H1restFreqLimits[1]) or (restfreq gt H2OrestFreqLimits[0] and restfreq lt H2OrestFreqLimits[1])
  if total(restfreqSel) eq 0 then begin
     print,'No observations found within the desired rest frequency limits.'
     return,-1
  endif

  psIndx = where((procedure eq 'OnOff' or procedure eq 'OffOn' or procedure eq 'Nod') and restfreqSel, count)
  if count le 0 then begin
     print,'No position switching or Nod data found for the desired rest frequency'
     return,-1
  endif
  psSources = sources[psIndx]
  psScans = scans[psIndx]
  psProcseqn = procseqn[psIndx]
  uniqSources = psSources[uniq(psSources,sort(psSources))]

  result = {sources:uniqSources}

  ; information about each source
  for jj=0,n_elements(uniqSources)-1 do begin
     thisSource = uniqSources[jj]
     firstScans = psScans[where(psSources eq thisSource and psProcseqn eq 1)]
     firstScans = firstScans[uniq(firstScans,sort(firstScans))]
     secondScans = psScans[where(psSources eq thisSource and psProcseqn eq 2)]
     secondScans = secondScans[uniq(secondScans,sort(secondScans))]
     duplicateScans = -1
     missingScans = -1
     scanMask = make_array(n_elements(firstScans),value=1)
     ; look for and remove duplicates from firstScans list
     if hasDupScans then begin
        if n_elements(dupScans) lt n_elements(firstScans) then begin
           for kk=0,n_elements(dupScans)-1 do begin
              thisDup = where(dupScans[kk] eq firstScans)
              if thisDup ge 0 then begin
                 scanMask[thisDup] = 0
                 if duplicateScans[0] eq -1 then begin
                    duplicateScans = dupScans[kk]
                 endif else begin
                    duplicateScans = [duplicateScans,dupScans[kk]]
                 endelse
              endif
           endfor
        endif else begin
           for kk=0,n_elements(firstScans)-1 do begin
              thisDup = where(firstScans[kk] eq dupScans)
              if thisDup ge 0 then begin
                 scanMask[kk] = 0
                 if duplicateScans[0] eq -1 then begin
                    duplicateScans = scanMask[kk]
                 endif else begin
                    duplicateScans = [duplicateScans,dupScans[kk]]
                 endelse
              endif
           endfor
        endelse
     endif
     if duplicateScans[0] ge -1 then begin
        ; some scans were removed
        okIndex = where(scanMask,count)
        if count eq 0 then begin
           ; everything is a duplicate
           firstScans = -1
        endif else begin
           firstScans = firstScans[okIndex]
           scanMask = scanMask[okIndex]
        endelse
     endif
     ; look for second scan
     if firstScans[0] ge 0 then begin
        for ll=0,n_elements(firstScans)-1 do begin
           thisSecond = firstScans[ll]+1
           thisSecondLoc = where(thisSecond eq secondScans,count)
           if count ne 1 then begin
              if count eq 0 then begin
                 ; either way, this scan can't be used
                 scanMask[ll] = 0
                 ; missing second scan
                 if missingScans[0] eq -1 then begin
                    missingScans = thisSecond-1
                 endif else begin
                    missingScans = [missingScans,thisSecond-1]
                 endelse
              endif else begin
                 ; duplicate second scan
                 if duplicateScans[0] eq -1 then begin
                    duplicateScans = thisSecond-1
                 endif else begin
                    duplicateScans = [duplicateScans,thisSecond-1]
                 endelse
              endelse
           endif else begin
              ; make sure the second scan isn't a duplicate elsewhere
              if hasDupScans then begin
                 secDupIndex = where(thisSecond eq dupScans)
                 if secDupIndex[0] ge 0 then begin
                    ; it is
                    scanMask[ll] = 0
                    if duplicateScans[0] eq -1 then begin
                       duplicateScans = thisSecond-1
                    endif else begin
                       duplicateScans = [duplicateScans,thisSecond-1]
                    endelse
                 endif
              endif
           endelse
        endfor
        ; final list of OK scans for this source
        okIndex = where(scanMask,count)
        if count eq 0 then begin
           firstScans = -1
        endif else begin
           firstScans = firstScans[okIndex]
        endelse
     endif
     ; sort and remove duplications in duplcates and missingScans
     if duplicateScans[0] ne -1 then duplicateScans = duplicateScans[uniq(duplicateScans,sort(duplicateScans))]
     if missingScans[0] ne -1 then missingScans = missingScans[uniq(missingScans,sort(missingScans))]
     ; and assemble the structure for this source
     if (restfreq[0] gt H1restFreqLimits[0] and restfreq[0] lt H1restFreqLimits[1]) then begin
         sourceType='HI'
     endif else begin
         if (restfreq[0] gt H2OrestFreqLimits[0] and restfreq[0] lt H2OrestFreqLimits[1]) then begin
             sourceType='H2O'
         endif
     endelse
     sourceStruct = {scans:firstScans, duplicates:duplicateScans,missing:missingScans,source:thisSource,srctype:sourceType}
     ; add to result
                                ; it would have been nice to use the
                                ; source name as the tag name but tag
                                ; naming rules are more restrictive
                                ; than source naming rule so just do
                                ; this
     tagName = "s"+strtrim(string(jj),2)
     result = create_struct(result,tagName,sourceStruct)
  endfor
  return, result
end
