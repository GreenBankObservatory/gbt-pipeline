#! /usr/bin/env python
import sys
import os
import pyfits
import multiprocessing

import commandline

import pipeutils
from pipeutils import *
from check_for_sdfits_file import *
from index_it import *
from process_a_single_map import *
from summarize_it import *

cl = commandline.CommandLine()
(opt, args) = cl.read(sys)

opt.verbose = int(opt.verbose)

infile = check_for_sdfits_file(opt.infile, opt.sdfitsdir, opt.beginscan,\
                               opt.endscan,opt.refscan1, opt.refscan2,\
                               opt.verbose)

firstScan = opt.beginscan
lastScan  = opt.endscan

if opt.gaincoeffs:
    gaincoeffs = opt.gaincoeffs.split(',')
    gaincoeffs = [ float(xx) for xx in gaincoeffs ]


# -------------------------------------------------------- configure logging
logger = pipeutils.configure_logfile(opt,'pipeline.log')

# force units to all lowercase to make later tests easier
opt.units = opt.units.lower()
ACCEPTABLE_UNITS = [ 'ta', 'ta*', 'tmb', 'tb*' ]
if not (opt.units in ACCEPTABLE_UNITS ):
    doMessage(logger,msg.ERR,'ERROR: Not able to calibrate to units of',opt.units)
    doMessage(logger,msg.ERR,'       Please use one of the following:',', '.join(ACCEPTABLE_UNITS))
    sys.exit(9)

doMessage(logger,msg.INFO,"---------------")
doMessage(logger,msg.INFO,"Command summary")
doMessage(logger,msg.INFO,"---------------")
doMessage(logger,msg.INFO,"Calibrating to units of.......",opt.units)
if not opt.allmaps:
    doMessage(logger,msg.INFO,"Map scans.....................",firstScan,'to',lastScan)
doMessage(logger,msg.INFO,"creating all maps.............",opt.allmaps)
if opt.nodisplay:     doMessage(logger,msg.INFO,"no idlToSdfits display .......",opt.nodisplay)
if opt.sampler:       doMessage(logger,msg.INFO,"sampler.......................",opt.sampler)
if opt.spillover:     doMessage(logger,msg.INFO,"spillover factor (eta_l)......",str(opt.spillover))
if opt.aperture_eff:  doMessage(logger,msg.INFO,"aperture efficiency (eta_A)...",str(opt.aperture_eff))
class prettyfloat(float):
    def __repr__(self):
        return "%0.2g" % self
pretty_gaincoeffs = map(prettyfloat, gaincoeffs)
if opt.gaincoeffs:    doMessage(logger,msg.INFO,"gain coefficiencts............",str(pretty_gaincoeffs))
if opt.verbose:       doMessage(logger,msg.INFO,"verbosity level...............",str(opt.verbose))
print 'verbosity level',opt.verbose
doMessage(logger,msg.INFO,"overwrite existing output.....",str(opt.clobber))
#if opt.mainbeam_eff:  doMessage(logger,msg.INFO,"main beam efficiency (eta_B)..",opt.mainbeam_eff)
#if opt.vsourcecenter: doMessage(logger,msg.INFO,"vSource.......................",opt.vsourcecenter)
#if opt.vsourcewidth:  doMessage(logger,msg.INFO,"vSourceWidth..................",opt.vsourcewidth)
#if opt.vsourcebegin:  doMessage(logger,msg.INFO,"vSourceBegin..................",opt.vsourcebegin)
#if opt.vsourceend:    doMessage(logger,msg.INFO,"vSourceEnd....................",opt.vsourceend)

fbeampol=1

if not opt.allmaps:
    # setup scan numbers
    allscans = range(int(firstScan),int(lastScan)+1)
    doMessage(logger,msg.INFO,"Map scans",allscans)

    # convert refscan strings to integers
    refscans = list(set([ int(x) for x in (opt.refscan1, opt.refscan2) ]))
    if refscans[0] < 0:
        doMessage(logger,msg.ERR,'No reference scan provided. Exiting.')
        sys.exit(1)
    if refscans[1] < 0: refscans = [refscans[0]]

    if not opt.allscansref: refscans = allscans
    doMessage(logger,msg.INFO,"Reference scan(s)",refscans)
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

if opt.allmaps:

    # we need to set allscans, refscan1 and refscan2 for each map
    #    and continue
    mymaps = summarize_it(indexfile)

else:
    
    mymaps = [(opt.refscan1,allscans,opt.refscan2)]
    
process_ids = []

for idx,scans in enumerate(mymaps):    
    # create a process for each map
    process_ids.append(multiprocessing.Process(target=process_a_single_map,
        args=(scans,masks,opt,infile,samplerlist,gaincoeffs,fbeampol,opacity_coeffs,) ))

for idx,pp in enumerate(process_ids):
    pp.start()

for idx,pp in enumerate(process_ids):
    pp.join()
