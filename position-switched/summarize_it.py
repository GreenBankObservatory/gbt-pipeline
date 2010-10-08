import sys

def summarize_it(indexfile,debug=False):

    myFile = open(indexfile,'rU')
    
    scans = {}
    map_scans = {}

    # skip over the index file header lines
    while True:
        row = myFile.readline().split()
        if len(row)==40:
            # we just found the column keywords, so read the next line
            row = myFile.readline().split()
            break

    while row:
        
        obsid = row[7]
        scan = int(row[10])

        if not scan in scans:
            scans[scan] = obsid
            
        # read the next row
        row = myFile.readline().split()

    myFile.close()

    # print results
    if debug:
        print '------------------------- All scans'
        for scan in scans:
            print 'scan',scan,scans[scan]

        print '------------------------- Relavant scans'

    for scan in scans:
        if scans[scan]=='Map' or scans[scan]=='Off':
            map_scans[scan] = scans[scan]

    mapkeys = map_scans.keys()
    mapkeys.sort()

    if debug:
        for scan in mapkeys:
            print 'scan',scan,map_scans[scan]

    maps = [] # final list of maps
    ref1 = False
    ref2 = False
    prev_ref2 = False
    mapscans = [] # temporary list of map scans for a single map

    if debug:
        print 'mapkeys', mapkeys
        
    for idx,scan in enumerate(mapkeys):
        
        # look for the offs
        if map_scans[scan]=='Off':
            # if there is no ref1 or this is another ref1
            if not ref1 or (ref1 and bool(mapscans)==False):
                ref1 = scan
            else:
                ref2 = scan
                prev_ref2 = ref2

        elif map_scans[scan]=='Map':
            if not ref1 and prev_ref2:
                ref1 = prev_ref2
        
            mapscans.append(scan)
        
        if ref2 or bool(map_scans)==False:
            maps.append((ref1,mapscans,ref2))
            ref1 = False
            ref2 = False
            mapscans = []
            
        if idx==len(mapkeys)-1:
            maps.append((ref1,mapscans,ref2))

    if debug:
        import pprint
        pprint.pprint(maps)
        
        for idx,mm in enumerate(maps):
            print "Map",idx
            if mm[2]:
                print "\tReference scans.....",mm[0],mm[2]
            else:
                print "\tReference scan......",mm[0]
            print "\tMap scans...........",mm[1]

    return maps

if __name__ == "__main__":
    
    indexfile = '/media/980d0181-4160-4bbf-8c3d-3d370f24fefd/data/TKFPA_29.raw.acs.index'

    summarize_it(indexfile,debug=True)
