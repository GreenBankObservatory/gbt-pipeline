# parsel-tongue script tuned for SGR B2 obs of NH3
#HISTORY
#11JAN26 GIL add help
#10OCT06 GIL measure the NH3 1-1 integrated profile only

from AIPS import *
from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import *
from AIPSData import AIPSUVData, AIPSImage
from Wizardry.AIPSData import AIPSUVData as WizAIPSUVData
import sys
import os
import math

AIPS.userno=int(sys.argv[1])        # Extract AIPS pipeline number
outName = sys.argv[2]               # Extract Integrated Line Name
restFreqMHz = float(sys.argv[3])    # rest Frequency (MHz)
velocityKmS = float(sys.argv[4])    # velocity (km/s)
velWidthKmS = float(sys.argv[5])    # velocity Full Width (km/s)
mydisk=2

defaultName = 'Pipeline'
#Enforce name > 5 characters
if len(outName) < 6:
    outName = defaultName[0:(6-len(outName))] + outName
    
print 'Outname : ',outName
print 'RestFreq: ',restFreqMHz, ' (MHz)'
print 'Velocity: ',velocityKmS,' (km/s)'
print 'VelWidth: ',velWidthKmS,' (km/s)'

fittp=AIPSTask('fittp')
momnt=AIPSTask('momnt')
subim=AIPSTask('subim')

image = AIPSImage(AIPSCat()[mydisk][-1].name, 'IMLIN', mydisk, 1)

# now read parameters passed inside the data header
nChan    = round(image.header.naxis[0])
refChan  = image.header.crpix[0]
nuRef    = image.header.crval[0]
dNu      = image.header.cdelt[0]

print nChan, refChan, nuRef, dNu

#set rest frequency to select out the line
restFreq = restFreqMHz * 1.e6

cLightKmSec = 299792.458  # speed of light in Km/Sec

#These constants are particular to each source
sourceLineWidthHz = .2E6

sourceFreq = restFreq*(1.-(velocityKmS/cLightKmSec))
print 'Source Frequency:',sourceFreq*1.E-6,'+/-', \
  dNu*1.E-6,' MHz'
#now set the default line channels and widths
lineWidthChan = 100
lineChan = round(nChan*.5)

#Compute number of channels from the Velocity width
if dNu != 0:
    lineWidthChan = round(velWidthKmS * sourceFreq/(dNu * cLightKmSec))
    lineWidthChan = round(lineWidthChan/2.)
    if lineWidthChan < 0:
        lineWidthChan = - lineWidthChan
    lineChan = round(((sourceFreq-nuRef)/dNu) + refChan)

print 'Source Channel  :',lineChan,'+/-',lineWidthChan                    

#now calcuate channels from channel width
bChan = lineChan - lineWidthChan
eChan = lineChan + lineWidthChan
if bChan < 1:
    bChan = 1
if bChan > nChan:
    bChan = 1
if eChan > nChan:
    eChan = nChan
if eChan < 1:
    eChan = nChan
#Run momnt task
momnt.indisk=mydisk
momnt.outdisk=mydisk
momnt.inname=AIPSCat()[mydisk][-1].name
momnt.inclass='IMLIN'
momnt.inseq=1
momnt.icut=-10000.
momnt.flux=-.00001
momnt.outclass='0'
momnt.cellsize[1] = 0
momnt.cellsize[2] = 0
momnt.blc[1]=bChan
momnt.blc[2]=0
momnt.blc[3]=0
momnt.trc[1]=eChan
momnt.trc[2]=0
momnt.trc[3]=0
momnt.go()

# prepare to zap after the copy
image = AIPSImage( AIPSCat()[mydisk][-1].name, \
                   AIPSCat()[mydisk][-1].klass, mydisk, \
                   AIPSCat()[mydisk][-1].seq)

## Use the subim task to rename the output image
subim.indisk=mydisk
subim.inname=AIPSCat()[mydisk][-1].name
subim.inclass=AIPSCat()[mydisk][-1].klass
subim.inseq=AIPSCat()[mydisk][-1].seq
subim.outclass=outName[-6:]
subim.outdi=mydisk
subim.go()

#cleanup
#image.zap()

## and write the last thing now in the catalog to disk
fittp.indisk=mydisk
fittp.inname=AIPSCat()[mydisk][-1].name
fittp.inclass=AIPSCat()[mydisk][-1].klass
fittp.inseq=AIPSCat()[mydisk][-1].seq
outimage = outName+'.fits'
if os.path.exists(outimage):
    os.remove(outimage)
    print 'Removed existing file to make room for new one :',outimage
fittp.dataout='PWD:'+outimage
fittp.go()

