# Copyright (C) 2007 Associated Universities, Inc. Washington DC, USA.
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# 
# Correspondence concerning GBT software should be addressed as follows:
#       GBT Operations
#       National Radio Astronomy Observatory
#       P. O. Box 2
#       Green Bank, WV 24944-0002 USA

# $Id$

# parsel-tongue script that performs only the default imaging
#HISTORY
#11FEB22 GIL decrease convolution function size
#11JAN26 GIL make default line image flatter
#10DEC23 GIL try to reduce default size so baselineing runs
#10DEC18 GIL clean up more comments
#10DEC02 GIL assume data are in the first slot
#10DEC01 GIL make default image size smaller
#10NOV30 GIL make generic version gaussian convolving function
#10NOV29 GIL add TMC CP coordinates
#10NOV12 GIL try to improve baseline for NH3
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
if argc < 2:
    print ''
    print 'mapDefault: Compute default images from calibrated spectra'
    print 'usage: doImage mapDefault.py <aipsNumber> [<nAverage>] [<mapRaDeg>] [<mapDecDeg>] [<imageXPixels>] [<imageYPixels>] [<refFreqMHz>]'
    print 'where <aipsNumber>     Your *PIPELINE* AIPS number (should always be the same)'
    print '     [<nAverage>]      Optional number of channels to average'
    print '     [<mapRaDeg>]      Optional map center RA (in Degrees)'
    print '     [<mapDecDeg>]     Optional map center Declination (in Degrees)'
    print '     [<imageXPixels>]  Optional image X pixel size'
    print '     [<imageYPixels>]  Optional image Y pixel size'
    print '     [<refFregMHz>]    Optional rest frequency MHz'
    print 'To enter later arguments, values for the previous must be provided' 
    print ''
    quit()

AIPS.userno=int(sys.argv[1])    # retrieve AIPS pipeline user number
# All other arguments arguments have defaults
if argc > 2:
    inNAve = int( sys.argv[2])
else:
    inNAve = 3                  # default is average 3 channels
if argc > 3:
    inRa = float( sys.argv[3])
else:
    inRa = 0
if argc > 4:
    inDec = float( sys.argv[4])
else:
    inDec = 0
if argc > 5:
    inImX = int( sys.argv[5])
else:
    inImX = 0
if argc > 6:
    inImY = int( sys.argv[6])
else:
    inImY = 0
if argc > 7:
    inRefFreqHz = float( sys.argv[7])*1.E6  # convert to Hz
else:
    inRefFreqHz = 0
mydisk=2                        # choose a good default work disk
baddisk=1                       # list a disk to avoid (0==no avoidance)

sdgrd=AIPSTask('sdgrd')
fittp=AIPSTask('fittp')
imlod=AIPSTask('imlod')
trans=AIPSTask('trans')
imlin=AIPSTask('imlin')
avspc=AIPSTask('avspc')
subim=AIPSTask('subim')
sqash=AIPSTask('sqash')

# Extract the observations summary
spectra = AIPSUVData(AIPSCat()[mydisk][0].name, AIPSCat()[mydisk][0].klass, mydisk, AIPSCat()[mydisk][0].seq)

# Read parameters passed inside the spectra data header
nChan    = round(spectra.header.naxis[2])
cellsize = round(spectra.header.cdelt[4] * 3600.)
refChan  = spectra.header.crpix[2]
imxSize  = (2*round(spectra.header.crpix[3]/1.95)) + 20
imySize  = (2*round(spectra.header.crpix[4]/1.95)) + 20
raDeg    = spectra.header.crval[3]
decDeg   = spectra.header.crval[4]
nuRef    = spectra.header.crval[2]
dNu      = spectra.header.cdelt[2]
xType    = spectra.header.ctype[3]
yType    = spectra.header.ctype[4]
bunit    = spectra.header.bunit

print 'Observing coordinates: ',xType, yType, ' Unit: ', bunit
if inRefFreqHz != 0.:
   restFreqHz = inRefFreqHz
   print "Using Rest Frequency: ", restFreqHz/1.E6, " MHz"
else:
   restFreqHz = nuRef

NH3_1_1=   23694.5060E6
#special case of favorite rest frequency (override here).
#restFreqHz = NH3_1_1

if inRa != 0:
    raDeg=inRa
if inDec != 0:
    decDeg=inDec
if inImX != 0:
    imxSize = inImX
if inImY != 0:
    imySize = inImY

print "Ra,Dec:", raDeg, decDeg, "Image:", imxSize, imySize, cellsize, 
#print spectra.header

# set number of channels to average
if inNAve > 0:
    nAverage = inNAve
else:
    nAverage = 3

if nAverage > 1:
    print 'Averaging ',nAverage,' Spectral Channels'
else:
    print 'Not Averaging Spectral Channels'
    nAverage = 1
# now average channels to reduce the image plane data volumn
avspc.indisk=mydisk
avspc.outdisk=mydisk
avspc.outclass=''
avspc.inname=AIPSCat()[mydisk][0].name
avspc.inclass=AIPSCat()[mydisk][0].klass
avspc.inseq=AIPSCat()[mydisk][0].seq
avspc.channel=nAverage
avspc.ichansel[1][1] = 1
avspc.ichansel[2][1] = nChan
avspc.ichansel[3][1] = 1
avspc.avoption='SUBS'
avspc.go()

#now have fewer channels, with broader frequencies
nChan = round(nChan/nAverage)
dNu = nAverage*dNu
refChan = refChan/nAverage

# Now make an image using the last entry in the catalog
sdgrd.indisk=mydisk
sdgrd.outdisk=mydisk
sdgrd.baddisk[1]=baddisk
sdgrd.inname=AIPSCat()[mydisk][-1].name
sdgrd.inclass=AIPSCat()[mydisk][-1].klass
sdgrd.inseq=AIPSCat()[mydisk][-1].seq
sdgrd.optype='-GLS'
sdgrd.reweight[1] = 0
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

#sdgrd.xtype=-16         # sync/bessel convolving type
sdgrd.xtype=-12         # gaussian convolving type
# sync/bessel function parameters
if sdgrd.xtype == -16:
    sdgrd.xparm[1] = 3*cellsize
    sdgrd.xparm[2] = 2.5*cellsize
    sdgrd.xparm[3] = 1.5*cellsize
    sdgrd.xparm[4] = 2
    sdgrd.reweight[2] = .01
# gaussian parameters
if sdgrd.xtype == -12:
    sdgrd.xparm[1] = 5.0*cellsize
    sdgrd.xparm[2] = 1.5*cellsize # Parameter sets Gaussian FWHM
    sdgrd.xparm[3] = 2
    sdgrd.xparm[4] = 0
    sdgrd.reweight[2] = -1.E-6
# always make a circuluar convolving function
sdgrd.ytype=sdgrd.xtype
#prevent error due to large image sizes; temporary
if imxSize > 700:
    imxSize = 150
if imySize < 30:
    imySize = 50
#prevent error due to large image sizes; temporary
if imySize > 700:
    imySize = 150

#if needed, override size here
#imxSize = 280
#imySize = 350
sdgrd.imsize[1] = imxSize
sdgrd.imsize[2] = imySize
## The above lines set the default image parameters
## Below, override imaging center coordinate
# RA
#sdgrd.aparm[1] = 04    #hours
#sdgrd.aparm[2] = 41    #minutes
#sdgrd.aparm[3] = 15.0  #seconds
# DEC
#sdgrd.aparm[4] = 25    #degrees
#sdgrd.aparm[5] = 50    #arcmins
#sdgrd.aparm[6] = 00    #arcseconds
sdgrd.go()

from Wizardry.AIPSData import AIPSImage as WizAIPSImage
image = WizAIPSImage(AIPSCat()[mydisk][-1].name, \
                     AIPSCat()[mydisk][-1].klass, \
                     mydisk, AIPSCat()[mydisk][-1].seq)

image.header.niter = 1          # Allow down stream IMSTATs to sum correctly
#print image.header
bmaj = image.header.bmaj
#assume no smoothing in convolving function (sdgrd.xtype = -16)
newBmaj = bmaj
if sdgrd.xtype == -12:
    convolveMaj = sdgrd.xparm[2]/3600. # convolving function FWHM in degrees
#Convolved image resolution adds in quadrature
    newBmaj = math.sqrt( (bmaj*bmaj) + (convolveMaj*convolveMaj))
    print 'Gaussian Convolving function:'
    print bmaj*3600., convolveMaj*3600., '->',newBmaj*3600.
if sdgrd.xtype == -16:
#Convolved image resolution adds in quadrature
    newBmaj = bmaj
    print 'Sync Bessel Convolving function FWHM :', newBmaj
image.header.bmaj = newBmaj
image.header.bmin = newBmaj
image.update()                  # This step does not seem to work!
                                # Work-around: write file, update header, read.
## keep track of the latest cube squence for later processing
outseq = AIPSCat()[mydisk][-1].seq

## Write the last Entry in the catalog to disk
fittp.indisk=mydisk
fittp.inname=AIPSCat()[mydisk][-1].name
fittp.inclass=AIPSCat()[mydisk][-1].klass
fittp.inseq=AIPSCat()[mydisk][-1].seq
restFreqName = "_%.0f_MHz" % (restFreqHz * 1.E-6)
outName = AIPSCat()[mydisk][-1].name + restFreqName
outimage = outName+'_cube.fits'
if os.path.exists(outimage):
    os.remove(outimage)
    print 'Removed existing file to make room for new one :',outimage

fittp.dataout='PWD:'+outimage
fittp.go()

gridType = image.header.ctype[0]

#transfer coordinate back after gridding
print 'Data Coordinate type: ', xType, yType
xlen = len(xType)
if (xlen < 2):
    xType = xType + '-'
if (xlen < 3):
    xType = xType + '-'
if (xlen < 4):
    xType = xType + '-'
ylen = len(yType)
if (ylen < 2):
    yType = yType + '-'
if (ylen < 3):
    yType = yType + '-'
if (ylen < 4):
    yType = yType + '-'
print 'Padded Coordinate type: ', xType, yType
xType = xType + gridType[4:]
yType = yType + gridType[4:]
print 'Map Coordinate type: ', xType, yType

image.header.restfreq=restFreqHz
image.header.bunit='JY/BEAM'
image.header.bmaj=newBmaj
image.header.bmin=newBmaj
image.header.ctype[0]=xType
image.header.ctype[1]=yType
image.header.niter=1
image.header.update()

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
trans.inseq=outseq
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
imlin.box[1][1]=round(nChan*0.04)
imlin.box[1][2]=round(nChan*0.12)
imlin.box[1][3]=round(nChan*0.81)
imlin.box[1][4]=round(nChan*0.89)
imlin.order=0  # beware using imlin.order=1; use imlin.order=0
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

