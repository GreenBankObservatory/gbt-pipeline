pro write_output, sourcename
    ; Write out the reduced data
    outfilename = sourcename + '_' + !g.s[0].date + '.fits'
    print, 'writing ', outfilename
    fileout, outfilename
    keep
end

