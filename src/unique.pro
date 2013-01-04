function unique, sources

    ; make sure the list is unique
    for ii=0, n_elements(sources)-1 do begin

        ; start a unique sources array
        if ii eq 0 then begin
            unique_sources = [sources[ii]]
        endif

        ; check to see if the source is already in the list
        index = where(unique_sources eq sources[ii])
        if index eq [-1] then begin
            ; if the source isn't already in the list, add it
            unique_sources = [unique_sources, sources[ii]]
        endif

    endfor
;    print,'number of unique sources', n_elements(unique_sources)
    return, unique_sources
end

