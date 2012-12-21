pro get_sources
    common mysources, sources

    sources_all=!g.lineio->get_index_values('SOURCE')
    sources = sources_all[uniq(sources_all)]
    
end

