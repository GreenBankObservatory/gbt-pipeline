pro write_empty_output, sourcename, scans
    compile_opt idl2

    gettp, scans[0]

    ; nan out all the channel data
    flag, scans[0]

    write_output, sourcename, scans
    make_plot, sourcename
end
