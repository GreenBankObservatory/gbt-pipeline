pro write_output, sourcename, scans
    compile_opt idl2

    ; Write out the reduced data
    outfilename = sourcename + '_' + !g.s[0].date + '.fits'
    print, 'writing ', outfilename
    file_delete, outfilename, /ALLOW_NONEXISTENT
    fileout, outfilename
    keep

    ; write out velocities to be used for plots
    unfreeze
    show
    velfilename = sourcename + '_' + !g.s[0].date + '.vdata' 
    file_delete, velfilename, /ALLOW_NONEXISTENT
    write_ascii, velfilename
    freeze

   ; update outfile header with list of scans used
    fd = readfits(outfilename, header, EXTEN_NO=1)

    scanlist = compress_scanlist(scans)
    fxaddpar, header, 'SCANLIST', scanlist[0]
    modfits, outfilename, 0, header, EXTEN_NO=1

    hdr = headfits(outfilename)
    sxaddhist,"This spectrum was created by the GBT spectral pipeline.",hdr,/COMMENT
    sxaddhist,"It is intended for quick-look assessment of the data quality.",hdr,/COMMENT
    sxaddhist,"This file is written in SDFITS format and can be read by",hdr,/COMMENT
    sxaddhist,"GBTIDL and other standard FITS readers.",hdr,/COMMENT
    sxaddhist,"",hdr,/COMMENT
    sxaddhist,"The GBTIDL webpage is here:",hdr,/COMMENT
    sxaddhist,"http://gbtidl.nrao.edu",hdr,/COMMENT
    sxaddhist,"",hdr,/COMMENT
    sxaddhist,"SDFITS is described here:",hdr,/COMMENT
    sxaddhist,"http://fits.gsfc.nasa.gov/registry/sdfits.html",hdr,/COMMENT
    modfits,outfilename,0,hdr

end

