import numpy as np
import pyfits
import sys

def index_it(indexfile,fitsfile=None,table_length=0,samplers=[],verbose=0):
    
    myFile = open(indexfile,'rU')
    if fitsfile:
        fd = pyfits.open(fitsfile,memmap=1)
        table_length = []
        # one set of masks per FITS extension
        # each set of masks has a mask for each sampler
        mask = []
        for blockid in range(1,len(fd)):
            table_length.append(len(fd[blockid].data))
            mask.append({})

        fd.close()
    else:
        if not bool(table_length):
            print 'ERROR: either fits file or table size must be provided'
            return False

    # skip over the index file header lines
    while True:
        row = myFile.readline().split()
        if len(row)==40:
            # we just found the column keywords, so read the next line
            row = myFile.readline().split()
            break

    while row:
        
        sampler = row[20]
        ii = int(row[4])
        extension_idx = int(row[3])-1  # FITS extention index, same as blockid +1 (above)

        # if samplers is empty, assume all samplers
        # i.e. not samplers == all samplers
        # if 1 or more sampler is specified, only use those for masks
        if (not samplers) or (sampler in samplers):
            
            # add a mask for a new sampler
            if not sampler in mask[extension_idx]:
                mask[extension_idx][sampler] = np.zeros((table_length[extension_idx]),dtype='bool')

            mask[extension_idx][sampler][ii] = True
            
        # read the next row
        row = myFile.readline().split()

    # print results
    for idx,maskblock in enumerate(mask):
        total = 0
        if verbose: print '-------------------'
        if verbose: print 'EXTENSION',idx+1
        if verbose: print '-------------------'
        for sampler in maskblock:
            total = total + maskblock[sampler].tolist().count(True)
            if verbose: print sampler,maskblock[sampler].tolist().count(True)
        if verbose: print 'total',total
        
    myFile.close()
    
    return mask

if __name__ == "__main__":

    indexfile='/media/980d0181-4160-4bbf-8c3d-3d370f24fefd/data/TKFPA_29.raw.acs.index'
    fitsfile='/media/980d0181-4160-4bbf-8c3d-3d370f24fefd/data/TKFPA_29.raw.acs.fits'
    samplers = []
    
    if len(sys.argv)>3:
        indexfile = sys.argv[1]
        fitsfile  = sys.argv[2]
        samplers = sys.argv[3]
        samplers = samplers.split(',')
        
    samplermask = index_it(indexfile=indexfile,fitsfile=fitsfile,samplers=samplers,verbose=1)
