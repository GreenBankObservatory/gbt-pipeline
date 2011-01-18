#! /usr/bin/env python
import sys
import os
import pyfits
import multiprocessing

import commandline
import pipeutils
from pipeutils import *
from process_a_single_map import *

cl = commandline.CommandLine()
opt = cl.read(sys)

if not opt.allmaps:
    try:
        opt.mapscans = parserange(opt.mapscans)
    except:
        print 'ERROR: could not parse range:',opt.mapscans
        sys.exit(10)

beginscan = False
endscan = False
if opt.mapscans:
    beginscan = opt.mapscans[0]
    endscan = opt.mapscans[-1]

opt.infile = check_for_sdfits_file(opt.infile, opt.sdfitsdir, beginscan,\
                               endscan,opt.refscan1, opt.refscan2,\
                               opt.verbose)

# -------------------------------------------------------- configure logging
logger = pipeutils.configure_logfile(opt,'pipeline'+'_'+timestamp()+'.log')

# ------------------------------------------------- identify imaging script

# look in integration and release contrib directories for
# if no script is found, turn imaging off
RELCONDIR = '/home/gbtpipeline/release/contrib'
TESTCONDIR = '/home/gbtpipeline/integration/contrib'
IMSCRIPT = '/' + 'imageDefault.py'

if not opt.imagingoff:
    if TESTCONDIR in sys.path and os.path.isfile(TESTCONDIR + IMSCRIPT):
        opt.imageScript = TESTCONDIR + IMSCRIPT
    elif os.path.isfile(RELCONDIR + IMSCRIPT):
        opt.imageScript = RELCONDIR + IMSCRIPT
    else:
        doMessage(logger,msg.ERR,"ERROR: imaging script not found.")
        opt.imagingoff = True

# -------------------  force units to all lowercase to make later tests easier
opt.units = opt.units.lower()
ACCEPTABLE_UNITS = [ 'ta', 'ta*', 'tmb', 'tb*', 'jy' ]
if not (opt.units in ACCEPTABLE_UNITS ):
    doMessage(logger,msg.ERR,'ERROR: Not able to calibrate to units of',opt.units)
    doMessage(logger,msg.ERR,'       Please use one of the following:',', '.join(ACCEPTABLE_UNITS))
    sys.exit(9)

commandSummary(logger,opt)

fbeampol=1

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

    if not any(refscans):
        doMessage(logger,msg.ERR,'No reference scan provided. Exiting.')
        sys.exit(1)

    doMessage(logger,msg.INFO,"Reference scan(s)",', '.join(map(str,list(refscans))))
    doMessage(logger,msg.INFO,"---------------\n")
    
# read in the input file
doMessage(logger,msg.DBG,'opening input sdfits file')
if not os.path.exists(opt.infile):
    doMessage(logger,msg.ERR,'ERROR: input sdfits file not readable')
    doMessage(logger,msg.ERR,'    Please check input sdfits and run again')
    sys.exit(9)

# name index file
projdir = "/".join(opt.infile.split('/')[:-1])
projfile = opt.infile.split('/')[-1]
projhead = projfile.split('.')[0]
projname = projdir + "/" + projhead
indexfile=projname+'.raw.acs.index'

doMessage(logger,msg.DBG,'getting mask index',projname+'.raw.acs.index')
masks = index_it(indexfile,opt.infile)
doMessage(logger,msg.DBG,'done')

# opacities coefficients filename
opacity_coefficients_filename = '/users/rmaddale/Weather/ArchiveCoeffs/CoeffsOpacityFreqList_avrg.txt'
if os.path.exists(opacity_coefficients_filename):
    doMessage(logger,msg.DBG,'Using coefficients from',opacity_coefficients_filename)
    opacity_coeffs = pipeutils.opacity_coefficients(opacity_coefficients_filename)
else:
    doMessage(logger,msg.WARN,'WARNING: No opacity coefficients file')
    opacity_coeffs = False

aips_input_files = []

doMessage(logger,msg.DBG,'getting data object from input file')
doMessage(logger,msg.DBG,'opening fits file')
infile = pyfits.open(opt.infile,memmap=1)

# we need to set allscans, refscan1 and refscan2 for each map
#    and continue
maps_and_samplers = list_samplers(opt.allmaps,indexfile)

samplerlist = []
if opt.allmaps:

    # we need to set allscans, refscan1 and refscan2 for each map
    #    and continue
    mymaps = maps_and_samplers
    for mask in masks:
        samplerlist.append(mask.keys())

else:
    samplermap = maps_and_samplers[allscans[0]][1]

    if not opt.feed and not opt.pol:
        samplerlist = samplermap.keys()

    else:
        # check the feed and pol specified at the commandline
        #  before including a sampler in the list
        if opt.feed:
            try:
                inclusive = is_inclusive_range(opt.feed)
            except:
                doMessage(logger,msg.INFO,'ERROR: can not parse range',opt.feed)
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
                doMessage(logger,msg.ERR,'ERROR: could not parse range',opt.feed)
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

    mymaps = [(opt.refscan1,allscans,opt.refscan2,samplermap)]

if not opt.allmaps:
    sampler_summary(logger,samplermap)

doMessage(logger,msg.INFO,'Processing',len(mymaps),'map(s):')
for idx,mm in enumerate(mymaps):
    doMessage(logger,msg.INFO,'Map',idx+1)
    doMessage(logger,msg.INFO,'-----')
    doMessage(logger,msg.INFO,'Reference scan.. ',mm[0])
    doMessage(logger,msg.INFO,'map scans....... ',', '.join(map(str,mm[1])))
    if mm[2]:
        doMessage(logger,msg.INFO,'Reference scan.. ',mm[2])
    if opt.allmaps:
        sampler_summary(logger,mm[3])

if not opt.allmaps:
    doMessage(logger,msg.INFO,'Processing',len(samplerlist),'sampler(s):', ', '.join(samplerlist))

for idx,scans in enumerate(mymaps):
    # create a process for each map
    process_a_single_map(scans,masks,opt,infile,samplerlist,fbeampol,opacity_coeffs)

doMessage(logger,msg.INFO,'Pipeline finished.')
