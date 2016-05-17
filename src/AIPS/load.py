# Copyright (C) 2013 Associated Universities, Inc. Washington DC, USA.
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

import os
import sys

import argparse
from AIPSTask import AIPSTask

import AIPS
import aips_utils

if os.path.dirname(os.path.realpath(__file__)).endswith('contrib'):
    # if we're in the contrib/ directory, that means we are running
    # the old 'contrib/dbcon.py' command.  Prepend the src/ directory
    # to the pythonpath to get the aips_utils module
    srcdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, srcdir)

DISK_ID = 1                        # choose a good default work disk
BADDISK = 0                       # list a disk to avoid (0==no avoidance)
cat = aips_utils.Catalog()   # initialize a catalog object
tmpfn = 'tmpUvlodFile.fits'


def print_header(message):
    print ""
    print "-" * len(message)
    print message
    print "-" * len(message)
    print ""


def read_command_line(argv):
    """Read options from the command line."""
    # if no options are set, print help
    if len(argv) == 1:
        argv.append('-h')

    parser = argparse.ArgumentParser(description='Run the AIPS dbcon task to load '
                                     'calibrated spectra for imaging.')
    parser.add_argument('aipsid', type=int,
                        help=("The AIPS catalog number to use.  This is typically "
                              "your system id, which you can find by typing "
                              "'id -u' at the command line."))
    parser.add_argument('--empty-catalog', dest='empty_catalog', action='store_true',
                        default=False, help='If set, will empty the AIPS catalog '
                        'without prompt before processing.  Otherwise, the user is '
                        'prompted to override the default False setting.')
    parser.add_argument('files', type=str, nargs='+',
                        help="Names of files (*.aips.fits) to load into AIPS (space-separated)")
    args = parser.parse_args()

    cat.config(args.aipsid, DISK_ID)  # configure the catalog object

    # start with a clean slate by trying to empty the catalog
    cat.empty(args.empty_catalog)

    return args.files


def load_into_aips(myfiles):
    """Load files into AIPS with UVLOD task."""

    # mandl = AIPSTask('mandl')
    # mandl.outdisk = DISK_ID
    # mandl.go()

    print_header("Loading data into AIPS")

    uvlod = AIPSTask('uvlod')
    uvlod.outdisk = DISK_ID            # write all input data to a select disk
    uvlod.userno = AIPS.userno

    first_file = True   # to help determine center freq to use

    for this_file in myfiles:        # input all AIPS single dish FITS files
        if not os.path.exists(this_file):
            print 'WARNING: can not find file: {0}'.format(this_file)
            continue

        print 'Adding {0} to AIPS.'.format(this_file)

        # AIPS has problems with long filenames so we create a symlink to a short filename
        if os.path.exists(tmpfn):
            os.unlink(tmpfn)

        os.symlink(this_file, tmpfn)
        uvlod.datain = 'PWD:' + tmpfn
        uvlod.go()
        os.unlink(tmpfn)  # remove the temporary symlink

        # get the center frequency of the sdf file that was just loaded
        last = cat.last_entry()
        spectra = cat.get_uv(last)
        center_freq = spectra.header.crval[2]

        # if this is the first file loaded, look for
        # the same frequency in the next ones
        if first_file:
            expected_freq = center_freq
            first_file = False

        # if frequency of sdf file just loaded and 1st file differ by
        # more than 100 kHz, do not use the current file
        if abs(expected_freq - center_freq) > 1e5:
            print 'Frequencies differ: {0} != {1}'.format(center_freq, expected_freq)
            print '  Rejecting {0}'.format(this_file)
            spectra.zap()


def run_dbcon(entryA, entryB):
    """Combine the data in AIPS with the DBCON task"""
    dbcon = AIPSTask('dbcon')

    # always do firs
    dbcon.indisk = dbcon.outdisk = dbcon.in2disk = DISK_ID
    dbcon.userno = AIPS.userno

    file1 = cat.get_entry(entryA)
    dbcon.inname = file1.name
    dbcon.inclass = file1.klass
    dbcon.inseq = file1.seq

    file2 = cat.get_entry(entryB)
    dbcon.in2name = file2.name
    dbcon.in2class = file2.klass
    dbcon.in2seq = file2.seq

    dbcon.reweight[1] = 0
    dbcon.reweight[2] = 0

    print 'combining: ', dbcon.inname, dbcon.inclass, dbcon.inseq
    print '     with: ', dbcon.in2name, dbcon.in2class, dbcon.in2seq

    dbcon.go()


def print_source_names():
    n_files = len(cat)

    source_names = set([])
    for x in range(n_files):
        entry = cat.get_entry(x)
        uvdata = cat.get_uv(entry)
        source_names.add(uvdata.header.object)

    print len(source_names), 'object(s) observed:', ', '.join(source_names)


def combine_files():
    """A containing function that chooses when to run the AIPS DBCON task."""

    print_header("Combining catalog DBCON files")

    n_files = len(cat)
    print_source_names()

    # if more than 1 file combine them with DBCON
    if n_files > 1:

        run_dbcon(0, 1)

        # and keep adding in one if there are more
        for ii in range(2, n_files):
            run_dbcon(-1, ii)

        # remove uv files
        for ii in range(n_files):
            cat.zap_entry(0)


def time_sort_data():
    """Time-sort data in AIPS with the UVSRT task."""

    print_header("Time-sorting data")

    uvsrt = AIPSTask('uvsrt')
    uvsrt.userno = AIPS.userno

    # -------------------------------------------------------------------------
    #    UVSRT the data
    # -------------------------------------------------------------------------

    # sort data to prevent down stream problems
    uvsrt.indisk = uvsrt.outdisk = DISK_ID
    uvsrt.baddisk[1] = BADDISK
    uvsrt.outcl = 'UVSRT'
    uvsrt.sort = 'TB'
    last = cat.last_entry()
    uvsrt.inname = last.name
    uvsrt.inclass = last.klass
    uvsrt.inseq = last.seq

    # will write to entry 1 because input sdf/uv files were removed
    uvsrt.go()

    nfiles = len(cat)

    for dbcon_entry in range(nfiles-1):
        cat.zap_entry(-1)  # remove the DBCON entries


def print_summary():
    """Print a simple summary to the screen of image RA/DEC and size."""

    print_header("Data summary")

    # Extract the observations summary
    last = cat.last_entry()
    spectra = cat.get_uv(last)

    # and read parameters passed inside the spectra data header
    freq = spectra.header.crval[2]
    raDeg = spectra.header.crval[3]
    decDeg = spectra.header.crval[4]
    imxSize = 2 * round(spectra.header.crpix[3] / 1.5)
    imySize = 2 * round(spectra.header.crpix[4] / 1.5)
    cellsize = round(spectra.header.cdelt[4] * 3600.)

    print "Center Freq. (GHz)  : {0:.2f}".format(freq/1e9)
    print "Ra, Dec             : {0:.2f}, {1:.2f}".format(raDeg, decDeg)
    print "Image x,y           : {0}, {1}".format(imxSize, imySize)
    print "Cell size (arcsec)  : {0}".format(cellsize)

if __name__ == '__main__':
    aips_filenames = read_command_line(sys.argv)

    for ff in aips_filenames:
        if not os.path.exists(ff):
            print 'ERROR: can not find file', ff

    try:
        load_into_aips(aips_filenames)
    except ValueError, msg:
        print 'ERROR: ', msg
        print 'Please run this command on: ',
        print 'arcturus.gb.nrao.edu'
        print 'If you are on arcturus, please report this error.'
        sys.exit(-1)
    except RuntimeError, msg:
        print 'ERROR: ', msg
        print 'Check format of input files.'
        if os.path.exists(tmpfn):
            os.unlink(tmpfn)
        sys.exit(-1)

    # if any files were loaded into the catalog, do other steps
    if len(cat) > 0:
        combine_files()
        time_sort_data()
        print_summary()

    cat.show()
