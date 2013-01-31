pro make_plot, sourcename
    compile_opt idl2

    spawn, '/home/gbtpipeline/integration/spectralpipe/showreduced ' + sourcename + '_' + !g.s[0].date + '.fits'

end
