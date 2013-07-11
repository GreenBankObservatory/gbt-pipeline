; This spectralpipe procedure is meant to process GBT spectral line data
; stored in the SDFITS format.  For each source in the input file, a
; calibrated SDFITS file with a single spectrum is produced.  Also, there
; is a png plot of the spectrum with useful metadata displayed in the
; header.  The spectralpipe procedure is run from a GBTIDL command line
; with a single input paramter, the uncalibrated SDFITS filename.
pro spectralpipe, filename
    ; compile_opt is a compile-time directive and idl2 means that the 
    ; default integer type is a 32-bit integer instead of a 16-bit integer
    ; it limits the array index syntax to just [].
    ; the default also allows () - which leads to confusion when reading 
    ; the code because it's difficult tell when one is a function and one
    ; is an array.
    compile_opt idl2

    filein, filename ; read the input file into the !g structure

    ; make sure it worked
    if !g.line_filein_name ne filename then begin
       print,'Could not open : ',filename
       return
    endif
    if (nrecords() eq 0) then begin
       print,filename,' is empty'
       return
    endif

    makeplots = 1
   
    velo ; change the idl plotter x-axis to velocity
    freeze ; freeze the plotter so it doesn't slow down processing

    ; collect a bunch of information from the input file
    ; and put it into the projectInfo structure
    projectInfo = get_project_info()
    if size(projectInfo,/type) ne 8 then begin
       print,"No PS scans that could be used found in data."
       return
    endif
    sources = projectInfo.sources
    print,'sources', sources

    ; for each source
    tags = tag_names(projectInfo)
    for isource=0, n_tags(projectInfo)-1 do begin
       if tags[isource] eq 'SOURCES' then continue

       sourceInfo = projectInfo.(isource)
       sourcename = sourceInfo.source
       scans = sourceInfo.scans
       dups = sourceInfo.duplicates
       missing = sourceInfo.missing
       srctype = sourceInfo.srctype

       print, 'sourcename ', sourcename, ' scans ', scans

       ; if there's nothing there to process (all duplicate or missing
       ; scans) then create invoke write_empty_output
       if scans[0] eq -1 then begin
                                ; reconstruct the list of all scans to
                                ; send to write_empty_output
          ; sort out the -1s later, this is simpler code
          allScans = [scans,dups,missing]
          allScans = allScans[uniq(allScans,sort(allScans))]
          if allScans[0] eq -1 then begin
             ; we know that there must be at least one real
             ; scan number here so that if the first one is -1
             ; there must be at least 2 elements in allScans
             ; so this is safe in all cases
             allScans = allScans[1:(n_elements(allScans)-1)]
          endif
          write_empty_output, sourcename, allScans
          if makeplots eq 1 then make_plot, sourcename

        endif else begin

           ; average all data from all scans for this source
           ; only examines IFNUM=0, FDNUM=0 for now
           ; assumes data has both plnum=0 and plnum=1
           ; if do_flag_broad_rfi is true, then inspect every 
           ; integration for wavy baselines
           ; only integrations that are not flagged are averaged
           average_source_scans, scans, sourcename, /do_flag_broad_rfi, naccum=naccum
           if naccum le 0 then begin
              ; everything was flagged 
              print,'All data from ',sourcename,' was flagged or otherwise unusable'
              write_empty_output, sourcename, scans
              if makeplots eq 1 then make_plot, sourcename
              continue
           endif

	    ; blank out the channels near band edges
	    blank_edges
	    
            if (srctype eq 'HI' || srctype eq 'TP_Source') then flag_narrow_rfi

	    smooth_spectrum
            
            if srctype eq 'HI' then blank_galactic
            
            fit_baseline

            ; set the frequency rest frame in the data to the tracked one.
            setfframe
            write_output, sourcename, scans

            if makeplots eq 1 then make_plot, sourcename

         endelse 
     endfor                     ; end loop over sources

    unfreeze

end

