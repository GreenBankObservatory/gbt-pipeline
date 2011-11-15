#! /usr/bin/env python

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

import sys
import os
import pyfits
import multiprocessing
import glob

import commandline
import pipeutils
from process_a_single_map import *

# -----------------------------------  interpret the command line parameters

cl = commandline.CommandLine()
opt = cl.read(sys)

# if not using automatic map detection
# try to interpret the range of scans provided by the user.
# automatic map detection works by using scan annotations.
# for example, reference scans are labeled 'OFF' and map scans
# are labeled 'MAP'.  if the scans are not annotated properly,
# the allmaps option will not work
if not opt.allmaps:
    try:
        opt.mapscans = pipeutils.parserange(opt.mapscans)
    except:
        print 'ERROR: could not parse range:',opt.mapscans
        sys.exit(10)

# numerically sort the map scans, which start as a list of strings,
# cast as integers, are sorted, then cast back into strings
opt.mapscans = [ int(xx) for xx in opt.mapscans ]
opt.mapscans.sort()
opt.mapscans = [ str(xx) for xx in opt.mapscans ]

# define the begin and end map scan numbers if the range was set by the user
beginscan = False
endscan = False
if opt.mapscans:
    beginscan = opt.mapscans[0]
    endscan = opt.mapscans[-1]

# -----------------------------------------------  look for an input file

# if it doesn't exist try to recreate it from a user supplied directory
# with the -d pipeline option.  this is the project directory populated
# with engineering FITS files
opt.infile = check_for_sdfits_file(opt.infile, opt.sdfitsdir, beginscan,\
                               endscan,opt.refscan1, opt.refscan2,\
                               opt.verbose)

# -------------------------------------------------------- configure logging
pipeline_logfile_name = 'pipeline_' + timestamp() + '.log'
logger = pipeutils.configure_logfile(opt,pipeline_logfile_name)

# ------------------------------------------------- identify imaging script

# look in integration or release contrib directories for imaging script
# if no script is found, turn imaging off

RELCONTRIBDIR = '/home/gbtpipeline/release/contrib'
TESTCONTRIBDIR = '/home/gbtpipeline/integration/contrib'
DBCONSCRIPT = '/' + 'dbcon.py'
MAPSCRIPT = '/' + 'mapDefault.py'

# if the user opted to do imaging, then check for the presence of
# the necessary imaging scripts (dbcon.py, mapDefault.py).  the path
# to the scripts depends on the version (release vs. test) of the
# pipeline which is running.
if not opt.imagingoff:

    # test version of pipeline
    if TESTCONTRIBDIR in sys.path and \
      os.path.isfile(TESTCONTRIBDIR + DBCONSCRIPT) and \
      os.path.isfile(TESTCONTRIBDIR + MAPSCRIPT):

        opt.dbconScript = TESTCONTRIBDIR + DBCONSCRIPT
        opt.mapScript = TESTCONTRIBDIR + MAPSCRIPT

    # release version of pipeline
    elif os.path.isfile(RELCONTRIBDIR + DBCONSCRIPT) and \
      os.path.isfile(RELCONTRIBDIR + MAPSCRIPT):

        opt.dbconScript = RELCONTRIBDIR + DBCONSCRIPT
        opt.mapScript = RELCONTRIBDIR + MAPSCRIPT

    else:
        doMessage(logger,msg.ERR,"ERROR: imaging script not found.")
        opt.imagingoff = True

# ---------------------------------------------------  check calibration units

#  force units to all lowercase to make later tests easier
opt.units = opt.units.lower()
ACCEPTABLE_UNITS = [ 'ta', 'ta*', 'tmb', 'tb*', 'jy', 'tatsky' ]
if not (opt.units in ACCEPTABLE_UNITS ):
    doMessage(logger,msg.ERR,'ERROR: Not able to calibrate to units of',\
              opt.units)
    doMessage(logger,msg.ERR,'       Please use one of the following:',\
              ', '.join(ACCEPTABLE_UNITS))
    sys.exit(9)

# --------------------------------------------------- print command summary

commandSummary(logger,opt)

# --------------------------------------------- define PS-mode reference scans

# if we are not doing automatic map detection, determine the scan numbers
# for the map and reference scan(s) based on the user-defined command line
# options
if not opt.allmaps:
    # setup scan numbers
    allscans = [ int(item) for item in opt.mapscans ]
    doMessage(logger,msg.INFO,"Map scans",', '.join(map(str,allscans)))

    refscans = set([])
    if opt.refscan1:
        refscans.add(opt.refscan1)
    if opt.refscan2:
        if opt.refscan2 != opt.refscan1:
            refscans.add(opt.refscan2)
        else:
            opt.refscan2 = False

    doMessage(logger,msg.INFO,"Reference scan(s)",\
        ', '.join(map(str,list(refscans))))
    doMessage(logger,msg.INFO,"---------------\n")
    
# ----------------------------------  check input file for readability

doMessage(logger,msg.DBG,'opening input sdfits file')
if not os.path.exists(opt.infile):
    doMessage(logger,msg.ERR,'ERROR: input sdfits file not readable')
    doMessage(logger,msg.ERR,'    Please check input sdfits and run again')
    sys.exit(9)

# -------------------------------------------------  name index file

if opt.infile.endswith('.acs.fits') or opt.infile.endswith('.vegas.fits'):
    # reverse the filename to only replace '.fits' at the end of the string
    # the python string replace method works from left to right
    indexfile = opt.infile[::-1].replace('stif.','xedni.',1)
    indexfile = indexfile[::-1]
else:
    doMessage(logger,msg.ERR,'input file not recognized as acs or vegas',\
      indexfile)
    sys.exit(9)

# ------------------------------------------- get sampler mask using index file

# this creates an array of masks, one for each sampler, on the input file
#** in a future version of the pipeline, we may read a set of input files
#** which are already split by sampler, thus eliminating the need for this
#** step.  other changes will also be necessary where these masks are used.
doMessage(logger,msg.DBG,'getting mask index',indexfile)
masks = pipeutils.get_masks(indexfile,opt.infile)
doMessage(logger,msg.DBG,'done')

# ----------------------------------------------- look for opacity coefficients

# retrieve the mjd for the first spectrum in the index file.  this is used
# to determine if opacity coefficients are available for this observation epoch.
start_mjd = pipeutils.get_start_mjd(indexfile)

# retrieve a list of opacity coefficients files, based on a given directory
# and filename structure
opacity_coefficients_filename = False
opacity_files = glob.glob(\
  '/users/rmaddale/Weather/ArchiveCoeffs/CoeffsOpacityFreqList_avrg_*.txt')
# sort the list of files so they are in chronological order
opacity_files.sort()

# make sure we have a reasonable zenith tau value.  this is set at the
# command line.
if opt.zenithtau and (opt.zenithtau < 0  or opt.zenithtau > 1):
    doMessage(logger,msg.ERR,'ERROR: zenith tau must be between 0 and 1.')
    sys.exit(9)

# the following will become True if start_mjd is older than available ranges
# provided in the opacity coefficients files
tooearly = False
# check the date of each opacity coefficients file
for idx,opacity_candidate_file in enumerate(opacity_files):
    dates = opacity_candidate_file.split('_')[-2:]
    mydate = []
    for date in dates:
        mydate.append(int(date.split('.')[0]))

    # set tooearly=True when start_mjd is older than available ranges
    if idx == 0 and start_mjd < mydate[0]:
        tooearly = True
        break

    if start_mjd >= mydate[0] and start_mjd < mydate[1]:
        opacity_coefficients_filename = opacity_candidate_file
        break

if not opt.zenithtau and not opacity_coefficients_filename:
    if tooearly and opt.units != 'ta':
        doMessage(logger,msg.ERR,'ERROR: Date is too early for opacities.')
        doMessage(logger,msg.ERR,'  Try setting zenith tau at command line')
        doMessage(logger,msg.ERR,'  or changing units to Ta.')
        sys.exit(9)
    else:
    # if the mjd in the index file comes after the date string in all of the
    # opacity coefficients files, then we can assume the current opacity
    # coefficients file will apply.  a date string is only added to the opacity
    # coefficients file when it is no longer the most current.
        opacity_coefficients_filename = \
          '/users/rmaddale/Weather/ArchiveCoeffs/CoeffsOpacityFreqList_avrg.txt'

# opacities coefficients filename
if opacity_coefficients_filename and \
   os.path.exists(opacity_coefficients_filename):
    doMessage(logger,msg.DBG,'Using coefficients from',\
              opacity_coefficients_filename)
    opacity_coeffs = \
        pipeutils.opacity_coefficients(opacity_coefficients_filename)
else:
    if not opt.zenithtau and not opt.units == 'ta':
        doMessage(logger,msg.WARN,'WARNING: No opacity coefficients file')
    opacity_coeffs = False

# ---------------------------------------------------------- open data file

doMessage(logger,msg.DBG,'opening fits file',opt.infile)
try:
	infile = pyfits.open(opt.infile,memmap=1,mode='readonly')
except(IOError):
    doMessage(logger,msg.ERR,'ERROR: unable to open',opt.infile)
    sys.exit(8)

# --------------------------------------------------- automatically find maps

# also get a list of samplers used for each map

# we need to set allscans, refscan1 and refscan2 for each map
# and continue.  the following returns a structure that has references,
# maps scans, and a list of samplers for each map
maps_and_samplers = pipeutils.get_maps_and_samplers(opt.allmaps,indexfile)

samplerlist = []

# ------------------------------------ identify the list of samplers to process

# if we are doing automatic map detection
if opt.allmaps:

	# copy the map structure to mymaps
    mymaps = maps_and_samplers
    # sperately store a list of samplers for each map
    for mask in masks:
        samplerlist.append(mask.keys())

# if the map and reference scan numbers are provided to the pipeline
else:
    try:
    # get a sampler map from the first map scan.  this should be the same
    # for all the map scans because they should all use the same samplers
        samplermap = maps_and_samplers[allscans[0]][1]
    except(KeyError):
        doMessage(logger,msg.ERR,'ERROR: scan',str(allscans[0]),'not in infile')
        sys.exit(8)

	 # if the feed and polarization are not provided to the pipeline,
	 # assume we are using all the samplers
    if not opt.feed and not opt.pol:
        samplerlist = samplermap.keys()

    # if either the feed or polarization are provided to the pipeline,
    # filter on feed and/or polarization
    else:
    # the following indicies are for the structure returned from
    # get_maps_and_samplers()
        FEEDINDEX = 0
        POLINDEX  = 1

        # check the feed and pol specified at the commandline
        # before including a sampler in the list. in other words,
        # filter on feed and/or sampler.

        # if a list of feed numbers is provided to the pipeline
        if opt.feed:
            try:
                inclusive = pipeutils.is_inclusive_range(opt.feed)
            except:
                doMessage(logger,msg.INFO,'ERROR: can not parse range',\
                          opt.feed)
                sys.exit(11)
            # if there are only exclusive items listed
            # add all feeds to the list so we have something to
            # subtract from.
            # for example, we may start with opt.feed='-2,-4'.
            # then, we will add all feeds for the map to
            # get (for example) opt.feed='-2,-4,1,2,3,4,5,6'.
            # then, when we parse the range we end up
            # with opt.feed='1,3,5,6'.
            if not inclusive:
                feeds = []
                for sampler in samplermap:
                    feeds.append(str(samplermap[sampler][FEEDINDEX]))
                feeds = ',' + ','.join(feeds)
                opt.feed += feeds
            try:
                opt.feed = parserange(opt.feed)
            except:
                doMessage(logger,msg.ERR,'ERROR: could not parse range',\
                          opt.feed)
                sys.exit(11)

		 # if there is a list of feeds provided, but no list of polarizations
		 # then assume all polarizations
        if opt.feed and not opt.pol:
            for sampler in samplermap:
                opt.pol.append(str(samplermap[sampler][POLINDEX]))
		 # if there is a list of polarizations provided, but no list of feeds
		 # then assume all feeds
        elif opt.pol and not opt.feed:
            for sampler in samplermap:
                opt.feed.append(str(samplermap[sampler][FEEDINDEX]))

		 # now we address the case of both feeds and polarizaitons provided to
		 # the pipeline.  this next block should execute in any case.  not that
		 # if only the feed or only the polarizaiton are provided, one of the
		 # previous statements will execute and by this point we will have both
		 # lists populated.  if both are provided to the pipeline, neither of
		 # the previous two statements will execute, but we will still have
		 # both the feed and polarization lists provided and the next statement
		 # will execute.  if neither were provided to the pipeline, then all
		 # the sampelers are used as in the first 'if' part of this if-else
		 # statement

        # add only the samplers we will process
        for sampler in samplermap:
            feed = samplermap[sampler][FEEDINDEX]
            pol = samplermap[sampler][POLINDEX]
            if str(feed) in opt.feed and pol in opt.pol:
                samplerlist.append(sampler)

    # if this is a FS-as-PS map, we need to check for the presence of a
    # reference scan opt.psmap is only set when --fs-as-ps is set at the
    # command line.  the purpose of this is to try to calibrate a FS map as
    # PS using a reference scan and a list of map scans.
    if opt.psmap:
        if opt.refscan1:
            maptype = 'PS'
        else:
            doMessage(logger,msg.ERR,'ERROR: missing 1st reference scan',\
              'for PS map calibration.')
    # automatically detect the type of this 'normal' FS or PS map by looking at
    # the number of states present in the first map scan
    else:
        maptype = pipeutils.maptype(allscans[0],indexfile,debug=False)

    # in the case of provided map and reference scans, we only have one map
    # which is defined here 
    mymaps = [(opt.refscan1,allscans,opt.refscan2,samplermap,maptype)]

# -------------------------------------------- print map and samplers summary

# the purpose of the following code is only for user feedback and for
# keeping track of processing information in the log files
if not opt.allmaps:
    pipeutils.sampler_summary(logger,samplermap)
    doMessage(logger,msg.INFO,'This map is type:',maptype)
    if maptype == 'PS' and not opt.refscan1:
        doMessage(logger,msg.ERR,'ERROR: missing 1st reference scan.')
        sys.exit(9)

doMessage(logger,msg.INFO,'Processing',len(mymaps),'map(s):')
for idx,mm in enumerate(mymaps):
    doMessage(logger,msg.INFO,'\nMap',idx+1)
    doMessage(logger,msg.INFO,'-----')
    if mm[4] == 'PS':
        doMessage(logger,msg.INFO,'Reference scan.. ',mm[0])
    doMessage(logger,msg.INFO,'map scans....... ',', '.join(map(str,mm[1])))
    if mm[2] and mm[4] == 'PS':
        doMessage(logger,msg.INFO,'Reference scan.. ',mm[2])
    if opt.allmaps:
        pipeutils.sampler_summary(logger,mm[3])

if not opt.allmaps:
    doMessage(logger,msg.INFO,'Processing',len(samplerlist),\
        'sampler(s):', ', '.join(samplerlist))

# ------------------------------------ do calibration and imaging of each map

for scans in mymaps:
    # create a process for each map
    #** a future version of the pipeline might be able to do wittout the
    #** masks paramter if the infiles are already split by sampler.
    #** likewise for samplerlist.
    process_a_single_map(scans,masks,opt,infile,samplerlist,opacity_coeffs)

doMessage(logger,msg.INFO,'Pipeline finished.')
