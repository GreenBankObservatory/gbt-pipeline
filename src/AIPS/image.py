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

import math
import os
import sys

import argparse
from AIPSData import *
from AIPSTask import AIPSTask

from fixAipsImages import fixAipsImages
import aips_utils

if os.path.dirname(os.path.realpath(__file__)).endswith('contrib'):
    # if we're in the contrib/ directory, that means we are running
    # the old 'contrib/mapDefault.py' command.  Prepend the src/ directory
    # to the pythonpath to get the fixaAipsImages and aips_utils modules
    srcdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, srcdir)

DISK_ID = 1                        # choose a good default work disk
BADDISK = 0                       # list a disk to avoid (0==no avoidance)
cat = aips_utils.Catalog()


def print_header(message):
    print ""
    print "-" * len(message)
    print message
    print "-" * len(message)
    print ""


def ra_deg2hms(degrees):
    full_hours = degrees / 15
    hours = math.floor(full_hours)

    full_minutes = (full_hours - hours) * 60
    minutes = math.floor(full_minutes)

    seconds = round((full_minutes - minutes) * 60)
    return hours, minutes, seconds


def dec_deg2hms(degrees):
    hours = math.floor(degrees)
    minutes = math.floor((degrees - hours) * 60)
    seconds = round((((degrees - hours) * 60) - minutes) * 60)
    return hours, minutes, seconds


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
    parser.add_argument('-a', '--average', type=int, default=1,
                        help="Number of channels to average")
    parser.add_argument('-c',  '--center', metavar=('RA', 'DEC'), type=float, nargs=2,
                        help="Map center right ascension and declination (degrees)")
    parser.add_argument('-s', '--size', metavar=('X', 'Y'), type=int, nargs=2,
                        help="Image X,Y size (pixels)")
    parser.add_argument('-u', '--unique-file-string', type=str, dest="uniqueid", default="",
                        help="Unique identifier for outfile names "
                        "(e.g. 125_130 to represent scans 125-130)")
    parser.add_argument('-r', '--restfreq', type=float, help="Rest frequency (MHz)")
    parser.add_argument('--noave', action='store_true', help="Disable average map")
    parser.add_argument('--noline', action='store_true', help="Disable line cube")

    args = parser.parse_args()

    cat.config(args.aipsid, DISK_ID)

    return args


def average_channels(binsize):
    if binsize > 1:
        print 'Averaging ', binsize, ' Spectral Channels'
    else:
        print 'Not Averaging Spectral Channels'
        return

    avspc = AIPSTask('avspc')

    last = cat.last_entry()
    spectra = cat.get_uv(last)
    nChan = round(spectra.header.naxis[2])
    print spectra.header.naxis, nChan

    # now average channels to reduce the image plane data volumn
    avspc.indisk = avspc.outdisk = DISK_ID
    avspc.outclass = ''
    avspc.inname = last.name
    avspc.inclass = last.klass
    avspc.inseq = last.seq
    avspc.channel = binsize
    avspc.ichansel[1][1] = 1
    avspc.ichansel[2][1] = nChan
    avspc.ichansel[3][1] = 1
    avspc.avoption = 'SUBS'
    avspc.outcl = 'avg'
    avspc.go()

    # now have fewer channels, with broader frequencies
    spectra.header.naxis[2] = round(nChan / binsize)  # write back to header
    print 'naxis', spectra.header.naxis
    print 'cdelt', spectra.header.cdelt
    dNu = spectra.header.cdelt[2]
    dNu = binsize * dNu  # write back to header !!!
    print 'cdelt', spectra.header.cdelt, 'dNu', dNu, 'binsize', binsize

    refChan = spectra.header.crpix[2]
    print 'refChan', refChan, 'crpix', spectra.header.crpix
    refChan = refChan / binsize  # write back to header !!!
    print 'refChan', refChan, 'crpix', spectra.header.crpix
    return


def update_header(args):
    sdgrd = AIPSTask('sdgrd')

    first = cat.get_entry(0)
    spectra = cat.get_uv(first)

    xType, yType = spectra.header.ctype[3], spectra.header.ctype[4]
    bunit = spectra.header.bunit
    print 'Observing coordinates: {0}, {1}   Unit {2}'.format(xType, yType, bunit)

    last = cat.last_entry()
    image = cat.get_image(last)

    image.header.niter = 1          # Allow down stream IMSTATs to sum correctly
    bmaj = image.header.bmaj
    newBmaj = bmaj

    if sdgrd.xtype == -12:
        convolveMaj = sdgrd.xparm[2]/3600.  # convolving function FWHM in degrees
        # Convolved image resolution adds in quadrature
        newBmaj = math.sqrt((bmaj*bmaj) + (convolveMaj*convolveMaj))
        print 'Gaussian Convolving function:'
        print bmaj*3600., convolveMaj*3600., '->', newBmaj*3600.

    if sdgrd.xtype == -16:
        # assume no smoothing in convolving function (sdgrd.xtype = -16)
        # Convolved image resolution adds in quadrature
        newBmaj = bmaj
        print 'Sync Bessel Convolving function FWHM :', newBmaj

    image.header.bmaj = newBmaj
    image.header.bmin = newBmaj
    image.update()

    # transfer coordinate back after gridding
    print 'Data Coordinate type   : ', xType, yType
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

    print 'Padded Coordinate type : ', xType, yType
    gridType = image.header.ctype[0]
    xType = xType + gridType[4:]
    yType = yType + gridType[4:]
    print 'Map Coordinate type    : ', xType, yType

    # Read parameters passed inside the spectra data header
    if 'restfreq' in args and args.restfreq:
        restFreqHz = args.restfreq * 1e6  # convert to Hz
    else:
        restFreqHz = spectra.header.restfreq

    image.header.restfreq = restFreqHz
    image.header.bunit = 'JY/BEAM'
    image.header.bmaj = newBmaj
    image.header.bmin = newBmaj
    image.header.ctype[0] = xType
    image.header.ctype[1] = yType
    image.header.niter = 1
    image.header.update()

    return last.seq, restFreqHz


def write_fits(outname):
    fittp = AIPSTask('fittp')

    # Write the last Entry in the catalog to disk
    fittp.indisk = DISK_ID
    last = cat.last_entry()
    fittp.inname = last.name
    fittp.inclass = last.klass
    fittp.inseq = last.seq
    if os.path.exists(outname):
        os.remove(outname)
        print 'Removed existing file to make room for new one :', outname
    fittp.dataout = 'PWD:' + outname
    fittp.go()


def make_average_map(restfreq, uniqueid):
    print_header("Making average map")
    sqash = AIPSTask('sqash')

    # squash the frequency axis to make a continuum image
    sqash.indisk = DISK_ID
    sqash.outdisk = DISK_ID
    last = cat.last_entry()
    sqash.inname = last.name
    sqash.inclass = last.klass
    sqash.inseq = last.seq
    sqash.bdrop = 3  # squash frequency axis
    sqash.go()

    outcont = write_average_map(restfreq, uniqueid)
    return outcont


def remove_continuum(outseq):
    trans = AIPSTask('trans')
    imlin = AIPSTask('imlin')

    entry = cat.get_entry(1)    # get SDGRD entry
    img = cat.get_image(entry)
    nChan = round(img.header.naxis[2])

    # transpose image in order to run IMLIN
    trans.indisk = DISK_ID
    trans.outdisk = DISK_ID
    trans.baddisk[1] = BADDISK
    trans.inname = entry.name
    trans.inclass = 'SDGRD'
    trans.inseq = outseq
    trans.transc = '312'
    trans.outcl = 'trans'
    trans.go()

    # Run imlin task on trans file
    # remove a spectral baseline.  Output image is in Freq-RA-Dec order
    # (Transcod 312)
    imlin.indisk = DISK_ID
    imlin.outdisk = DISK_ID
    imlin.outcl = 'IMLIN'
    last = cat.last_entry()
    imlin.inname = last.name
    imlin.inclass = last.klass
    imlin.inseq = last.seq
    imlin.nbox = 2
    # use only the end channels for the default baseline fits
    imlin.box[1][1] = round(nChan * 0.04)  # 4-12%
    imlin.box[1][2] = round(nChan * 0.12)
    imlin.box[1][3] = round(nChan * 0.81)  # 82-89%
    imlin.box[1][4] = round(nChan * 0.89)

    imlin.order = 0  # polynomial order
    print 'IMLIN box', imlin.box
    imlin.go()

    # Run transpose again task on sdgrd file produced by IMLIN
    last = cat.last_entry()
    trans.inname = last.name
    trans.inclass = last.klass
    trans.inseq = last.seq
    trans.transc = '231'
    trans.outdi = DISK_ID
    trans.outcl = 'baseli'
    trans.go()


def write_line_cube(restfreq, uniqueid):
    last = cat.last_entry()
    source = last.name.replace(" ", "")
    freq = "_%.0f_MHz" % (restfreq * 1e-6)
    outfilename = source + uniqueid + freq + "_line.fits"
    write_fits(outfilename)
    return outfilename


def make_cube_minus_continuum(restfreq, seqno, uniqueid):
    print_header("Making cube minus continuum")

    remove_continuum(seqno)
    outline = write_line_cube(restfreq, uniqueid)
    return outline


def write_image_cube(restfreq, uniqueid):
    last = cat.last_entry()
    source = last.name.replace(" ", "")
    freq = "_%.0f_MHz" % (restfreq * 1e-6)
    outfilename = source + uniqueid + freq + "_cube.fits"
    write_fits(outfilename)
    return outfilename


def write_average_map(restfreq, uniqueid):
    last = cat.last_entry()
    source = last.name.replace(" ", "")
    freq = "_%.0f_MHz" % (restfreq * 1e-6)
    outfilename = source + uniqueid + freq + "_cont.fits"
    write_fits(outfilename)
    return outfilename


def make_cube(args):

    print_header("Making image cube")

    average_channels(args.average)

    sdgrd = AIPSTask('sdgrd')

    # Now make an image using the last entry in the catalog
    sdgrd.indisk = DISK_ID
    sdgrd.outdisk = DISK_ID
    sdgrd.baddisk[1] = BADDISK
    last = cat.last_entry()
    sdgrd.inname = last.name
    sdgrd.inclass = last.klass
    sdgrd.inseq = last.seq
    sdgrd.optype = '-GLS'
    sdgrd.reweight[1] = 0

    spectra = cat.get_uv(last)
    if 'center' in args and args.center:
        raDeg, decDeg = args.center
    else:
        raDeg, decDeg = spectra.header.crval[3], spectra.header.crval[4]

    # must break up RA into hours minutes seconds
    hh, mm, ss = ra_deg2hms(raDeg)
    sdgrd.aparm[1] = hh
    sdgrd.aparm[2] = mm
    sdgrd.aparm[3] = ss

    # now break up degrees, but must preserve sign
    decSign = 1
    if decDeg < 0:
        decSign = -1
        decDeg = -1 * decDeg

    hh, mm, ss = dec_deg2hms(decDeg)
    sdgrd.aparm[4] = hh
    sdgrd.aparm[5] = mm
    sdgrd.aparm[6] = ss

    # deal with degrees and/or minutes == 0
    if decSign < 0.:
        sdgrd.aparm[4] = -1 * sdgrd.aparm[4]
        if sdgrd.aparm[4] == 0:
            sdgrd.aparm[5] = -1 * sdgrd.aparm[5]
            if sdgrd.aparm[5] == 0:
                sdgrd.aparm[6] = -1 * sdgrd.aparm[6]

    print raDeg, decDeg, '->', sdgrd.aparm[1:7]

    # transfer cellsize
    cellsize = round(spectra.header.cdelt[4] * 3600.)
    sdgrd.cellsize[1] = sdgrd.cellsize[2] = cellsize

    # sdgrd.xtype=-16         # sync/bessel convolving type
    sdgrd.xtype = -12         # gaussian convolving type

    # sync/bessel function parameters
    if sdgrd.xtype == -16:
        sdgrd.xparm[1] = 3.0 * cellsize
        sdgrd.xparm[2] = 2.5 * cellsize
        sdgrd.xparm[3] = 1.5 * cellsize
        sdgrd.xparm[4] = 2
        sdgrd.reweight[2] = .01

    # gaussian parameters
    if sdgrd.xtype == -12:
        sdgrd.xparm[1] = 5.0 * cellsize
        sdgrd.xparm[2] = 1.5 * cellsize  # Parameter sets Gaussian FWHM
        sdgrd.xparm[3] = 2
        sdgrd.xparm[4] = 0
        sdgrd.reweight[2] = -1.E-6

    # always make a circuluar convolving function
    sdgrd.ytype = sdgrd.xtype

    if 'size' in args and args.size:
        imxSize, imySize = args.size
    else:
        imxSize = (2 * round(spectra.header.crpix[3] / 1.95)) + 20
        imySize = (2 * round(spectra.header.crpix[4] / 1.95)) + 20

    print "Ra, Dec          : {0}, {1}".format(raDeg, decDeg)
    print "Image size (X,Y) : {0}, {1}".format(imxSize, imySize)
    print "Cell size        : {0}".format(cellsize)

    sdgrd.imsize[1] = imxSize
    sdgrd.imsize[2] = imySize
    sdgrd.go()

    seqno, restFreqHz = update_header(args)
    outcube = write_image_cube(restFreqHz, args.uniqueid)

    return seqno, restFreqHz, outcube

if __name__ == '__main__':

    args = read_command_line(sys.argv)
    print args

    outfiles = []
    try:
        seqno, restFreqHz, outcube = make_cube(args)  # make the image cube
        outfiles.append(outcube)
    except ValueError, msg:
        print 'ERROR: ', msg
        print 'Please run this command on: ',
        print 'arcturus.gb.nrao.edu'
        print 'If you are on arcturus, please report this error.'
        sys.exit(-1)
    except:
        print('ERROR: There was a problem making the image cube.  Please '
              'see the log files for details')
        sys.exit(-3)

    # make the moment 0 map
    if not args.noave:
        outcont = make_average_map(restFreqHz, args.uniqueid)
        outfiles.append(outcont)

    if not args.noave and not args.noline:
        outline = make_cube_minus_continuum(restFreqHz, seqno, args.uniqueid)
        outfiles.append(outline)

    cat.show()
    fixAipsImages(outfiles)
