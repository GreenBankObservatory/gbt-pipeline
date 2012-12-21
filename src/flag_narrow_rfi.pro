pro flag_narrow_rfi
    
    niter=10
    nsigma=3
    filtwin=15
    while niter gt 0 do begin
        print,niter
        copy,0,10
        mediansub,filtwin
        sd = stddev(*!g.s[0].data_ptr, /NAN)
        spikes = abs(*!g.s[0].data_ptr)
        copy,10,0
        mask = where(spikes gt (nsigma*sd))
        if mask[0] eq -1 then break 
        for ii=0, n_elements(mask)-1 do begin
            replace, mask[ii], /blank
        end
        niter -= 1
    end
end


