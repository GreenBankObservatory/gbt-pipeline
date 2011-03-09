# parsel-tongue script tuned for SGR B2 obs of NH3
#HISTORY
#10OCT05 GIL slight name and comment changes
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

# empty the catalog
AIPSCat().zap()

uvlod=AIPSTask('uvlod')
sdgrd=AIPSTask('sdgrd')
fittp=AIPSTask('fittp')
dbcon=AIPSTask('dbcon')
trans=AIPSTask('trans')
imlin=AIPSTask('imlin')
momnt=AIPSTask('momnt')
avspc=AIPSTask('avspc')
subim=AIPSTask('subim')

for thisFile in myfiles:
    print thisFile
    uvlod.datain='PWD:'+thisFile
    print uvlod.datain
    uvlod.outdisk=mydisk
    uvlod.go()

if len(myfiles) > 1:
    # must DBCON

    # always do first 2
    dbcon.indisk=mydisk
    dbcon.outdisk=mydisk
    dbcon.inname = AIPSCat()[mydisk][0].name
    dbcon.inclass = AIPSCat()[mydisk][0].klass
    dbcon.inseq = AIPSCat()[mydisk][0].seq
    dbcon.in2name = AIPSCat()[mydisk][1].name
    dbcon.in2class = AIPSCat()[mydisk][1].klass
    dbcon.in2seq = AIPSCat()[mydisk][1].seq
    dbcon.reweight[1] = 0
    dbcon.reweight[2] = 0
    dbcon.go()

    # and keep adding in one
    for i in range(2,len(myfiles)):
        # end of cat is always most recent dbcon result
        dbcon.inname = AIPSCat()[mydisk][-1].name
        dbcon.inclass = AIPSCat()[mydisk][-1].klass
        dbcon.inseq = AIPSCat()[mydisk][-1].seq
        dbcon.in2name = AIPSCat()[mydisk][i].name
        dbcon.in2class = AIPSCat()[mydisk][i].klass
        dbcon.in2seq = AIPSCat()[mydisk][i].seq
        dbcon.go()



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

spectra = AIPSUVData(AIPSCat()[mydisk][-1].name, AIPSCat()[mydisk][-1].klass, mydisk, AIPSCat()[mydisk][-1].seq)

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

print imxSize, imySize
print raDeg, decDeg
print cellsize
print spectra.header
print 'nChan = ',nChan

nAverage = 5
# now average channels to reduce the image plan volumn
avspc.indisk=mydisk
avspc.outdisk=mydisk
avspc.inname=AIPSCat()[mydisk][-1].name
avspc.inclass=AIPSCat()[mydisk][-1].klass
avspc.inseq=AIPSCat()[mydisk][-1].seq
avspc.channel=nAverage
avspc.ichansel[1][1] = 1
avspc.ichansel[2][1] = nChan
avspc.ichansel[3][1] = 3
avspc.avoption='SUBS'
avspc.go()

#now have fewer channels, with broader frequencies
nChan = round(nChan/nAverage)
dNu = nAverage*dNu
refChan = refChan/nAverage

# Now make an image using the last item in the catalog
sdgrd.indisk=mydisk
sdgrd.outdisk=mydisk
sdgrd.inname=AIPSCat()[mydisk][-1].name
sdgrd.inclass=AIPSCat()[mydisk][-1].klass
sdgrd.inseq=AIPSCat()[mydisk][-1].seq
sdgrd.optype='-GLS'
sdgrd.xtype=-12
sdgrd.ytype=-12
sdgrd.reweight[1] = 0
sdgrd.reweight[2] = 0.05
# must break up RA into hours minutes seconds
sdgrd.aparm[1]=math.floor(raDeg/15.)
sdgrd.aparm[2]=math.floor(((raDeg/15.)-sdgrd.aparm[1])*60.)
sdgrd.aparm[3]=round(((((raDeg/15.)-sdgrd.aparm[1])*60.)-sdgrd.aparm[2])*60.)
#now break up degrees, but must preserve sign
decSign = 1.
if decDeg < 0.:
    decSign = -1.
    decDeg = -1. * decDeg

sdgrd.aparm[4]=math.floor(decDeg)
sdgrd.aparm[5]=math.floor((decDeg-sdgrd.aparm[4])*60.)
sdgrd.aparm[6]=round((((decDeg-sdgrd.aparm[4])*60.)-sdgrd.aparm[5])*60.)
#now deal with degrees and/or minutes == 0
if decSign < 0.:
    sdgrd.aparm[4] = -1. * sdgrd.aparm[4]
    if sdgrd.aparm[4] == 0:
        sdgrd.aparm[5] = -1. * sdgrd.aparm[5]
        if sdgrd.aparm[5] == 0:
            sdgrd.aparm[6] = -1.* sdgrd.aparm[6]
print raDeg, decDeg, '->',sdgrd.aparm
#sdgrd.aparm[4]=decDeg
#custom edited for Sgr B2 obs
#if  cellsize < 2:
#cellsize = 6
sdgrd.cellsize[1] = cellsize
sdgrd.cellsize[2] = cellsize
sdgrd.xparm[1] = 8*cellsize
sdgrd.xparm[2] = 2*cellsize
sdgrd.xparm[3] = 2
if imxSize < 10:
    imxSize = 150
if imySize < 10:
    imySize = 150
sdgrd.imsize[1] = imxSize
sdgrd.imsize[2] = imySize
## The above lines set the default image parameters
## Below override imaging parameters to make uniform images
# RA
sdgrd.aparm[1] = 19
sdgrd.aparm[2] = 23
sdgrd.aparm[3] = 40
# DEC
sdgrd.aparm[4] = 14
sdgrd.aparm[5] = 31
sdgrd.aparm[6] = 30
# Imsize
sdgrd.imsize[1] = 100
sdgrd.imsize[2] = 110
sdgrd.go()

## and write the last thing now in the catalog to disk
fittp.indisk=mydisk
fittp.inname=AIPSCat()[mydisk][-1].name
fittp.inclass=AIPSCat()[mydisk][-1].klass
fittp.inseq=AIPSCat()[mydisk][-1].seq
outimage = os.path.splitext(myfiles[0])[0]+'_image.fits'
if os.path.exists(outimage):
    os.remove(outimage)
    print 'Removed existing file to make room for new one :',outimage

fittp.dataout='PWD:'+outimage
fittp.go()

print 'Wrote',outimage

print AIPSCat()

#Run trans task on sdgrd file 
trans.indisk=mydisk
trans.outdisk=mydisk
trans.inname=AIPSCat()[mydisk][-1].name
trans.inclass=AIPSCat()[mydisk][-1].klass
trans.inseq=AIPSCat()[mydisk][-1].seq
trans.transc= '312'
trans.outcl='312'
trans.go()

#Run imlin task on trans file
#remove a spectral baseline.  Output image is in Freq-RA-Dec order
#(Transcod 312)
imlin.indisk=mydisk
imlin.outdisk=mydisk
imlin.outcl='IMLIN'
imlin.inname=AIPSCat()[mydisk][-1].name
imlin.inclass=AIPSCat()[mydisk][-1].klass
imlin.inseq=AIPSCat()[mydisk][-1].seq
imlin.nbox=2
# use only the end channels for the default fits
imlin.box[1][1]=round(nChan*0.05)
imlin.box[1][2]=round(nChan*0.1)
imlin.box[1][3]=round(nChan*0.95)
imlin.box[1][4]=round(nChan*0.99)

print imlin.box

imlin.go()

#Run trans task on sdgrd file 
trans.inname=AIPSCat()[mydisk][-1].name
trans.inclass=AIPSCat()[mydisk][-1].klass
trans.inseq=AIPSCat()[mydisk][-1].seq
trans.transc= '231'
trans.outcl='baseli'
trans.go()

## and write the last thing now in the catalog to disk
fittp.indisk=mydisk
fittp.inname=AIPSCat()[mydisk][-1].name
fittp.inclass=AIPSCat()[mydisk][-1].klass
fittp.inseq=AIPSCat()[mydisk][-1].seq
outimage = os.path.splitext(myfiles[0])[0]+'_imlin.fits'
if os.path.exists(outimage):
    os.remove(outimage)
    print 'Removed existing file to make room for new one :',outimage

fittp.dataout='PWD:'+outimage
fittp.go()

#Run momnt task
#previously selected channels with the NH3 1-1 line
momnt.indisk=mydisk
momnt.outdisk=mydisk
momnt.inname=AIPSCat()[mydisk][-1].name
momnt.inclass='IMLIN'
momnt.inseq=1
momnt.icut=-300.
momnt.flux=-.005
momnt.outclass='0'
momnt.blc[1]=1
momnt.blc[2]=0
momnt.blc[3]=0
momnt.trc[1]=nChan
momnt.trc[2]=0
momnt.trc[3]=0
momnt.cellsize[1] = 0
momnt.cellsize[2] = 0
print momnt.blc,momnt.trc
momnt.go()

## and write the last thing now in the catalog to disk
fittp.indisk=mydisk
fittp.inname=AIPSCat()[mydisk][-1].name
fittp.inclass=AIPSCat()[mydisk][-1].klass
fittp.inseq=AIPSCat()[mydisk][-1].seq
outimage = os.path.splitext(myfiles[0])[0]+'_continuum.fits'
if os.path.exists(outimage):
    os.remove(outimage)
    print 'Removed existing file to make room for new one :',outimage
fittp.dataout='PWD:'+outimage
fittp.go()

#add rest frequency to select out the line
restFreq = 14488.4801e6
restFreq = 23694.506e6

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
subim.outclass='11'
subim.outdi=mydisk
subim.go()


## and write the last thing now in the catalog to disk
fittp.indisk=mydisk
fittp.inname=AIPSCat()[mydisk][-1].name
fittp.inclass=AIPSCat()[mydisk][-1].klass
fittp.inseq=AIPSCat()[mydisk][-1].seq
outimage = os.path.splitext(myfiles[0])[0]+'_NH3-11.fits'
if os.path.exists(outimage):
    os.remove(outimage)
    print 'Removed existing file to make room for new one :',outimage
fittp.dataout='PWD:'+outimage
fittp.go()

