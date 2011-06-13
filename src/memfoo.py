import pyfits
import sys
import numpy as np
import os
#import memorymonitor

fd = pyfits.open('/media/980d0181-4160-4bbf-8c3d-3d370f24fefd/data/AGBT06A_065_05/AGBT06A_065_05.raw.acs.fits',memmap=1)
fd.info()

#raw_input('ready?')
#for idx,row in enumerate(fd[1].data):
    #a = row['DATA'].mean()
    ##print a.nbytes
    ##if idx%10000==0:
        ##raw_input(str(idx))
#raw_input(str(idx))
#sys.exit(0)


chunksize=10000
minrow = 0
#raw_input('do mask?')
#mask = fd[1].data.field('SCAN')==37
#raw_input('filter on mask?')
#data = fd[1].data[mask]
mydata = []
outputrows = []
print os.getpid()
raw_input('start?')
#mmon = memorymonitor.MemoryMonitor('jmasters')
while True:
    maxrow = minrow+chunksize

    #raw_input('read a chunk? '+str(minrow)+' to '+str(maxrow))
    data = fd[1].data[minrow:maxrow]

    if len(data) is 0:
        break

    for idx,row in enumerate(data):

        if row['SCAN'] == 37:
            outputrows.append(row)
            if len(mydata):
                mydata = np.vstack((mydata,row['DATA']))
            else:
                mydata = np.array(row['DATA'],ndmin=2)
    #print mmon.usage()
    minrow = maxrow


