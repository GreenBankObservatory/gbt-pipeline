import pyfits
import sys

z={}

fd = pyfits.open(sys.argv[1],memmap=1)
data = fd[1].data
lastscan=-1

for idx in range(len(data)):
    if data[idx]['SCAN']!=lastscan:
        z[data[idx]['SCAN']]=idx+1
        lastscan=data[idx]['SCAN']

print z
