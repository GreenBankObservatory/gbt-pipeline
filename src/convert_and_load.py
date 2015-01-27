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

# parsel-tongue script that performs only the default processing
#HISTORY
#11MAR04 GIL add more messages and fix dbcon
#10DEC16 GIL sort uvdata to final slot; this fixes some data issues.
#10DEC02 GIL assure final dbcon is in the first catalog slot
#10DEC01 GIL merge all spectra in single dish format
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
import argparse

import pyfits

def run_idlToSdfits(files, average, channels, display_idlToSdfits,
               idlToSdfits_rms_flag, verbose, idlToSdfits_baseline_subtract):

    
    # set the idlToSdfits output file name
    for infile in files:
        aipsinname = '_'.join(infile.split('_')[:-1])+'.aips.fits'
    
    # run idlToSdfits, which converts calibrated sdfits into a format
    options = ''

    if int(average):
        options = options + ' -a ' + average
    
    if bool(channels):
        options = options + ' -c ' + channels + ' '
    
    if not int(display_idlToSdfits):
        options = options + ' -l '
    
    if int(idlToSdfits_rms_flag):
        options = options + ' -n ' + idlToSdfits_rms_flag + ' '
        
    if int(verbose) > 4:
        options = options + ' -v 2 '
    else:
        options = options + ' -v 0 '
    
    if int(idlToSdfits_baseline_subtract):
        options = options + ' -w ' + idlToSdfits_baseline_subtract + ' '
        
    idlcmd = '/home/gbtpipeline/bin/idlToSdfits -o ' + aipsinname + options + ' '.join(files)
    
    print 'DBG',idlcmd
    os.system(idlcmd)

    # Note original SDFITS VELDEF value in HISTORY
    try:
        f0 = pyfits.open(files[0],mode='readonly',memmap=True)
        veldef = f0[1].data.field('veldef')[0]
        hist = '  SDFITS VELDEF = "%s"' % veldef
        f0.close()
        sdf = pyfits.open(aipsinname,mode='update',memmap=True)
        sdf[0].header.add_history(hist,after='VELREF')
        sdf.close()
    except:
        print "Unable to note original SDFITS VELDEF value in aips file(s).  Final frequency axis may be wrong."
    
    return aipsinname

def read_command_line(argv):
    """Read options from the command line."""
    # if no options are set, print help
    if len(argv) == 1:
        argv.append('-h')

    parser = argparse.ArgumentParser()
    parser.add_argument('aipsid', type=int,
                        help=("The AIPS catalog number to use.  This is typically "
                              "your system id, which you can find by typing "
                              "'id -u' at the command line."))
    parser.add_argument('--feeds', type=str)
    parser.add_argument('--average', type=str, help="Number of channels to average")
    parser.add_argument('--channels', type=str)
    parser.add_argument('--display_idlToSdfits', type=str)
    parser.add_argument('--idlToSdfits_rms_flag', type=str)
    parser.add_argument('--verbose', type=str)
    parser.add_argument('--idlToSdfits_baseline_subtract', type=str)
    parser.add_argument('--keeptempfiles', type=str)
    parser.add_argument('imfiles', type=str, nargs='+')

    args = parser.parse_args()

    return args
    
def dbcon(args):
    if not args.imfiles:
        return
    
    aips_files = []
    for feed in args.feeds.split(','):
        files = []
        for xx in args.imfiles:
            if 'feed{num}_'.format(num=feed) in xx:
                files.append(xx)
        
        if not files:
            continue
            
        aipsfile = run_idlToSdfits(files, args.average, args.channels,
                                   args.display_idlToSdfits,
                                   args.idlToSdfits_rms_flag, args.verbose,
                                   args.idlToSdfits_baseline_subtract)
        aips_files.append(aipsfile)
        
    AIPS.userno=args.aipsid         # retrieve AIPS pipeline user number
    mydisk=2                        # choose a good default work disk
    baddisk=1                       # list a disk to avoid (0==no avoidance)
    
    AIPSCat().zap()                 # empty the catalog
    
    uvlod=AIPSTask('uvlod')         # Create structures for AIPS tasks
    uvlod.outdisk=mydisk            # write all input data to a select disk
    fittp=AIPSTask('fittp')
    dbcon=AIPSTask('dbcon')
    uvsrt=AIPSTask('uvsrt')
    mandl=AIPSTask('mandl')
    
    # Need a temporary small file to reserve slot 1
    mandl.outdisk = mydisk
    # create an image that will be deleted at end
    mandl.go()
    
    #
    kount = 0                       # init count of similar input files
    
    for thisFile in aips_files:        # input all AIPS single dish FITS files
        uvlod.datain='PWD:'+thisFile
        print uvlod.datain
        uvlod.outdisk=mydisk
        uvlod.go()
        spectra = AIPSUVData(AIPSCat()[mydisk][-1].name, AIPSCat()[mydisk][-1].klass, mydisk, AIPSCat()[mydisk][-1].seq)
        nuRef    = spectra.header.crval[2]
        if kount == 0:
            firstNu = nuRef
        if ((firstNu - nuRef) < -1.E5) or ((firstNu - nuRef) > 1.E5):
            print 'Frequencies differ: ',nuRef,' != ',firstNu
            spectra.zap()
        else:
            kount = kount+1
    
    spectra = AIPSUVData(AIPSCat()[mydisk][-1].name, AIPSCat()[mydisk][-1].klass, mydisk, AIPSCat()[mydisk][-1].seq)
    
    # prepare to accumulate source names
    allObjects = ["","","","","","","","","","","","","","","","","","","",
                      "","","","","","","","","","","","","","","","","","",""]
    allObjects[0] = spectra.header.object
    nObjects = 1
    
    if kount > 1:            # if more than 1 file DBCON them
    
        # always do first 2
        dbcon.indisk=mydisk
        dbcon.outdisk=mydisk
        dbcon.in2disk=mydisk
        dbcon.inname = AIPSCat()[mydisk][1].name
        dbcon.inclass = AIPSCat()[mydisk][1].klass
        dbcon.inseq = AIPSCat()[mydisk][1].seq
        dbcon.in2name = AIPSCat()[mydisk][2].name
        dbcon.in2class = AIPSCat()[mydisk][2].klass
        dbcon.in2seq = AIPSCat()[mydisk][2].seq
        print 'combining 1: ', dbcon.inname, dbcon.inclass, dbcon.inseq
        print 'combining 2: ', dbcon.in2name, dbcon.in2class, dbcon.in2seq
        dbcon.reweight[1] = 0
        dbcon.reweight[2] = 0
        dbcon.go()
    
        # and keep adding in one
        for i in range(2,kount):
            # end of cat is always most recent dbcon result
            dbcon.inname = AIPSCat()[mydisk][-1].name
            dbcon.inclass = 'DBCON'
            dbcon.inseq = i - 1
            dbcon.in2name = AIPSCat()[mydisk][i+1].name
            dbcon.in2class = AIPSCat()[mydisk][i+1].klass
            dbcon.in2seq = AIPSCat()[mydisk][i+1].seq
            print 'combining 1: ', dbcon.inname, dbcon.inclass, dbcon.inseq
            print 'combining 2: ', dbcon.in2name, dbcon.in2class, dbcon.in2seq
            #prepare to zap revious dbconned file
            dbcon.go()
            # now zap previous big input file 
            spectra = AIPSUVData(AIPSCat()[mydisk][-1].name, 'DBCON',mydisk, i-1)
            spectra.zap()
    
        # remove input files, must remove them in reverse to presurve catalog order
        for i in range(1,kount+1):
            j = kount+1-i
            aname = AIPSCat()[mydisk][j].name
            aclass = AIPSCat()[mydisk][j].klass
            aseq = AIPSCat()[mydisk][j].seq
            # print i, j, aname, aclass, aseq
            spectra = AIPSUVData( aname, aclass, mydisk, aseq)
            notFound = True
            # check if this object is already in the list
            for iii in range(0,nObjects):
                if (allObjects[iii] == spectra.header.object):
                    notFound = False
            # if not in the list add to list and increment count
            if (notFound):
                allObjects[nObjects] = spectra.header.object
                nObjects = nObjects+1
            spectra.zap()
    
    #print nObjects,' Object(s) Observed: ', allObjects
    objectName = allObjects[0]
    for iii in range(1,nObjects):
        if len(allObjects[iii]) > 0:
            objectName = objectName + '+' + allObjects[iii]
    
    print nObjects,' Object(s) Observed: ', objectName
    
    if nObjects > 2:
        objectName = allObjects[0] + '+' + str( nObjects-1)
    
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
    
    #now free up slot 0
    image = WizAIPSImage(AIPSCat()[mydisk][0].name, \
                         AIPSCat()[mydisk][0].klass, \
                         mydisk, AIPSCat()[mydisk][0].seq)
    image.zap()
    
    # sort data to prevent down stream probelms
    uvsrt.indisk=mydisk
    uvsrt.outdisk=mydisk
    uvsrt.baddisk[1]=baddisk
    uvsrt.outcl='UVSRT'
    uvsrt.sort='TB'
    uvsrt.inname=AIPSCat()[mydisk][-1].name
    if kount < 2:
        uvsrt.inclass=AIPSCat()[mydisk][-1].klass
        uvsrt.inseq=kount    
    else:
        uvsrt.inclass='DBCON'
        uvsrt.inseq=kount - 1
    uvsrt.go()
    
    # now clean up the last of the input files
    spectra.zap()

    if args.keeptempfiles != '1':
        [os.unlink(xx) for xx in aips_files]
        if os.path.isdir('summary'):
            [os.unlink('summary/'+xx) for xx in os.listdir('summary')]
            if not os.listdir('summary'): # rmdir if empty
                os.rmdir('summary')
    
    
if __name__ == '__main__':

    args = read_command_line(sys.argv)
    print args
    dbcon(args)
