pro blank_galactic
    compile_opt idl2

    ; get chan range for -300 km/s to 300 km/s
    galactic1=veltochan(!g.s[0], -300000)
    galactic2=veltochan(!g.s[0],  300000)
    low_channel = galactic1 < galactic2
    high_channel = galactic1 > galactic2
    replace, low_channel, high_channel, /blank
end

