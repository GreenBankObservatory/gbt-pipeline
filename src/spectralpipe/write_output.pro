pro write_output, sourcename, scans
    ; Write out the reduced data
    outfilename = sourcename + '_' + !g.s[0].date + '.fits'
    print, 'writing ', outfilename
    file_delete, outfilename, /ALLOW_NONEXISTENT
    fileout, outfilename
    keep

    ; update outfile header with list of scans used
    fd = readfits(outfilename, header, EXTEN_NO=1)

    scanlist = compress_scanlist(scans)
    fxaddpar, header, 'SCANLIST', scanlist[0]
    modfits, outfilename, 0, header, EXTEN_NO=1
end

