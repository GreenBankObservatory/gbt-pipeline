class ScanInfo:
    n_feeds = set([])
    n_polarizations = set([])
    n_ifs = set([])
    n_integrations = set([])
    n_channels = set([])
    n_samplers = set([])
    n_cals = set([])
    data=[]

def scan_info(scan_number,sdfdata):

    si = ScanInfo()

    for idx in range(len(sdfdata)):
        if sdfdata[idx]['SCAN']==scan_number:
            si.n_feeds.add(sdfdata[idx]['FEED'])
            si.n_polarizations.add(sdfdata[idx]['CRVAL4'])
            si.n_samplers.add(sdfdata[idx]['SAMPLER'])
            si.n_cals.add(sdfdata[idx]['CAL'])
            si.data.append(sdfdata[idx]['DATA'])
        elif sdfdata[idx]['SCAN']>scan_number:
            break
    si.n_ifs = len(si.n_samplers)/len(si.n_cals)

    if (verbose > 3):
        print 'n_feeds',len(si.n_feeds)
        print 'n_polarizations',len(si.n_polarizations)
        print 'n_ifs',si.n_ifs
        print 'n_cals',len(si.n_cals)
        print 'n_channels',len(si.data[0])
        print 'n_samplers',len(si.n_samplers)
        print 'nrecords',len(si.data)
    return si
