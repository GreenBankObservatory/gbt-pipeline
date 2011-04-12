#! /usr/bin/env python
import sys
import os
import pyfits
import multiprocessing
import glob

import commandline
import pipeutils
from pipeutils import *
from process_a_single_map import *

# -----------------------------------  interpret the command linen parameters

cl = commandline.CommandLine()
opt = cl.read(sys)

# if not using automatic map detection
#   try to interpret the range of scans provided by the user
if not opt.allmaps:
    try:
        opt.mapscans = parserange(opt.mapscans)
    except:
        print 'ERROR: could not parse range:',opt.mapscans
        sys.exit(10)

# numerically sort the map scans
opt.mapscans = [ int(xx) for xx in opt.mapscans ]
opt.mapscans.sort()
opt.mapscans = [ str(xx) for xx in opt.mapscans ]

# define begin and end map scans if range set by user
beginscan = False
endscan = False
if opt.mapscans:
    beginscan = opt.mapscans[0]
    endscan = opt.mapscans[-1]

# -----------------------------------------------  look for an input file

#   if it doesn't exist try to recreate it from a user supplied directory
opt.infile = check_for_sdfits_file(opt.infile, opt.sdfitsdir, beginscan,\
                               endscan,opt.refscan1, opt.refscan2,\
                               opt.verbose)

# -------------------------------------------------------- configure logging

logger = pipeutils.configure_logfile(opt,'pipeline'+'_'+timestamp()+'.log')

# ------------------------------------------------- identify imaging script

# look in integration and release contrib directories for imaging script
# if no script is found, turn imaging off

RELCONDIR = '/home/gbtpipeline/release/contrib'
TESTCONDIR = '/home/gbtpipeline/integration/contrib'
DBCONSCRIPT = '/' + 'dbcon.py'
MAPSCRIPT = '/' + 'mapDefault.py'
if not opt.imagingoff:

    # test version of pipeline
    if TESTCONDIR in sys.path and \
      os.path.isfile(TESTCONDIR + DBCONSCRIPT) and \
      os.path.isfile(TESTCONDIR + MAPSCRIPT):

        opt.dbconScript = TESTCONDIR + DBCONSCRIPT
        opt.mapScript = TESTCONDIR + MAPSCRIPT

    # release version of pipeline
    elif os.path.isfile(RELCONDIR + DBCONSCRIPT) and \
      os.path.isfile(RELCONDIR + MAPSCRIPT):

        opt.dbconScript = RELCONDIR + DBCONSCRIPT
        opt.mapScript = RELCONDIR + MAPSCRIPT

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
    
# -------------------------------------------------  read in the input file

doMessage(logger,msg.DBG,'opening input sdfits file')
if not os.path.exists(opt.infile):
    doMessage(logger,msg.ERR,'ERROR: input sdfits file not readable')
    doMessage(logger,msg.ERR,'    Please check input sdfits and run again')
    sys.exit(9)

# -------------------------------------------------  name index file

projdir = "/".join(opt.infile.split('/')[:-1])
projfile = opt.infile.split('/')[-1]
projhead = projfile.split('.')[0]
projname = projdir + "/" + projhead
indexfile=projname+'.raw.acs.index'

# ------------------------------------------- get sampler mask using index file

doMessage(logger,msg.DBG,'getting mask index',projname+'.raw.acs.index')
masks = get_masks(indexfile,opt.infile)
doMessage(logger,msg.DBG,'done')

# ----------------------------------------------- look for opacity coefficients

start_mjd = get_start_mjd(indexfile)
opacity_coefficients_filename = False
opacity_files = glob.glob('/users/rmaddale/Weather/ArchiveCoeffs/CoeffsOpacityFreqList_avrg_*.txt')

for opacity_candidate_file in opacity_files:
    dates = opacity_candidate_file.split('_')[-2:]
    mydate = []
    for date in dates:
        mydate.append(int(date.split('.')[0]))

    if start_mjd >= mydate[0] and start_mjd < mydate[1]:
        opacity_coefficients_filename = opacity_candidate_file
        break

if not opacity_coefficients_filename:
    opacity_coefficients_filename = \
        '/users/rmaddale/Weather/ArchiveCoeffs/CoeffsOpacityFreqList_avrg.txt'

# opacities coefficients filename
if os.path.exists(opacity_coefficients_filename):
    doMessage(logger,msg.DBG,'Using coefficients from',\
              opacity_coefficients_filename)
    opacity_coeffs = \
        pipeutils.opacity_coefficients(opacity_coefficients_filename)
else:
    doMessage(logger,msg.WARN,'WARNING: No opacity coefficients file')
    opacity_coeffs = False

aips_input_files = []

# ---------------------------------------------------------- open data file

doMessage(logger,msg.DBG,'getting data object from input file')
doMessage(logger,msg.DBG,'opening fits file')
infile = pyfits.open(opt.infile,memmap=1,mode='readonly')


# --------------------------------------------------- automatically find maps

# also get a list of samplers used for each map

# we need to set allscans, refscan1 and refscan2 for each map
#    and continue
maps_and_samplers = get_maps_and_samplers(opt.allmaps,indexfile)

samplerlist = []
if opt.allmaps:

    # we need to set allscans, refscan1 and refscan2 for each map
    #    and continue
    mymaps = maps_and_samplers
    for mask in masks:
        samplerlist.append(mask.keys())

else:
    try:
        samplermap = maps_and_samplers[allscans[0]][1]
    except(KeyError):
        doMessage(logger,msg.ERR,'ERROR: scan',str(allscans[0]),'not in infile')
        sys.exit(8)

    if not opt.feed and not opt.pol:
        samplerlist = samplermap.keys()

    # filter on feed and polarization if defined by user
    else:
        # check the feed and pol specified at the commandline
        #  before including a sampler in the list
        if opt.feed:
            try:
                inclusive = is_inclusive_range(opt.feed)
            except:
                doMessage(logger,msg.INFO,'ERROR: can not parse range',\
                          opt.feed)
                sys.exit(11)
            # if there are only exclusive items listed
            #   add all feeds to the list so we have something to
            #   subtract from
            if not inclusive:
                feeds = []
                for sampler in samplermap:
                    feeds.append(str(samplermap[sampler][0]))
                feeds = ',' + ','.join(feeds)
                opt.feed += feeds
            try:
                opt.feed = parserange(opt.feed)
            except:
                doMessage(logger,msg.ERR,'ERROR: could not parse range',\
                          opt.feed)
                sys.exit(11)

        if opt.feed and not opt.pol:
            for sampler in samplermap:
                opt.pol.append(str(samplermap[sampler][1]))
        elif opt.pol and not opt.feed:
            for sampler in samplermap:
                opt.feed.append(str(samplermap[sampler][0]))

        # add only the samplers we will process
        for sampler in samplermap:
            feed = samplermap[sampler][0]
            pol = samplermap[sampler][1]
            if str(feed) in opt.feed and pol in opt.pol:
                samplerlist.append(sampler)

    if opt.psmap:
        if opt.refscan1:
            maptype = 'PS'
        else:
            doMessage(logger,msg.ERR,'ERROR: PS map but missing 1st reference scan.')
    else:
        maptype = maptype(allscans[0],indexfile,debug=False)

    mymaps = [(opt.refscan1,allscans,opt.refscan2,samplermap,maptype)]

# -------------------------------------------- print map and samplers summary

if not opt.allmaps:
    sampler_summary(logger,samplermap)
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
        sampler_summary(logger,mm[3])

if not opt.allmaps:
    doMessage(logger,msg.INFO,'Processing',len(samplerlist),\
        'sampler(s):', ', '.join(samplerlist))

# ------------------------------------ do calibration and imaging of each map

for idx,scans in enumerate(mymaps):
    # create a process for each map
    process_a_single_map(scans,masks,opt,infile,samplerlist,\
                         opacity_coeffs)

doMessage(logger,msg.INFO,'Pipeline finished.')
