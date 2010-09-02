import numpy as np
import pyfits
import sys

def index_it(indexfile,fitsfile=None,table_length=0,samplers=[],verbose=0):
    
    myFile = open(indexfile,'rU')
    
    if fitsfile:
        fd = pyfits.open(fitsfile,memmap=1)
        table_length = len(fd[1].data)
        fd.close()
    else:
        if not bool(table_length):
            print 'ERROR: either fits file or table size must be provided'
            return False

    # identify map blocks first

    # one mask per sampler
    mask = {}

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

        # if samplers is empty, assume all samplers
        # i.e. not samplers == all samplers
        # if 1 or more sampler is specified, only use those for masks
        if (not samplers) or (sampler in samplers):
            
            # add a mask for a new sampler
            if not sampler in mask:
                mask[sampler] = np.zeros((table_length),dtype='bool')

            mask[sampler][ii] = True
            
        # read the next row
        row = myFile.readline().split()

    # print results
    total = 0
    
    if verbose: print '-------------------'
    for sampler in mask:
        total = total + mask[sampler].tolist().count(True)
        if verbose: print sampler,mask[sampler].tolist().count(True)
    if verbose: print 'total',total
        
    myFile.close()
    
    return mask

if __name__ == "__main__":

    indexfile='/home/jmasters/data/TKFPA_17.raw.acs.index'
    fitsfile='/home/jmasters/data/TKFPA_17.raw.acs.fits'
    samplers = []
    
    if len(sys.argv)>3:
        indexfile = sys.argv[1]
        fitsfile  = sys.argv[2]
        samplers = sys.argv[3]
        samplers = samplers.split(',')
        
    samplermask = index_it(indexfile=indexfile,fitsfile=fitsfile,samplers=samplers,verbose=1)
