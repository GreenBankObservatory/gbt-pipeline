function compress_scanlist, scans
    compile_opt idl2

    ; make sure scans numbers are in ascending order
    scans = scans[sort(scans)]

    ; scans only contains the first scan number of each pair.
    ; we need to expand this to include all scans, so e.g.
    ; [1,3,5,9] becomes [1,2,3,4,5,6,9,10]
    ia = intarr(n_elements(scans)*2)
    for ii = 0, n_elements(scans)-1 do begin
        ia[ii*2]  = scans[ii]
        ia[ii*2+1] = scans[ii] + 1
    endfor

    ; now we create an array showing the delta between each
    ; scan number.  so [1,2,3,4,5,6,9,10] would produce
    ; [1,1,1,1,1,3,1]
    da = intarr(n_elements(ia))
    for ii = 1, n_elements(ia)-1 do begin
        da[ii] = ia[ii] - ia[ii-1]
    endfor

    ; start the return string with the first scan in the list
    compressed_scanlist = strtrim(ia[0],2) + '-'

    ; we use delta>1 to decide where one range ends and another begins 
    for ii=1, n_elements(ia)-1 do begin
        delta = ia[ii]-ia[ii-1]
        if delta gt 1 then begin
            compressed_scanlist = compressed_scanlist + strtrim(ia[ii-1],2) + ', ' + strtrim(ia[ii],2) + '-'
        endif
    endfor

    ; add the final scan number to the scan list string to close the last range
    compressed_scanlist = compressed_scanlist + strtrim(ia[n_elements(ia)-1],2)

    return, compressed_scanlist 
end
