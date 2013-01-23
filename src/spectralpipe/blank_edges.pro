pro blank_edges
    xx=getdata(0)
    nchans=n_elements(xx)
    ; blank first and last 5% of channels
;    print, 'blanking 0 to', uint(nchans*.05)
    replace, 0, uint(nchans*.05), /blank
 ;   print,'blanking', nchans-1-uint(nchans*.05),' to', nchans-1
    replace, nchans-1-uint(nchans*.05), nchans-1, /blank
end
