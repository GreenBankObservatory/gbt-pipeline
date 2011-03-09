# parsel-tongue script tuned for 200 MHz bw obs of NH3
#HISTORY
#10OCT20 GIL clean up comments and more help
#10OCT13 GIL add more comments and write out the Temperature image
#10OCT06 GIL measure the NH3 1-1 integrated profile only

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

print 'Number of arguments:', argc
if argc < 5:
    print 'tempNH3-11-22: Compute temperature map from NH3 11 and 22 obs.'
    print 'usage: tempNH3-11-22 <aipsNumber> <outName> <velocityKmS> <velWidthKmS> <fluxMin>'
    print 'where <aipsNumber>  your *PIPELINE* AIPS number (should always be the same)'
    print '      <outName>     Initial part of Name of output temperature map'
    print '      <velocityKmS> Source Velocity in km/sec'
    print '      <velWidthKmS> Source Velocity width to Sum (km/sec)'
    print '      <fluxMin>     Minimum Intensity to include sum (- for +/- values)'
    print '                    Pick 1-3 sigma to blank out noise'

AIPS.userno=int(sys.argv[1])        # Extract AIPS pipeline number
print 'User Number:', AIPS.userno
outName = sys.argv[2]               # Extract Integrated Line Name
velocityKmS = 0.                    # Default velocity (km/s)
velWidthKmS = 10.                   # Default velocity Full Width (km/s)
fluxMin = -0.050                    # Default Minimum flux for sum (K)

if argc > 3:
    velocityKmS = float(sys.argv[3])# velocity (km/s)
if argc > 4:
    velWidthKmS = float(sys.argv[4])# velocity Full Width (km/s)
if argc > 5:
    fluxMin = float(sys.argv[5])    # minimum flux to include in sum

mydisk=2                            # default AIPS disk drive

sigma = fluxMin
if sigma < 0:
    sigma = -sigma
    
print 'Outname : ',outName
print 'Velocity: ',velocityKmS,' (km/s)'
print 'VelWidth: ',velWidthKmS,' (km/s FWHM)'
print 'Flux Min: ',fluxMin, ' (K)'

fittp=AIPSTask('fittp')
momnt=AIPSTask('momnt')
subim=AIPSTask('subim')
comb=AIPSTask('comb')

print 'mydisk:',mydisk
# This proceedure assumes calibrated data are already loaded into AIPS
# and the first images are produced.  A spectral baseline must be subtracted
image = AIPSImage(AIPSCat()[mydisk][-1].name, 'IMLIN', mydisk, 1)
#image = WizAIPSImage(AIPSCat()[mydisk][-1].name, 'IMLIN', mydisk, 1)

# now read parameters passed inside the data header
nChan    = round(image.header.naxis[0])
refChan  = image.header.crpix[0]
nuRef    = image.header.crval[0]
dNu      = image.header.cdelt[0]

print nChan, refChan, nuRef, dNu

cLightKmS = 299792.458  # speed of light in Km/Sec

#define the two rest frequencies used
restFreq11 = 23694.506 * 1.e6
restFreq22 = 23722.633 * 1.e6
#start with 11 line
restFreq = restFreq11

#These constants are particular to each source
sourceLineWidthHz = .2E6

sourceFreq = restFreq*(1.-(velocityKmS/cLightKmS))
print 'Source Frequency:',sourceFreq*1.E-6,'+/-', \
  dNu*1.E-6,' MHz'
#now set the default line channels and widths
lineWidthChan = 100
lineChan = round(nChan*.5)

#Compute number of channels from the Velocity width
if dNu != 0:
    lineWidthChan = round(velWidthKmS * sourceFreq/(dNu * cLightKmS))
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
momnt.flux=fluxMin
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
subim.outclass='11'
subim.outdi=mydisk
subim.go()

#Next the 22 line
restFreq = restFreq22

sourceFreq = restFreq*(1.-(velocityKmS/cLightKmS))
print 'Source Frequency:',sourceFreq*1.E-6,'+/-', \
  dNu*1.E-6,' MHz'
#now set the default line channels and widths
lineWidthChan = 100
lineChan = round(nChan*.5)

#Compute number of channels from the Velocity width
if dNu != 0:
    lineWidthChan = round(velWidthKmS * sourceFreq/(dNu * cLightKmS))
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

## Use the subim task to rename the output image
subim.indisk=mydisk
subim.inname=AIPSCat()[mydisk][-1].name
subim.inclass=AIPSCat()[mydisk][-1].klass
subim.inseq=AIPSCat()[mydisk][-1].seq
subim.outclass='22'
subim.outdi=mydisk
subim.go()

#make a unit image for later use
comb.outdisk=mydisk
comb.indisk=mydisk
comb.inname=AIPSCat()[mydisk][-1].name
comb.inclass=AIPSCat()[mydisk][-1].klass
comb.inseq=AIPSCat()[mydisk][-1].seq
comb.in2disk=mydisk
comb.in2name=AIPSCat()[mydisk][-1].name
comb.in2class=AIPSCat()[mydisk][-1].klass
comb.in2seq=AIPSCat()[mydisk][-1].seq
comb.aparm[1]=1.
comb.aparm[2]=-1.
comb.aparm[3]=1.
comb.opcode='SUM'
comb.outcl='ONE'
comb.go()

#make a N(2,2) image
comb.aparm[1] = cLightKmS*(6./4.)*1.55e14/(restFreq22*restFreq22*1.E-9)
comb.aparm[2] = 1.E-10
comb.aparm[3] = 0
comb.aparm[4] = 0
comb.outcl='N(2,2)'
comb.opcode='SUM'
comb.go()

#make a N(1,1) image
comb.aparm[1] = cLightKmS*(2./1.)*1.55e14/(restFreq11*restFreq11*1.E-9)
comb.inclass='11'
comb.in2class='11'
comb.outcl='N(1,1)'
comb.go()

#now make the log10 (N1,1) image
comb.inclass='N(1,1)'
comb.in2class='ONE'
comb.opcode='OPTD'
comb.aparm[1]=1./2.3025851
comb.aparm[2]=0.
comb.aparm[3]=1./3.
comb.aparm[4]=0.
comb.bparm[1] = 0
comb.bparm[2] = 0
comb.bparm[4] = 0
comb.bparm[5] = 0
comb.outcl='LOG-11'
comb.go()

#now make the log10 (N2,2) image
comb.inclass='N(2,2)'
comb.in2class='ONE'
comb.opcode='OPTD'
comb.aparm[1]=1./2.3025851   # 1. / ln(10.)
comb.aparm[2]=0.
comb.aparm[3]=1./5.
comb.aparm[4]=0.
comb.outcl='LOG-22'
comb.go()

#now make the dY image
comb.inclass='LOG-22'
comb.in2class='LOG-11'
comb.opcode='SUM'
comb.aparm[1]=1.
comb.aparm[2]=-1.
comb.aparm[3]=0.
comb.aparm[4]=0.
comb.outcl='DY'
comb.go()

#Temperature difference between 11 and 22 line
dX = 41.5 # Kelvin
#finally make the Trot image
comb.inclass='ONE'
comb.in2class='DY'
comb.opcode='DIV'
comb.outcl = 'TROT'
comb.aparm[1] = -.434*dX
comb.aparm[2] = 0.
comb.aparm[3] = 0.
comb.go()

comb.inclass='TROT'
comb.in2class='TROT'
comb.opcode='CLIP'
comb.outcl = 'T CLIP'
comb.aparm[1] = -1.    # Minimum temp
comb.aparm[2] = 100.   # Maximum temp; arbitrary 
comb.aparm[3] = 0.
comb.go()


## and write the last thing now in the catalog to disk
fittp.indisk=mydisk
fittp.inname=AIPSCat()[mydisk][-1].name
fittp.inclass=AIPSCat()[mydisk][-1].klass
fittp.inseq=AIPSCat()[mydisk][-1].seq
outimage = outName+'_T_11_22.fits'
if os.path.exists(outimage):
    os.remove(outimage)
    print 'Removed existing file to make room for new one :',outimage

fittp.dataout='PWD:'+outimage
fittp.go()
