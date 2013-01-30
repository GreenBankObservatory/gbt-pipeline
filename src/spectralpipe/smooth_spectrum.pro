pro smooth_spectrum
    compile_opt idl2

    ; apply smoothing to achieve 12 kHz channels
    ;print, 'boxcar',round(12207.03125/abs(!g.s[0].frequency_interval))
    boxcar, round(12207.03125/abs(!g.s[0].frequency_interval)), /d
end

