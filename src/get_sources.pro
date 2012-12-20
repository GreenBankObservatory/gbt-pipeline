pro get_sources
    common mysources, sources

    sources_all=!g.lineio->get_index_values('SOURCE')
    source_indicies=uniq(sources_all)
    for ii=0,n_elements(source_indicies)-1 do begin
        if n_elements(sources) ge 1 then begin
            ;print,ii &$
            sources=[sources,sources_all[source_indicies[ii]]]
            ;print,'adding',sources_all[source_indicies[ii]] &$
        endif else begin
            ;print,ii &$
            ;print,'adding',sources_all[source_indicies[ii]] &$
            sources=[sources_all[source_indicies[ii]]]
        end
    end
    
    ;print, sources
end

