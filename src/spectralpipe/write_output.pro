pro write_output, sourcename
    ; Write out the reduced data
    outfilename = sourcename + '_' + !g.s[0].date + '.fits'
    print, 'writing ', outfilename
    file_delete, outfilename, /ALLOW_NONEXISTENT
    fileout, outfilename
    keep
end

