pro get_sources
    common mysources, sources

    sources_all=!g.lineio->get_index_values('SOURCE')
    procedure=!g.lineio->get_index_values('PROCEDURE')
    restfreq=!g.lineio->get_index_values('RESTFREQ')

    sources = sources_all[where((procedure eq 'OnOff' or procedure eq 'OffOn') and (restfreq gt 1.419e+09 and restfreq lt 1.421e+09))]

    sources = sources[uniq(sources)]
    ;print,sources 
end

