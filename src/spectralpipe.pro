pro spectralpipe, filename

    filein, filename
    ;filein,'/home/scratch/jbraatz/ExGalHI/10A59/AGBT10A_059_11.raw.acs.fits'
    
    freeze
    sources = get_sources()
    print,'sources', sources

    ; for each source
    for isource=0, n_elements(sources)-1 do begin
    ;for isource=1, 1 do begin

        sourcename = sources[isource]
        scans = get_scans(sourcename)

        print, 'sourcname ', sourcename, ' scans ', scans

        ;inspect every integration for wavy baselines
        flag_broad_rfi, scans, sourcename

        ; get an average of all scans on the source
        average_source_scans, scans
	
	; blank out the channels near band edges
        blank_edges
	
        smooth_spectrum
        blank_galactic
       	flag_narrow_rfi
        fit_baseline
        ;copy,0,isource
	write_output, sourcename 
    
    endfor ; end loop over sources

    unfreeze

end

