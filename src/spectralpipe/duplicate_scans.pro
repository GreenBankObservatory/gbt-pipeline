function duplicate_scans, scans
    compile_opt idl2

    for idx=0, n_elements(scans)-1 do begin
        if n_elements(scan_info(scans[idx])) gt 1 then begin
            return, 1
        endif
    endfor
    return, 0 
end
