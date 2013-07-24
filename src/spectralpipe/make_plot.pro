pro make_plot, sourcename
    compile_opt idl2

    ; remove whitespace from sourcename for writing files
    srcname = strcompress(sourcename, /REMOVE_ALL)

    spawn, '/home/gbtpipeline/integration/spectralpipe/showreduced ' + srcname + '_' + !g.s[0].date + '.fits'

end
