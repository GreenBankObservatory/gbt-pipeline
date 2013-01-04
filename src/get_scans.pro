function get_scans, sourcename
    scans = get_scan_numbers(source=sourcename, procseqn=1, /unique)
    return, scans
end

