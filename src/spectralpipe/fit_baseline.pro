pro fit_baseline
    compile_opt idl2

    xx=getdata(0)
    nchans=n_elements(xx)
    ; use first and last 40% of channels
;    print, 'baseline', [ uint(nchans*.05), uint(nchans*.4), nchans-1-uint(nchans*.4), nchans-1-uint(nchans*.05)]
    nregion, [ uint(nchans*.05), uint(nchans*.4), nchans-1-uint(nchans*.4), nchans-1-uint(nchans*.05)]
    nfit, 3
    baseline
end

