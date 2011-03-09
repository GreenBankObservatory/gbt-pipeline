# parsel-tongue script that performs only the default processing
#HISTORY
#10OCT28 GIL Strip out sampler name for output
#10OCT20 GIL default average is 3 channels, add comments
#10OCT08 GIL comment out all source specific lines
#10OCT07 GIL remove Line specific processing; add comments
#10OCT05 GIL slight name and comment changes
#10SEP29 GIL try on NH3 1-1
#10SEP01 GIL initial version

from AIPS import *
from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import *
from AIPSData import AIPSUVData, AIPSImage
from Wizardry.AIPSData import AIPSUVData as WizAIPSUVData
from Wizardry.AIPSData import AIPSImage as WizAIPSImage

import sys
import os
import math

argc = len(sys.argv)
if argc < 3:
    print ''
    print 'imageDefault: Compute default images from calibrated spectra'
    print 'usage: doImage imageDefault.py <aipsNumber> <spectra File 1> [<spectra File n>]'
    print 'where <aipsNumber>     Your *PIPELINE* AIPS number (should always be the same)'
    print '      <spectra File 1> One or more calibrated spectra files (*.sdf)'
    print ''
    quit()
        
AIPS.userno=int(sys.argv[1])    # retrieve AIPS pipeline user number
myfiles = sys.argv[2:]          # make a list of input files
mydisk=2                        # choose a good default work disk
baddisk=1                       # choose a disk to avoid

AIPSCat().zap()                 # empty the catalog

uvlod=AIPSTask('uvlod')         # Create structures for AIPS tasks
sdgrd=AIPSTask('sdgrd')
fittp=AIPSTask('fittp')
dbcon=AIPSTask('dbcon')
trans=AIPSTask('trans')
imlin=AIPSTask('imlin')
avspc=AIPSTask('avspc')
subim=AIPSTask('subim')
sqash=AIPSTask('sqash')

kount = 0

for thisFile in myfiles:        # input all AIPS single dish FITS files
    print thisFile
    uvlod.datain='PWD:'+thisFile
    print uvlod.datain
    uvlod.outdisk=mydisk
    uvlod.go()
    spectra = AIPSUVData(AIPSCat()[mydisk][-1].name, AIPSCat()[mydisk][-1].klass, mydisk, AIPSCat()[mydisk][-1].seq)
    nuRef    = spectra.header.crval[2]
    if kount == 0:
        firstNu = nuRef
    if ((firstNu - nuRef) < -1.E4) or ((firstNu - nuRef) > 1.E4):
        print 'Frequencies differ: ',nuRef,' != ',firstNu
        spectra.zap()
    else:
        kount = kount+1

if kount > 1:            # if more than 1 file DBCON them

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
    for i in range(2,kount):
        # end of cat is always most recent dbcon result
        dbcon.inname = AIPSCat()[mydisk][-1].name
        dbcon.inclass = AIPSCat()[mydisk][-1].klass
        dbcon.inseq = AIPSCat()[mydisk][-1].seq
        dbcon.in2name = AIPSCat()[mydisk][i].name
        dbcon.in2class = AIPSCat()[mydisk][i].klass
        dbcon.in2seq = AIPSCat()[mydisk][i].seq
        dbcon.go()

# Extract the observations summary
spectra = AIPSUVData(AIPSCat()[mydisk][-1].name, AIPSCat()[mydisk][-1].klass, mydisk, AIPSCat()[mydisk][-1].seq)

# Read parameters passed inside the spectra data header
nChan    = round(spectra.header.naxis[2])
cellsize = round(spectra.header.cdelt[4] * 3600.)
refChan  = spectra.header.crpix[2]
imxSize  = 2*round(spectra.header.crpix[3]/1.5 )
imySize  = 2*round(spectra.header.crpix[4]/1.5 )
raDeg    = spectra.header.crval[3]
decDeg   = spectra.header.crval[4]
nuRef    = spectra.header.crval[2]
dNu      = spectra.header.cdelt[2]

print "Ra,Dec:", raDeg, decDeg, "Image:", imxSize, imySize, cellsize, 
#print spectra.header

# set number of channels to average
nAverage = 3
# now average channels to reduce the image plane data volumn
avspc.indisk=mydisk
avspc.outdisk=mydisk
avspc.inname=AIPSCat()[mydisk][-1].name
avspc.inclass=AIPSCat()[mydisk][-1].klass
avspc.inseq=AIPSCat()[mydisk][-1].seq
avspc.channel=nAverage
avspc.ichansel[1][1] = 1
avspc.ichansel[2][1] = nChan
avspc.ichansel[3][1] = nAverage
avspc.avoption='SUBS'
avspc.go()

#now have fewer channels, with broader frequencies
nChan = round(nChan/nAverage)
dNu = nAverage*dNu
refChan = refChan/nAverage

# Now make an image using the last entry in the catalog
sdgrd.indisk=mydisk
sdgrd.outdisk=mydisk
sdgrd.inname=AIPSCat()[mydisk][-1].name
sdgrd.inclass=AIPSCat()[mydisk][-1].klass
sdgrd.inseq=AIPSCat()[mydisk][-1].seq
sdgrd.optype='-GLS'
sdgrd.xtype=-12
sdgrd.ytype=-12
sdgrd.reweight[1] = 0
sdgrd.reweight[2] = 0.0025
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
print raDeg, decDeg, '->',sdgrd.aparm[1:6]
#transfer cellsize 
sdgrd.cellsize[1] = cellsize
sdgrd.cellsize[2] = cellsize
sdgrd.xparm[1] = 8*cellsize
sdgrd.xparm[2] = 2.5*cellsize
sdgrd.xparm[3] = 2
if imxSize < 30:
    imxSize = 150
if imySize < 30:
    imySize = 150
sdgrd.imsize[1] = imxSize
sdgrd.imsize[2] = imySize
sdgrd.baddisk[1]=baddisk
## The above lines set the default image parameters
## Below override imaging parameters to make observer set images
# RA
#sdgrd.aparm[1] = 19    #hours
#sdgrd.aparm[2] = 23    #minutes
#sdgrd.aparm[3] = 40    #seconds
# DEC
#sdgrd.aparm[4] = 14    #degrees
#sdgrd.aparm[5] = 31    #arcmins
#sdgrd.aparm[6] = 30    #arcseconds
# Imsize
#sdgrd.imsize[1] = 100
#sdgrd.imsize[2] = 110
sdgrd.go()

from Wizardry.AIPSData import AIPSImage as WizAIPSImage
image = WizAIPSImage(AIPSCat()[mydisk][-1].name, \
                     AIPSCat()[mydisk][-1].klass, \
                     mydisk, AIPSCat()[mydisk][-1].seq)

image.header.niter = 1          # Allow down stream IMSTATs to sum correctly
# optionally could change units to Jy/Beam, ETC
#image.header.bunit = 'JY/BEAM'
image.header.update()
image.update()
## and write the last thing now in the catalog to disk
fittp.indisk=mydisk
fittp.inname=AIPSCat()[mydisk][-1].name
fittp.inclass=AIPSCat()[mydisk][-1].klass
fittp.inseq=AIPSCat()[mydisk][-1].seq
outName = os.path.splitext(myfiles[0])[0]
iUnder = outName.rfind("_")
if iUnder > 0:
    outName = outName[0:iUnder]
outimage = outName+'_cube.fits'
if os.path.exists(outimage):
    os.remove(outimage)
    print 'Removed existing file to make room for new one :',outimage

fittp.dataout='PWD:'+outimage
fittp.go()

print 'Wrote',outimage

# squash the frequency axis to make a continuum image
sqash.indisk=mydisk
sqash.outdisk=mydisk
sqash.inname=AIPSCat()[mydisk][-1].name
sqash.inclass=AIPSCat()[mydisk][-1].klass
sqash.inseq=AIPSCat()[mydisk][-1].seq
sqash.bdrop=3 # squash frequency axis
sqash.go()

print AIPSCat()

## and write the last thing now in the catalog to disk
fittp.indisk=mydisk
fittp.inname=AIPSCat()[mydisk][-1].name
fittp.inclass=AIPSCat()[mydisk][-1].klass
fittp.inseq=AIPSCat()[mydisk][-1].seq
outimage = outName+'_cont.fits'
if os.path.exists(outimage):
    os.remove(outimage)
    print 'Removed existing file to make room for new one :',outimage
fittp.dataout='PWD:'+outimage
fittp.go()

#Run trans task on sdgrd file to prepare for the Moment map
trans.indisk=mydisk
trans.outdisk=mydisk
trans.baddisk[1]=baddisk
trans.inname=AIPSCat()[mydisk][-1].name
trans.inclass='SDGRD'
trans.inseq=1
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
# use only the end channels for the default baseline fits
imlin.box[1][1]=round(nChan*0.075)
imlin.box[1][2]=round(nChan*0.125)
imlin.box[1][3]=round(nChan*0.925)
imlin.box[1][4]=round(nChan*0.975)
#sometimes there is curvature in the baseline and another box is needed
#imlin.box[2][1]=round(nChan*0.6)
#imlin.box[2][2]=round(nChan*0.65)
#imlin.nbox=3
#imlin.order=2  # beware using imlin.order=1; use imlin.order=0
print imlin.box

imlin.go()

#Run trans task on sdgrd file 
trans.inname=AIPSCat()[mydisk][-1].name
trans.inclass=AIPSCat()[mydisk][-1].klass
trans.inseq=AIPSCat()[mydisk][-1].seq
trans.transc= '231'
trans.outdi=mydisk
trans.outcl='baseli'
trans.go()

## and write the last thing now in the catalog to disk
fittp.indisk=mydisk
fittp.inname=AIPSCat()[mydisk][-1].name
fittp.inclass=AIPSCat()[mydisk][-1].klass
fittp.inseq=AIPSCat()[mydisk][-1].seq
outimage = outName+'_line.fits'
if os.path.exists(outimage):
    os.remove(outimage)
    print 'Removed existing file to make room for new one :',outimage

fittp.dataout='PWD:'+outimage
fittp.go()

