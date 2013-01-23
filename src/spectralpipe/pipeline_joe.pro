pro spectralpipe, filename
    common mysources, sources
    common myscans, scans

    ;filein,'/home/scratch/jbraatz/ExGalHI/10A59/AGBT10A_059_11.raw.acs.fits'
    ; Select the input file
    ;;args = command_line_args()
    ;;print,args[0]
    ;;filein,args[0]

    get_sources
    freeze

    for isource=0, n_elements(sources)-1 do begin
        print,sources[isource]
        get_scans,sources[isource]
        print,scans

	; Select scans for the galaxy to be processed
	emptystack
	appendstack,scans

	for ii=0,!g.acount-1 do begin
	    scaninfo = scan_info(astack(ii))
	    for jj=0, scaninfo.n_integrations-1 do begin
		getps,astack(ii),int=jj,plnum=0,units='Jy'
		flag_broad_rfi, scannum, intnum, sourcename
		getps,astack(ii),int=jj,plnum=1,units='Jy'
		flag_broad_rfi, scannum, intnum, sourcename
	    end
	end

	; Average the scans
	for i=0,!g.acount-1 do begin
	    getps,astack(i),plnum=0,units='Jy'
	    accum
	    getps,astack(i),plnum=1,units='Jy'
	    accum
	end
	ave
	
	; blank out the channels near band edges
	xx=getdata(0)
	nchans=n_elements(xx)
	; blank first and last 5% of channels
	print, 'blanking 0 to', uint(nchans*.05)
	replace, 0, uint(nchans*.05), /blank
	print,'blanking', nchans-1-uint(nchans*.05),' to', nchans-1
	replace, nchans-1-uint(nchans*.05), nchans-1, /blank
	
	; apply smoothing to achieve 12 kHz channels
	; boxcar, 16, /d
	print, 'boxcar',round(12207.03125/abs(!g.s[0].frequency_interval))
	boxcar, round(12207.03125/abs(!g.s[0].frequency_interval)), /d
	
	; blank Galactic emission
	; get chan range for -300 km/s to 300 km/s
	galactic1=veltochan(!g.s[0], -300000)
	galactic2=veltochan(!g.s[0],  300000)
	low_channel = galactic1 < galactic2
	high_channel = galactic1 > galactic2
	replace, low_channel, high_channel, /blank
	
	; blank RFI
	flag_narrow_rfi
	
	; Fit a baseline
	xx=getdata(0)
	nchans=n_elements(xx)
	; use first and last 40% of channels
	print, 'baseline', [ uint(nchans*.05), uint(nchans*.4), nchans-1-uint(nchans*.4), nchans-1-uint(nchans*.05)]
	nregion, [ uint(nchans*.05), uint(nchans*.4), nchans-1-uint(nchans*.4), nchans-1-uint(nchans*.05)]
	nfit, 3
	baseline
	
	; Write out the reduced data
	fileout, sources[isource]+'_'+!g.s[0].date+'.fits'
	keep
    end
    unfreeze
end

