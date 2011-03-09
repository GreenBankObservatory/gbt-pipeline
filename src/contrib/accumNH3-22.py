# parsel-tongue script tuned for SGR B2 obs of NH3
#HISTORY
#10OCT05 GIL extract NH3 2-2 from existing cube (200MHz)
#10SEP29 GIL try on NH3 1-1
#10SEP24 GIL add adam's H2CO line and the source velocity
#10SEP23 GIL add adam's H2CO line and the source velocity
#10SEP07 GIL set parameters for map center etc
#10SEP01 GIL initial version

from AIPS import *
from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import *
from AIPSData import AIPSUVData, AIPSImage
from Wizardry.AIPSData import AIPSUVData as WizAIPSUVData
import sys
import os
import math

AIPS.userno=int(sys.argv[1])
myfiles = sys.argv[2:]
mydisk=2

fittp=AIPSTask('fittp')
momnt=AIPSTask('momnt')
subim=AIPSTask('subim')

#23694.506 NH3   Ammonia   1(1)-1(1) 2,2    0.50b L134N    Ho 77  
#23722.633 NH3   Ammonia   2(2)-2(2)        0.43j OriMC-1  Bar77  
#23870.129 NH3   Ammonia   3(3)-3(3)        0.53j OriMC-1  Bar77  
#24139.416 NH3   Ammonia   4(4)-4(4)        0.25j OriMC-1  Bar77  
#24205.287 NH3   Ammonia   10(9)-10(9       0.1   OriMC-1  Nys78  
#24532.988 NH3   Ammonia   5(5)-5(5)        0.09j OriMC-1  Bar77  
#25056.025 NH3   Ammonia   6(6)-6(6)        0.17j OriMC-1  Bar77  
#25715.182 NH3   Ammonia   7(7)-7(7)        3.    OriMC-1  Mau86  
#26518.981 NH3   Ammonia   8(8)-8(8)        0.70  OriMC-1  Ziu81  
#27477.943 NH3   Ammonia   9(9)-9(9)        0.76  OriMC-1  Ziu81  

# This script only works if one one 'SUB SP' dataset exits
spectra = AIPSUVData(AIPSCat()[mydisk][-1].name, 'SUB SP', mydisk, 1)

# now read parameters passed inside the data header
nChan    = round(spectra.header.naxis[2])
cellsize = round(spectra.header.cdelt[4] * 3600.)
refChan  = spectra.header.crpix[2]
imxSize  = 2*round(spectra.header.crpix[3]/1.5 )
imySize  = 2*round(spectra.header.crpix[4]/1.5 )
raDeg    = spectra.header.crval[3]
decDeg   = spectra.header.crval[4]
nuRef    = spectra.header.crval[2]
dNu      = spectra.header.cdelt[2]

#print imxSize, imySize
#print raDeg, decDeg
#print cellsize
#print spectra.header
print 'nChan = ',nChan

#Run momnt task
#previously selected channels with the NH3 1-1 line
momnt.indisk=mydisk
momnt.outdisk=mydisk
momnt.inname=AIPSCat()[mydisk][-1].name
momnt.inclass='IMLIN'
momnt.inseq=1
momnt.icut=-300.
momnt.flux=-.005
momnt.blc[1]=1
momnt.blc[2]=0
momnt.blc[3]=0
momnt.trc[1]=nChan
momnt.trc[2]=0
momnt.trc[3]=0
momnt.cellsize[1] = 0
momnt.cellsize[2] = 0
print momnt.blc,momnt.trc

#add rest frequency to select out the line
restFreq = 23694.506e6
restFreq = 23722.633e6 #NH3   Ammonia   2(2)-2(2)  0.43j OriMC-1  Bar77

cLightKmSec = 299792.458
#These constants are particular to each source
sourceLineWidthHz = .2E6
sourceVelocityKmSec = 60.0
velocityWidthKmSec = 20.
sourceFreq = restFreq*(1.-(sourceVelocityKmSec/cLightKmSec))
print 'Center, Source Freq:',nuRef*1.E-6, sourceFreq*1.E-6,'+/-',dNu*1.E-6,' MHz'
#now set the default line channels and widths
lineWidthChan = 100
lineChan = round(nChan*.5)
#the source velocity half width, then compute number of channels

if dNu != 0:
    lineWidthChan = round(velocityWidthKmSec * sourceFreq/(dNu * cLightKmSec))
    if lineWidthChan < 0:
        lineWidthChan = - lineWidthChan
    lineChan = round(((sourceFreq-nuRef)/dNu) + refChan)

print 'Source Line Channel:',lineChan,'+/-',lineWidthChan                    

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
momnt.blc[1]=bChan
momnt.blc[2]=0
momnt.blc[3]=0
momnt.trc[1]=eChan
momnt.trc[2]=0
momnt.trc[3]=0
momnt.outclass='0'
momnt.go()

## Use the subim task to rename the output image
subim.indisk=mydisk
subim.inname=AIPSCat()[mydisk][-1].name
subim.inclass=AIPSCat()[mydisk][-1].klass
subim.inseq=AIPSCat()[mydisk][-1].seq
subim.outclass='22'
subim.outdi=mydisk
subim.go()

## and write the last thing now in the catalog to disk
fittp.indisk=mydisk
fittp.inname=AIPSCat()[mydisk][-1].name
fittp.inclass=AIPSCat()[mydisk][-1].klass
fittp.inseq=AIPSCat()[mydisk][-1].seq
outimage = os.path.splitext(myfiles[0])[0]+'_NH3-22.fits'
if os.path.exists(outimage):
    os.remove(outimage)
    print 'Removed existing file to make room for new one :',outimage
fittp.dataout='PWD:'+outimage
fittp.go()

