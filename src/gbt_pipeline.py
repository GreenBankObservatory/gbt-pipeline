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

opt.infile = check_for_sdfits_file(opt.infile, opt.sdfitsdir, opt.beginscan,\
                               opt.endscan,opt.refscan1, opt.refscan2,\
                               opt.verbose)

firstScan = opt.beginscan
lastScan  = opt.endscan

if opt.gaincoeffs:
    gaincoeffs = opt.gaincoeffs.split(',')
    gaincoeffs = [ float(xx) for xx in gaincoeffs ]


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

doMessage(logger,msg.INFO,"---------------")
doMessage(logger,msg.INFO,"Command summary")
doMessage(logger,msg.INFO,"---------------")
doMessage(logger,msg.INFO,"Input file....................",opt.infile)
doMessage(logger,msg.INFO,"Calibrating to units of.......",opt.units)
if not opt.allmaps:
    doMessage(logger,msg.INFO,"Map scans.....................",firstScan,'to',lastScan)
doMessage(logger,msg.INFO,"creating all maps.............",opt.allmaps)
doMessage(logger,msg.INFO,"disable idlToSdfits display ..",opt.nodisplay)
doMessage(logger,msg.INFO,"spillover factor (eta_l)......",str(opt.spillover))
doMessage(logger,msg.INFO,"aperture efficiency (eta_A)...",str(opt.aperture_eff))
class prettyfloat(float):
    def __repr__(self):
        return "%0.2g" % self
pretty_gaincoeffs = map(prettyfloat, gaincoeffs)
doMessage(logger,msg.INFO,"gain coefficiencts............",str(pretty_gaincoeffs))
doMessage(logger,msg.INFO,"disable mapping ..............",opt.imagingoff)
doMessage(logger,msg.INFO,"map scans for scale ..........",opt.mapscansforscale)
if opt.sampler:
    doMessage(logger,msg.INFO,"sampler(s)....................",opt.sampler)
if opt.feed:
    doMessage(logger,msg.INFO,"feed(s) ......................",opt.feed)
if opt.pol:
    doMessage(logger,msg.INFO,"polarization .................",opt.pol)
doMessage(logger,msg.INFO,"map scans for scale ..........",opt.mapscansforscale)
doMessage(logger,msg.INFO,"verbosity level...............",str(opt.verbose))

doMessage(logger,msg.INFO,"overwrite existing output.....",str(opt.clobber))

fbeampol=1

if not opt.allmaps:
    # setup scan numbers
    allscans = range(int(firstScan),int(lastScan)+1)
    doMessage(logger,msg.INFO,"Map scans",allscans)

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

    doMessage(logger,msg.INFO,"Reference scan(s)",list(refscans))
    doMessage(logger,msg.INFO,"---------------\n")
    
# read in the input file
doMessage(logger,msg.DBG,'opening input sdfits file')
if not os.path.exists(opt.infile):
    doMessage(logger,msg.ERR,'ERROR: input sdfits file not readable')
    doMessage(logger,msg.ERR,'    Please check input sdfits and run again')
    sys.exit(9)

projdir = "/".join(opt.infile.split('/')[:-1])
projfile = opt.infile.split('/')[-1]
projhead = projfile.split('.')[0]
projname = projdir + "/" + projhead

doMessage(logger,msg.DBG,'getting mask index',projname+'.raw.acs.index')

indexfile=projname+'.raw.acs.index'
fitsfile=opt.infile
masks = index_it(indexfile,fitsfile)

doMessage(logger,msg.DBG,'done')

samplerlist = []
if opt.sampler:
    samplerlist = opt.sampler.split(',')
else:
    for mask in masks:
        samplerlist.append(mask.keys())

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

# if we are attempting to calibrate/image all maps in the input file
# we need to call summarize_it to get the maps and fire off a pipe for each one
#    probably using multiprocess

# get number of cpus in system
cpucount = multiprocessing.cpu_count()

# we need to set allscans, refscan1 and refscan2 for each map
#    and continue
maps_and_samplers = list_samplers(indexfile)

if opt.allmaps:

    # we need to set allscans, refscan1 and refscan2 for each map
    #    and continue
    mymaps = maps_and_samplers

elif not opt.sampler:
    
    samplerlist = []
    
    for mapblock in maps_and_samplers:

        if opt.refscan1 == mapblock[0]:

            samplermap = mapblock[3]

            if not opt.feed and not opt.pol:
                samplerlist = samplermap.keys()

            else:
                # check the feed and pol specified at the commandline
                #  before including a sampler in the list
                if opt.feed and not opt.pol:
                    opt.pol = ('LL','RR')
                elif opt.pol and not opt.feed:
                    opt.feed = range(1,8)

                for sampler in samplermap:
                    feed = samplermap[sampler][0]
                    pol = samplermap[sampler][1]
                    if str(feed) in opt.feed and pol in opt.pol:
                        samplerlist.append(sampler)

            mymaps = [(opt.refscan1,allscans,opt.refscan2)]
            break

if not opt.allmaps:
    sampler_summary(logger,samplermap)

doMessage(logger,msg.INFO,'Processing',len(mymaps),'map(s):')
for idx,mm in enumerate(mymaps):
    doMessage(logger,msg.INFO,'Map',idx+1)
    doMessage(logger,msg.INFO,'-----')
    doMessage(logger,msg.INFO,'Reference scan.. ',mm[0])
    doMessage(logger,msg.INFO,'map scans....... ',mm[1])
    if mm[2]:
        doMessage(logger,msg.INFO,'Reference scan.. ',mm[2])
    if opt.allmaps:
        sampler_summary(logger,mm[3])

if not opt.allmaps:
    doMessage(logger,msg.INFO,'Processing',len(samplerlist),'sampler(s):', samplerlist)

process_ids = []
lock = multiprocessing.Lock()
for idx,scans in enumerate(mymaps):    
    # create a process for each map
    process_ids.append(multiprocessing.Process(target=process_a_single_map,
        args=(scans,masks,opt,infile,samplerlist,gaincoeffs,fbeampol,opacity_coeffs,lock,) ))

for idx,pp in enumerate(process_ids):
    pp.start()

for idx,pp in enumerate(process_ids):
    pp.join()

doMessage(logger,msg.INFO,'Pipeline finished.')
