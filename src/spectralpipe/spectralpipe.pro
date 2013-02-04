pro spectralpipe, filename
    compile_opt idl2

    filein, filename
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
    
    freeze
    sources = get_sources()
    print,'sources', sources

    ; for each source
    for isource=0, n_elements(sources)-1 do begin

        sourcename = sources[isource]
        scans = get_scans(sourcename)

        print, 'sourcename ', sourcename, ' scans ', scans

        ; Check to see if the same scan number was used more than once
        ;  when observing this source.  If so, create an empty output
        ;  file and a plot with an error message.
        if duplicate_scans(scans) then begin

            write_empty_output, sourcename, scans
            if makeplots eq 1 then make_plot, sourcename

        endif else begin

	    ;inspect every integration for wavy baselines
            ; this also averages all integrations that are not flagged
	    flag_broad_rfi, scans, sourcename

	    ; blank out the channels near band edges
	    blank_edges
	    
	    smooth_spectrum
	    blank_galactic
	    flag_narrow_rfi
	    fit_baseline
	    write_output, sourcename, scans

	    if makeplots eq 1 then make_plot, sourcename

        endelse 
    endfor ; end loop over sources

    unfreeze

end

