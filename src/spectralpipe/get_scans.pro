function get_scans, sourcename
    compile_opt idl2

    scans = get_scan_numbers(source=sourcename, procseqn=1, /unique)
    return, scans
end

