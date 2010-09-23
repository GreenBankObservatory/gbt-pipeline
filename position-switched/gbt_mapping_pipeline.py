#! /usr/bin/env python
USE_MAP_SCAN_FOR_SCALE=True

import sys
import os
import pyfits
import numpy as np

import commandline
import scanreader
import smoothing
import pipeutils
from check_for_sdfits_file import *
from index_it import *

cl = commandline.CommandLine()
(opt, args) = cl.read(sys)

opt.verbose = int(opt.verbose)

infile = check_for_sdfits_file(opt.infile, opt.sdfitsdir, opt.beginscan,\
                               opt.endscan,opt.refscan1, opt.refscan2,\
                               opt.verbose)

firstScan = opt.beginscan
lastScan  = opt.endscan

if (opt.verbose > 0):
    print "Calibrating to units of",opt.units
    print "Map scans",firstScan,'to',lastScan
    if opt.vsourcecenter: print "vSource",opt.vsourcecenter
    if opt.vsourcewidth: print "vSourceWidth",opt.vsourcewidth
    if opt.vsourcebegin: print "vSourceBegin",opt.vsourcebegin
    if opt.vsourceend: print "vSourceEnd",opt.vsourceend
    if opt.sampler: print "sampler",opt.sampler

# setup scan numbers
allscans = range(int(firstScan),int(lastScan)+1)
if (opt.verbose > 0): print "All map scans",allscans

# convert refscan strings to integers
refscans = list(set([ int(x) for x in (opt.refscan1, opt.refscan2) ]))
if refscans[0] < 0:
    print 'No reference scan provided. Exiting.'
    sys.exit(1)
if refscans[1] < 0: refscans = [refscans[0]]

if not opt.allscansref: refscans = allscans
if opt.verbose > 0: print "Reference scan(s)",refscans

# read in the input file
if (opt.verbose > 0): print 'opening input sdfits file'
if not os.path.exists(opt.infile):
    print 'ERROR: input sdfits file not readable'
    print '    Please check input sdfits and run again'
    sys.exit(9)

projname = opt.infile.split('.')[0]

if (opt.verbose > 3): print 'getting mask index',projname+'.raw.acs.index'
masks = index_it(indexfile=projname+'.raw.acs.index',fitsfile=opt.infile)
if (opt.verbose > 3): print 'done'

if opt.sampler:
    samplerlist = opt.sampler.split(',')
else:
    samplerlist = masks.keys()
    
# opacities coefficients filename
opacity_coefficients_filename = '/users/rmaddale/Weather/ArchiveCoeffs/CoeffsOpacityFreqList_avrg.txt'
if os.path.exists(opacity_coefficients_filename):
    if opt.verbose > 0: print 'Using coefficients from',opacity_coefficients_filename
    opacity_coeffs = pipeutils.opacity_coefficients(opacity_coefficients_filename)
else:
    if opt.verbose > 0: print 'WARNING: No opacity coefficients file'
    opacity_coeffs = False

aips_input_files = []

for sampler in samplerlist:

    samplermask = masks.pop(sampler)

    if (opt.verbose > 1): print 'getting data object from input file'
    if (opt.verbose > 3): print 'opening fits file'
    infile = pyfits.open(opt.infile,memmap=1)
    if (opt.verbose > 3): print 'done'
    if (opt.verbose > 3): print 'appying mask'
    sdfitsdata = infile[1].data[samplermask]
    if (opt.verbose > 3): print 'done'

    if opt.verbose > 0:
        print '-----------'
        print 'SAMPLER',sampler
        print '-----------'

    freq=0
    refspec = []
    refdate = []
    ref_tsky = []
    ref_tsys = []
    
    # ------------------------------------------- name output file
    scan=allscans[0]
    mapscan = scanreader.ScanReader()
    obj,centerfreq,feed = mapscan.map_name_vals(sdfitsdata,opt.verbose)
    outfilename = 'Cal_' + obj + '_' + str(feed) + '_' + \
                    str(allscans[0]) + '_' + str(allscans[-1]) + '_' + \
                    str(centerfreq)[:6] + '_' + sampler + '.fits'
    if opt.verbose > 0: print 'outfile name',outfilename
    if os.path.exists(outfilename):
        print 'Outfile exits:',outfilename
        print 'Please remove or rename outfile and try again'
        sys.exit(1)

    # ------------------------------------------- get the first reference scan
    scan=refscans[0]
    if opt.verbose > 0: print 'Processing reference scan:',scan
    
    ref1 = scanreader.ScanReader()

    ref1.get_scan(scan,sdfitsdata,opt.verbose)
    
    ref1spec,ref1_max_tcal,ref1_mean_date,freq,tskys_ref1,ref1_tsys = \
    ref1.average_reference(opt.units,opacity_coeffs,opt.verbose)
    
    refdate.append(ref1_mean_date)
    ref_tsky.append(tskys_ref1)
    
    # determine scale factor used to compute Tsys of each integration
    k_per_count = ref1_max_tcal / ref1.calonoff_diff() # dcSCal in scaleIntsRef
    onave1 = ref1.calon_ave()
    offave1 = ref1.caloff_ave()
    dcRef1 = (ref1.calon_ave()+ref1.caloff_ave())/2.
    refspec.append(dcRef1)
    dcCal = (ref1.calon_ave()-ref1.caloff_ave())
    chanlo = int(len(ref1spec)*.1)
    chanhi = int(len(ref1spec)*.9)
    ratios = dcRef1[chanlo:chanhi] / dcCal[chanlo:chanhi]
    tsysRef1 = ratios.mean()*ref1_max_tcal
    ref_tsys.append(tsysRef1)
    if opt.verbose > 3:
        print 'REF 1'
        print 'dcCal (avg. calON-calOFF):',ref1.calonoff_diff().mean()
        print 'avg. K/count from ref1:',k_per_count.mean()
        print 'ON AVE [0][1000][nChan]',onave1[0],onave1[1000],onave1[-1]
        print 'OFF AVE [0][1000][nChan]',offave1[0],offave1[1000],offave1[-1]
        print 'dcRef1',dcRef1[0],dcRef1[1000],dcRef1[-1]
        print 'ref1 Tsys:',tsysRef1
    
    # ------------------------------------------- gather all map CALON-CALOFFS to scale
    # -------------------------------------------  reference scan counts to kelvin
    if USE_MAP_SCAN_FOR_SCALE:
        calonAVEs=[]
        caloffAVEs=[]
        maxTCAL=0
        
        for scan in allscans:
            print 'Processing map scan:',scan
            mapscan = scanreader.ScanReader()
            mapscan.get_scan(scan,sdfitsdata,opt.verbose)

            if len(calonAVEs):
                calonAVEs = np.ma.vstack((calonAVEs,mapscan.calon_ave()))
                caloffAVEs = np.ma.vstack((caloffAVEs,mapscan.caloff_ave()))
            else:
                calonAVEs = mapscan.calon_ave()
                caloffAVEs = mapscan.caloff_ave()

            thisTCAL = mapscan.max_tcal()
            if thisTCAL > maxTCAL:
                maxTCAL = thisTCAL

        sig_calONave = calonAVEs.mean(0)
        sig_calOFFave = caloffAVEs.mean(0)
        
        sig_calONOFFdiff = sig_calONave - sig_calOFFave

        if opt.verbose > 3:
            print 'sig calON mean',sig_calONave.mean()
            print 'sig calOFF mean',sig_calOFFave.mean()
            print 'sig calON-OFF mean',sig_calONOFFdiff.mean()
        
        map_scans_cal_smoothed = smoothing.smooth_spectrum(sig_calONOFFdiff,freq)

        # ---------------------------------------- set scaling factor, kelvins per count
        k_per_count = maxTCAL / sig_calONOFFdiff
    
    if opt.verbose > 3:
        print "K/count (mean)",k_per_count.mean()
    
    # ------------------------------------------- get the last reference scan
    if len(refscans)>1:
        scan=refscans[-1]
        if opt.verbose > 0:  print 'Processing reference scan:',scan
        
        ref2 = scanreader.ScanReader()
        ref2.get_scan(scan,sdfitsdata,opt.verbose)
        
        ref2spec,ref2_max_tcal,ref2_mean_date,freq,tskys_ref2,ref2_tsys = \
            ref2.average_reference(opt.units,opacity_coeffs,opt.verbose)
        refdate.append(ref2_mean_date)
        ref_tsky.append(tskys_ref2)

        dcRef2 = (ref2.calon_ave()+ref2.caloff_ave())/2.
        onave2 = ref2.calon_ave()
        offave2 = ref2.caloff_ave()
        
        refspec.append(dcRef2)
        dcCal = (ref2.calon_ave()-ref2.caloff_ave())
        chanlo = int(len(ref2spec)*.1)
        chanhi = int(len(ref2spec)*.9)
        ratios = dcRef2[chanlo:chanhi] / dcCal[chanlo:chanhi]
        tsysRef2 = ratios.mean()*ref2_max_tcal
        ref_tsys.append(tsysRef2)
        
        if opt.verbose > 3:
            print 'REF 2'
            print 'ON AVE [0][1000][nChan]',onave2[0],onave2[1000],onave2[-1]
            print 'OFF AVE [0][1000][nChan]',offave2[0],offave2[1000],offave2[-1]
            print 'dcRef2',dcRef2[0],dcRef2[1000],dcRef2[-1]
            print 'ref2 Tsys:',tsysRef2

    # --------------------------  calibrate all integrations to Tb
    # ----------------------------  if not possible, calibrate to Ta

    calibrated_integrations = []
    nchans = False # number of channels, used to filter of 2% from either edge
    
    for scan in allscans:
        print 'Calibrating scan:',scan

        mapscan = scanreader.ScanReader()
        mapscan.get_scan(scan,sdfitsdata,opt.verbose)
        nchans = len(mapscan.data[0])

        mapscan.mean_date()
        cal_ints = mapscan.calibrate_to(refspec,refdate,ref_tsys,\
            k_per_count,opacity_coeffs,ref_tsky,opt.units,
            opt.verbose)
        
        if len(calibrated_integrations):
            calibrated_integrations = np.concatenate((calibrated_integrations,cal_ints))
        else: # first scan
            calibrated_integrations = cal_ints

    # ---------------------------------- write out calibrated fits file
    primary = pyfits.PrimaryHDU()
    primary.header = infile[0].header

    sdfits = pyfits.new_table(infile[1].columns,nrows=len(calibrated_integrations),fill=1)
    for idx,ee in enumerate(calibrated_integrations):
        sdfits.data[idx] = ee

    sdfits.name = 'SINGLE DISH'

    hdulist = pyfits.HDUList([primary,sdfits])
    hdulist.writeto(outfilename,clobber=True)
    
    # set the idlToSdfits output file name
    aipsinname = os.path.splitext(outfilename)[0]+'.sdf'
    
    # run idlToSdfits, which converts calibrated sdfits into a format
    options = ''
    
    if bool(opt.average):
        options = options + ' -a ' + str(opt.average)

    if nchans:
        chan_min = int(nchans*.02) # start at 2% of nchan
        chan_max = int(nchans*.98) # end at 98% of nchans
        options = options + ' -c ' + str(chan_min) + ':' + str(chan_max) + ' '
    
    if opt.nodisplay:
        options = options + ' -l '
        
    idlcmd = 'idlToSdfits -o ' + aipsinname + options + outfilename
    if opt.verbose > 0: print idlcmd
    
    os.system(idlcmd)
    
    infile.close()
    del sdfitsdata
