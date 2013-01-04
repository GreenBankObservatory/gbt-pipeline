pro flag_broad_rfi, scans, sourcename

    ; check every integration on the source for
    ;   wavy RFI using a FFT to find low frequency components
    ; for each scan pair
    for ii=0, n_elements(scans)-1 do begin
        scaninfo = scan_info(scans[ii])

        ; for each integration
        for jj=0, scaninfo.n_integrations-1 do begin
   	    getps, scans[ii], int=jj, plnum=0, units='Jy'
	    fft_flag, scans[ii], jj, sourcename

	    getps, scans[ii], int=jj, plnum=1, units='Jy'
	    fft_flag, scans[ii], jj, sourcename
	endfor
    endfor    
end

