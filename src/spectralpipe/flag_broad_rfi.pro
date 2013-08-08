
pro flag_broad_rfi, intData, scanNumber, sourcename, intFlagged
    compile_opt idl2

    ; intData is a vector of data containers, one per 
    ; integration, from scanNumber and relevant to sourcename

    ; check every intData for 
    ;   wavy RFI using a FFT to find low frequency components
    ; for each scan pair
    ; intFlagged has the same length as intData (not checked here)
    ; and elements are set to 1 if that integration was flagged,
    ; else 0.

    for jj=0,n_elements(intData)-1 do begin
       fft_flag, intData[jj], scanNumber, jj, sourcename, isflagged=isflagged
       intFlagged[jj] = isflagged
    endfor
end

