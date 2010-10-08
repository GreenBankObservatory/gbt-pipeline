#! /usr/bin/env python
import sys
import os
import pyfits
import multiprocessing

import commandline

import pipeutils
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

# force units to all lowercase to make later tests easier
opt.units = opt.units.lower()
ACCEPTABLE_UNITS = [ 'ta', 'ta*', 'tmb', 'tb*' ]
if not (opt.units in ACCEPTABLE_UNITS ):
    print 'ERROR: Not able to calibrate to units of',opt.units
    print '       Please use one of the following:',', '.join(ACCEPTABLE_UNITS)
    sys.exit(9)

if (opt.verbose > 0):
    
    print "---------------"
    print "Command summary"
    print "---------------"
    print "Calibrating to units of.......",opt.units
    if not opt.allmaps:
        print "Map scans.....................",firstScan,'to',lastScan
    print "creating all maps.............",opt.allmaps
    if opt.nodisplay:     print "no idlToSdfits display .......",opt.nodisplay
    if opt.sampler:       print "sampler.......................",opt.sampler
    if opt.spillover:     print "spillover factor (eta_l)......",opt.spillover
    if opt.aperture_eff:  print "aperture efficiency (eta_A)...",opt.aperture_eff
    class prettyfloat(float):
        def __repr__(self):
            return "%0.2g" % self
    pretty_gaincoeffs = map(prettyfloat, gaincoeffs)
    if opt.gaincoeffs:    print "gain coefficiencts............",pretty_gaincoeffs
    if opt.verbose:       print "verbosity level...............",opt.verbose
    print "overwrite existing output.....",opt.clobber
    #if opt.mainbeam_eff:  print "main beam efficiency (eta_B)..",opt.mainbeam_eff
    #if opt.vsourcecenter: print "vSource.......................",opt.vsourcecenter
    #if opt.vsourcewidth:  print "vSourceWidth..................",opt.vsourcewidth
    #if opt.vsourcebegin:  print "vSourceBegin..................",opt.vsourcebegin
    #if opt.vsourceend:    print "vSourceEnd....................",opt.vsourceend

fbeampol=1

if not opt.allmaps:
    # setup scan numbers
    allscans = range(int(firstScan),int(lastScan)+1)
    if (opt.verbose > 0): print "Map scans",allscans

    # convert refscan strings to integers
    refscans = list(set([ int(x) for x in (opt.refscan1, opt.refscan2) ]))
    if refscans[0] < 0:
        print 'No reference scan provided. Exiting.'
        sys.exit(1)
    if refscans[1] < 0: refscans = [refscans[0]]

    if not opt.allscansref: refscans = allscans
    if opt.verbose > 0:
        print "Reference scan(s)",refscans
        print "---------------\n"
    
# read in the input file
if (opt.verbose > 1): print 'opening input sdfits file'
if not os.path.exists(opt.infile):
    print 'ERROR: input sdfits file not readable'
    print '    Please check input sdfits and run again'
    sys.exit(9)

projdir = "/".join(opt.infile.split('/')[:-1])
projfile = opt.infile.split('/')[-1]
projhead = projfile.split('.')[0]
projname = projdir + "/" + projhead

if (opt.verbose > 3): print 'getting mask index',projname+'.raw.acs.index'

indexfile=projname+'.raw.acs.index'
fitsfile=opt.infile
masks = index_it(indexfile,fitsfile)

if (opt.verbose > 3): print 'done'

samplerlist = []
if opt.sampler:
    samplerlist = opt.sampler.split(',')
else:
    for mask in masks:
        samplerlist.append(mask.keys())

# opacities coefficients filename
opacity_coefficients_filename = '/users/rmaddale/Weather/ArchiveCoeffs/CoeffsOpacityFreqList_avrg.txt'
if os.path.exists(opacity_coefficients_filename):
    if opt.verbose > 2: print 'Using coefficients from',opacity_coefficients_filename
    opacity_coeffs = pipeutils.opacity_coefficients(opacity_coefficients_filename)
else:
    if opt.verbose > 1: print 'WARNING: No opacity coefficients file'
    opacity_coeffs = False

aips_input_files = []

if (opt.verbose > 1): print 'getting data object from input file'
if (opt.verbose > 3): print 'opening fits file'
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
    
    mymaps = [(refscan1,allscans,refscan2)]
    
process_ids = []

#import time
#def printfoo(ii):
    #print 'foo',ii
    #rid = np.random.random(1)
    #time.sleep(rid)
    
for idx,scans in enumerate(mymaps):    
    # create a process for each map
    process_ids.append(multiprocessing.Process(target=process_a_single_map,
        args=(scans,masks,opt,infile,samplerlist,gaincoeffs,fbeampol,opacity_coeffs,) ))
    #process_ids.append(multiprocessing.Process(target=printfoo,args=(idx,) ))

#process_ids[0].start()
#process_ids[1].start()
#process_ids[0].join()
#process_ids[1].join()

for idx,pp in enumerate(process_ids):
    pp.start()

for idx,pp in enumerate(process_ids):
    pp.join()
