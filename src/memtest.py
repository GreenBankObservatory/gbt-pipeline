import pyfits
import os
import numpy as np
print 'pid',os.getpid()
raw_input('?')
fd = pyfits.open('/media/980d0181-4160-4bbf-8c3d-3d370f24fefd/data/AGBT10C_045_01/AGBT10C_045_01.raw.acs.fits',memmap=1)
print 'length of table is',fd[1].header['naxis2']
foo = []
raw_input('about to start mask')
mask = fd[1].data.field('SCAN')==24
raw_input('finished mask')
data = fd[1].data[mask]
raw_input('finished filter')
print len(data)
raw_input('lenth of filtered data')

for idx,row in enumerate(fd[1].data):
    
    if len(foo):
        foo = np.vstack((foo,row['DATA']))
    else:
        foo = np.array(row['DATA'],ndmin=2)
    if 0==idx%1000:
        print idx
        print len(foo),foo.nbytes/1e6
fd.close()
print len(foo)
raw_input('done')