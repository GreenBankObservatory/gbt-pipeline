function unique, sources
    compile_opt idl2

    return, sources[uniq(sources, sort(sources))]
end

