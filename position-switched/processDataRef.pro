; process all of the data through calBandRef, one feed and bank at a time
;
; called by createMap, which sets up these inputs.
; loop is over all nFeed and nBank.  Other arguments are
; passed to either calBandRef or toaips as is.

pro processDataRef, nFeed, nBand, refScans, allScans, wait, vsource, vSourceWidth, vSourceBegin, vSourceEnd

    ; toaips line: selects channels and writes the AIPS compatible data 
    for iFeed = 0, nFeed-1 do begin
        for iBand = 0, nBand-1 do begin
            gettp,refScans[0], int=0, ifnum=iBand, fdnum=iFeed, status=status
            if status ne 1 then begin
                print,'No data found for Band ',iBand,' Feed ',iFeed
                continue
            endif

            calBandRef, allscans, refscans, iBand, iFeed, nPol, wait

            toaips,!g.s[0],vSource,vSourceWidth,vSourceBegin,vSourceEnd
        endfor
    endfor
end
