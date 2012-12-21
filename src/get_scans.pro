pro get_scans, sourcename
    common myscans, scans
    delvarx,scans
    sources_all=!g.lineio->get_index_values('SOURCE')
    scans_all=!g.lineio->get_index_values('SCAN')
    procseqn_all=!g.lineio->get_index_values('PROCSEQN')
    scans = scans_all[where(sources_all eq sourcename and procseqn_all eq 1)]
    scans = scans[uniq(scans)]
end

