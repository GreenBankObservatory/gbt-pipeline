pro average_source_scans, scans
    compile_opt idl2

    ; make sure the accum buffer is empty
    sclear
    for ii=0, n_elements(scans)-1 do begin
        getps, scans[ii], plnum=0, units='Jy',status=stat
        if stat eq 1 then accum

        getps, scans[ii], plnum=1, units='Jy',status=stat
        if stat eq 1 then accum
    endfor
    ave
end

