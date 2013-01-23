pro fft_flag, scannum, intnum, sourcename

    FFT_THRESHOLD=20
    spec = *!g.s[0].data_ptr

    ; get the fft of the upper 95% of the spectrum
    fullfft = abs(fft(spec[uint(.05*n_elements(spec)):n_elements(spec)-1]))
                        
    ; top 10% of fft
    myfft = fullfft[(uint(.9*n_elements(fullfft))):n_elements(fullfft)-1]
                    
    if max(myfft) gt stddev(myfft)*FFT_THRESHOLD then begin
        print,'FLAGGING INTEGRATION'
        flag, scannum, int=intnum, id='fft_rfi'+sourcename
    end
    
end

