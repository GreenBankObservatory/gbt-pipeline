pro average_source_scans, scans
    compile_opt idl2

    for ii=0, n_elements(scans)-1 do begin
        getps, scans[ii], plnum=0, units='Jy'
        accum

        getps, scans[ii], plnum=1, units='Jy'
        accum
    endfor
    ave
end

