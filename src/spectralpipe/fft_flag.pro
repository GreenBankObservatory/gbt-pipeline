pro fft_flag, dc, scannum, intnum, sourcename, isflagged=isflagged
    compile_opt idl2

    FFT_THRESHOLD=20
    isflagged = 0
    spec = *(dc.data_ptr)

    ; get the fft of the upper 95% of the spectrum
    fullfft = abs(fft(spec[uint(.05*n_elements(spec)):n_elements(spec)-1]))
                        
    ; top 10% of fft
    myfft = fullfft[(uint(.9*n_elements(fullfft))):n_elements(fullfft)-1]
                    
    if max(myfft) gt stddev(myfft)*FFT_THRESHOLD then begin
        print,'FLAGGING INTEGRATION'
        flag, scannum, int=intnum, id='fft_rfi'+sourcename
        isflagged = 1
    end
    
end

