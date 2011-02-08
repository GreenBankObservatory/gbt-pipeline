import os
import sys
import getpass
import multiprocessing
#import pylab

import numpy as np
import pyfits

import scanreader
import smoothing
import pipeutils
from pipeutils import *

def do_sampler_fs(cc,sampler,logger,block_found,blockid,samplermap,allscans,\
                  refscans,scans,masks,opt,infile,fbeampol,opacity_coeffs):
    print 'IN do_sampler_fs',sampler
    doMessage(logger,msg.DBG,'-----------')
    doMessage(logger,msg.DBG,'SAMPLER',sampler)
    doMessage(logger,msg.DBG,'-----------')

    try:
        samplermask = masks[blockid-1].pop(sampler)
    except(TypeError):
        doMessage(logger,msg.ERR,'ERROR: TypeError when defining samplermask')
        doMessage(logger,msg.DBG,'sampler',sampler)
        doMessage(logger,msg.DBG,'blockid',blockid)
        doMessage(logger,msg.DBG,'len(samplerlist)',len(samplerlist))
        doMessage(logger,msg.DBG,'len(masks)',len(masks))
        doMessage(logger,msg.DBG,'len(masks[0])',len(masks[0]))
        doMessage(logger,msg.DBG,'type(masks)',type(masks))
        doMessage(logger,msg.DBG,'type(masks[0])',type(masks[0]))
        sys.exit(9)
    except(KeyError):
        doMessage(logger,msg.ERR,'ERROR: KeyError when defining samplermask')
        doMessage(logger,msg.DBG,'type(sampler)',type(sampler))
        doMessage(logger,msg.DBG,'sampler',sampler)
        doMessage(logger,msg.DBG,'type(samplers)',type(thismap_samplerlist))
        doMessage(logger,msg.DBG,'samplers',thismap_samplerlist)
        sys.exit(9)

    doMessage(logger,msg.DBG,'appying mask')
    if block_found:
        doMessage(logger,msg.DBG,'to extension',blockid)
        sdfitsdata = infile[blockid].data[samplermask]
        doMessage(logger,msg.DBG,'length of sampler-filtered data block is',len(sdfitsdata))
        del samplermask
    doMessage(logger,msg.DBG,'done')

    freq=0
    refspec = []
    refdate = []
    ref_tsky = []
    ref_tsys = []

    # ------------------------------------------- name output file
    scan=allscans[0]
    mapscan = scanreader.ScanReader()
    mapscan.setLogger(logger)

    obj,centerfreq,feed = mapscan.map_name_vals(scan,sdfitsdata,opt.verbose)
    outfilename = obj + '_' + str(feed) + '_' + \
                str(allscans[0]) + '_' + str(allscans[-1]) + '_' + \
                str(centerfreq)[:6] + '_' + sampler + '.fits'
    import warnings
    def send_warnings_to_logger(message, category, filename, lineno, file=None, line=None):
        doMessage(logger,msg.WARN,message)
    warnings.showwarning = send_warnings_to_logger
    warnings.filterwarnings('once', '.*converting a masked element to nan.*',)

    doMessage(logger,msg.DBG,'outfile name',outfilename)
    if (False == opt.clobber) and os.path.exists(outfilename):
        doMessage(logger,msg.ERR,'Outfile exits:',outfilename)
        doMessage(logger,msg.ERR,'Please remove or rename outfile(s) and try again')
        sys.exit(1)

    #    a FS reference scan integration (1st pass) is the F part of the SIG data
    #    a FS reference scan (2nd pass) is the T part of the SIG data
    #    on each pass the signal/map scan is the remainder of the data

    #    signal,reference = splitFSscan(scan,sdfitsdata,opt.verbose)
    
    #    Ta1 = sig-ref/ref
    
    #    switch signal and reference
    
    #    Ta2 = sig-ref/ref
    
    #    average
    #    Ta = (Ta1+Ta2) / 2
    # ----------------  calibrate all integrations to Ta* or requested
    # ----------------------------  if not possible, calibrate to Ta

    calibrated_integrations = []
    nchans = False # number of channels, used to filter of 2% from either edge

    for scan in allscans:
        doMessage(logger,msg.DBG,'Calibrating scan:',scan)

        mapscan = scanreader.ScanReader()
        mapscan.setLogger(logger)
        
        mapscan.get_scan(scan,sdfitsdata,opt.verbose)
        nchans = len(mapscan.data[0])

        # set relative gain factors for each beam/pol
        #  if they are supplied
        gain_factor = gainfactor(opt,samplermap,sampler)

        cal_ints = mapscan.calibrate_fs()

        #print cal_ints.mean(0)
        #cal_ints = mapscan.calibrate_fs(logger,refspec,refdate,ref_tsys,\
            #k_per_count,opacity_coeffs,opt.gaincoeffs,opt.spillover,\
            #opt.aperture_eff,fbeampol,ref_tsky,opt.units,gain_factor,opt.verbose)

        if len(calibrated_integrations):
            calibrated_integrations = np.concatenate((calibrated_integrations,cal_ints))
        else: # first scan
            calibrated_integrations = cal_ints
        
    del sdfitsdata

    # ---------------------------------- write out calibrated fits file

    primary = pyfits.PrimaryHDU()
    primary.header = infile[0].header
    
    sdfits = pyfits.new_table(pyfits.ColDefs(infile[blockid].columns),nrows=len(calibrated_integrations),fill=1)

    # add in virtual columns (keywords)
    inCardList = infile[blockid].header.ascardlist()
    for key in ["TELESCOP","CTYPE4","PROJID","BACKEND","SITELONG","SITELAT","SITEELEV"]:
        card = inCardList[key]
        sdfits.header.update(key,card.value,card.comment)

    print calibrated_integrations.shape,type(calibrated_integrations)
    print type(sdfits),type(sdfits.data),len(sdfits.data),np.__version__

    for idx,ee in enumerate(calibrated_integrations):
        sdfits.data[idx] = ee

    sdfits.name = 'SINGLE DISH'

    hdulist = pyfits.HDUList([primary,sdfits])
    hdulist.writeto(outfilename,clobber=opt.clobber)
    hdulist.close()
    del hdulist

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

    if not opt.display_idlToSdfits:
        options = options + ' -l '

    if opt.idlToSdfits_rms_flag:
        options = options + ' -n ' + opt.idlToSdfits_rms_flag + ' '
        
    if opt.verbose > 4:
        options = options + ' -v 2 '
    else:
        options = options + ' -v 0 '

    if opt.idlToSdfits_baseline_subtract:
        options = options + ' -w ' + opt.idlToSdfits_baseline_subtract + ' '
        
    idlcmd = '/opt/local/bin/idlToSdfits -o ' + aipsinname + options + outfilename

    doMessage(logger,msg.DBG,idlcmd)

    os.system(idlcmd)
    
    doMessage(logger,msg.INFO,'Finished calibrating: scans',allscans[0],'to',\
              allscans[-1],', beam',' '.join(map(str,samplermap[sampler])),'Hz')
    cc.send(outfilename)

def do_sampler_ps(cc,sampler,logger,block_found,blockid,samplermap,allscans,\
                  refscans,scans,masks,opt,infile,fbeampol,opacity_coeffs):

    doMessage(logger,msg.DBG,'-----------')
    doMessage(logger,msg.DBG,'SAMPLER',sampler)
    doMessage(logger,msg.DBG,'-----------')

    try:
        samplermask = masks[blockid-1].pop(sampler)
    except(TypeError):
        doMessage(logger,msg.ERR,'ERROR: TypeError when defining samplermask')
        doMessage(logger,msg.DBG,'sampler',sampler)
        doMessage(logger,msg.DBG,'blockid',blockid)
        doMessage(logger,msg.DBG,'len(samplerlist)',len(samplerlist))
        doMessage(logger,msg.DBG,'len(masks)',len(masks))
        doMessage(logger,msg.DBG,'len(masks[0])',len(masks[0]))
        doMessage(logger,msg.DBG,'type(masks)',type(masks))
        doMessage(logger,msg.DBG,'type(masks[0])',type(masks[0]))
        sys.exit(9)
    except(KeyError):
        doMessage(logger,msg.ERR,'ERROR: KeyError when defining samplermask')
        doMessage(logger,msg.DBG,'type(sampler)',type(sampler))
        doMessage(logger,msg.DBG,'sampler',sampler)
        doMessage(logger,msg.DBG,'type(samplers)',type(thismap_samplerlist))
        doMessage(logger,msg.DBG,'samplers',thismap_samplerlist)
        sys.exit(9)

    doMessage(logger,msg.DBG,'appying mask')
    if block_found:
        doMessage(logger,msg.DBG,'to extension',blockid)
        sdfitsdata = infile[blockid].data[samplermask]
        doMessage(logger,msg.DBG,'length of sampler-filtered data block is',len(sdfitsdata))
        del samplermask
    doMessage(logger,msg.DBG,'done')

    freq=0
    refspec = []
    refdate = []
    ref_tsky = []
    ref_tsys = []

    # ------------------------------------------- name output file
    scan=allscans[0]
    mapscan = scanreader.ScanReader()
    mapscan.setLogger(logger)

    obj,centerfreq,feed = mapscan.map_name_vals(scan,sdfitsdata,opt.verbose)
    outfilename = obj + '_' + str(feed) + '_' + \
                str(allscans[0]) + '_' + str(allscans[-1]) + '_' + \
                str(centerfreq)[:6] + '_' + sampler + '.fits'
    import warnings
    def send_warnings_to_logger(message, category, filename, lineno, file=None, line=None):
        doMessage(logger,msg.WARN,message)
    warnings.showwarning = send_warnings_to_logger
    warnings.filterwarnings('once', '.*converting a masked element to nan.*',)

    doMessage(logger,msg.DBG,'outfile name',outfilename)
    if (False == opt.clobber) and os.path.exists(outfilename):
        doMessage(logger,msg.ERR,'Outfile exits:',outfilename)
        doMessage(logger,msg.ERR,'Please remove or rename outfile(s) and try again')
        sys.exit(1)

    # ------------------------------------------- get the first reference scan
    scan=refscans[0]
    doMessage(logger,msg.DBG,'Processing reference scan:',scan)

    ref1 = scanreader.ScanReader()
    ref1.setLogger(logger)

    ref1.get_scan(scan,sdfitsdata,opt.verbose)

    ref1spec,ref1_max_tcal,ref1_mean_date,freq,tskys_ref1,ref1_tsys = \
        ref1.average_reference(logger,opt.units,opt.gaincoeffs,opt.spillover,\
        opt.aperture_eff,fbeampol,opacity_coeffs,opt.verbose)

    refdate.append(ref1_mean_date)
    ref_tsky.append(tskys_ref1)

    # determine scale factor used to compute Tsys of each integration
    try:
        k_per_count = ref1_max_tcal / ref1.calonoff_ave_diff() # dcSCal in scaleIntsRef
    except FloatingPointError:
        doMessage(logger,msg.ERR,ref1_max_tcal)
        doMessage(logger,msg.ERR,ref1.calonoff_ave_diff())

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
    doMessage(logger,msg.DBG,'REF 1')
    doMessage(logger,msg.DBG,'dcCal (avg. calON-calOFF):',ref1.calonoff_ave_diff().mean())
    doMessage(logger,msg.DBG,'avg. K/count from ref1:',k_per_count.mean())
    doMessage(logger,msg.DBG,'ON AVE [0][1000][nChan]',onave1[0],onave1[1000],onave1[-1])
    doMessage(logger,msg.DBG,'OFF AVE [0][1000][nChan]',offave1[0],offave1[1000],offave1[-1])
    doMessage(logger,msg.DBG,'dcRef1',dcRef1[0],dcRef1[1000],dcRef1[-1])
    doMessage(logger,msg.DBG,'ref1 Tsys:',tsysRef1)

    # ------------------------------------------- gather all map CALON-CALOFFS to scale
    # -------------------------------------------  reference scan counts to kelvin
    if opt.mapscansforscale:
        calonAVEs=[]
        caloffAVEs=[]
        maxTCAL=0

        for scan in allscans:
            doMessage(logger,msg.DBG,'Processing map scan:',scan)
            mapscan = scanreader.ScanReader()
            mapscan.setLogger(logger)

            mapscan.get_scan(scan,sdfitsdata,opt.verbose)

            if len(calonAVEs):
                calonAVEs = np.ma.vstack((calonAVEs,mapscan.calon_ave()))
                caloffAVEs = np.ma.vstack((caloffAVEs,mapscan.caloff_ave()))
            else:
                calonAVEs  = mapscan.calon_ave()
                caloffAVEs = mapscan.caloff_ave()
                calonAVEs  = calonAVEs.reshape((1,len(calonAVEs)))
                caloffAVEs = caloffAVEs.reshape((1,len(caloffAVEs)))

            thisTCAL = mapscan.max_tcal()
            if thisTCAL > maxTCAL:
                maxTCAL = thisTCAL

        sig_calONave = calonAVEs.mean(0)
        sig_calOFFave = caloffAVEs.mean(0)
        
        sig_calONOFFdiff = sig_calONave - sig_calOFFave

        doMessage(logger,msg.DBG,'sig calON mean',sig_calONave.mean())
        doMessage(logger,msg.DBG,'sig calOFF mean',sig_calOFFave.mean())
        doMessage(logger,msg.DBG,'sig calON-OFF mean',sig_calONOFFdiff.mean())
        
        map_scans_cal_smoothed = smoothing.smooth_spectrum(sig_calONOFFdiff,freq)

        # ---------------------------------------- set scaling factor, kelvins per count
        k_per_count = maxTCAL / sig_calONOFFdiff
    
    doMessage(logger,msg.DBG,"K/count (mean)",k_per_count.mean())

    # ------------------------------------------- get the last reference scan
    if len(refscans)>1:
        scan=refscans[-1]
        doMessage(logger,msg.DBG,'Processing reference scan:',scan)

        ref2 = scanreader.ScanReader()
        ref2.setLogger(logger)
        
        ref2.get_scan(scan,sdfitsdata,opt.verbose)

        ref2spec,ref2_max_tcal,ref2_mean_date,freq,tskys_ref2,ref2_tsys = \
            ref2.average_reference(logger,opt.units,opt.gaincoeffs,opt.spillover,\
            opt.aperture_eff,fbeampol,opacity_coeffs,opt.verbose)
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
        tsysRef2 = ratios.mean()*ref2_max_tcal  # eqn. (4)
        ref_tsys.append(tsysRef2)

        doMessage(logger,msg.DBG,'REF 2')
        doMessage(logger,msg.DBG,'ON AVE [0][1000][nChan]',onave2[0],onave2[1000],onave2[-1])
        doMessage(logger,msg.DBG,'OFF AVE [0][1000][nChan]',offave2[0],offave2[1000],offave2[-1])
        doMessage(logger,msg.DBG,'dcRef2',dcRef2[0],dcRef2[1000],dcRef2[-1])
        doMessage(logger,msg.DBG,'ref2 Tsys:',tsysRef2)

    # ----------------  calibrate all integrations to Ta* or requested
    # ----------------------------  if not possible, calibrate to Ta

    calibrated_integrations = []
    nchans = False # number of channels, used to filter of 2% from either edge

    for scan in allscans:
        doMessage(logger,msg.DBG,'Calibrating scan:',scan)

        mapscan = scanreader.ScanReader()
        mapscan.setLogger(logger)
        
        mapscan.get_scan(scan,sdfitsdata,opt.verbose)
        nchans = len(mapscan.data[0])

        # set relative gain factors for each beam/pol
        #  if they are supplied
        gain_factor = gainfactor(opt,samplermap,sampler)

        cal_ints = mapscan.calibrate_to(logger,refspec,refdate,ref_tsys,\
            k_per_count,opacity_coeffs,opt.gaincoeffs,opt.spillover,\
            opt.aperture_eff,fbeampol,ref_tsky,opt.units,gain_factor,opt.verbose)

        if len(calibrated_integrations):
            calibrated_integrations = np.concatenate((calibrated_integrations,cal_ints))
        else: # first scan
            calibrated_integrations = cal_ints

    del sdfitsdata

    # ---------------------------------- write out calibrated fits file

    primary = pyfits.PrimaryHDU()
    primary.header = infile[0].header
    
    sdfits = pyfits.new_table(pyfits.ColDefs(infile[blockid].columns),nrows=len(calibrated_integrations),fill=1)

    # add in virtual columns (keywords)
    inCardList = infile[blockid].header.ascardlist()
    for key in ["TELESCOP","CTYPE4","PROJID","BACKEND","SITELONG","SITELAT","SITEELEV"]:
        card = inCardList[key]
        sdfits.header.update(key,card.value,card.comment)

    for idx,ee in enumerate(calibrated_integrations):
        sdfits.data[idx] = ee

    sdfits.name = 'SINGLE DISH'

    hdulist = pyfits.HDUList([primary,sdfits])
    hdulist.writeto(outfilename,clobber=opt.clobber)
    hdulist.close()
    del hdulist

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

    if not opt.display_idlToSdfits:
        options = options + ' -l '

    if opt.idlToSdfits_rms_flag:
        options = options + ' -n ' + opt.idlToSdfits_rms_flag + ' '
        
    if opt.verbose > 4:
        options = options + ' -v 2 '
    else:
        options = options + ' -v 0 '

    if opt.idlToSdfits_baseline_subtract:
        options = options + ' -w ' + opt.idlToSdfits_baseline_subtract + ' '
        
    idlcmd = '/opt/local/bin/idlToSdfits -o ' + aipsinname + options + outfilename

    doMessage(logger,msg.DBG,idlcmd)

    os.system(idlcmd)
    
    doMessage(logger,msg.INFO,'Finished calibrating: scans',allscans[0],'to',\
              allscans[-1],', beam',' '.join(map(str,samplermap[sampler])),'Hz')
    cc.send(outfilename)

def process_a_single_map(scans,masks,opt,infile,samplerlist,fbeampol,opacity_coeffs):
    """
    """
    
    allscans = scans[1]
    
    if 0==len(allscans):
        print 'ERROR: no map scans in this block'
        print '       please check SCANID values'
        return

    refscans = [scans[0]]
    if scans[2]:
        refscans.append(scans[2])

    samplermap = scans[3]
    maptype = scans[4]

    try:
        logfilename = 'scans_'+str(allscans[0])+'_'+str(allscans[-1])+'_'+timestamp()+'.log'
        
    except(IndexError):
        print allscans
        sys.exit(9)
        
    logger = pipeutils.configure_logfile(opt,logfilename)

    doMessage(logger,msg.DBG,'finding scans')
    
    block_found = False
    
    for blockid in range(1,len(infile)):
        if allscans[-1] <= infile[blockid].data[-1].field('SCAN'):
            block_found = True
            doMessage(logger,msg.DBG,'scan',allscans[-1],'found in extension',blockid)
            break
    if not block_found:
        doMessage(logger,msg.ERR,'ERROR: map scans not found for scan',allscans[-1])
        sys.exit(9)

    doMessage(logger,msg.DBG,'done')

    # --allmaps set
    if opt.allmaps:
        doMessage(logger,msg.DBG,scans,blockid,samplerlist[blockid-1])
        thismap_samplerlist = samplerlist[blockid-1]
    else:
        doMessage(logger,msg.DBG,'scans',scans)
        doMessage(logger,msg.DBG,'blockid',blockid)
        thismap_samplerlist = samplerlist
        doMessage(logger,msg.DBG,'thismap_samplerlist',thismap_samplerlist)

    # if the sampler list is not actually a list, make sure to
    #  change it to one.
    #  code below expects a list of samplers, so we want to make sure that
    #  does not break
    if type([]) != type(thismap_samplerlist):
        thismap_samplerlist = [thismap_samplerlist]

# ---------------------------------------------------------------- start parallelism
    if opt.process_max:
        process_group_max = opt.process_max
    else:
        cpucount = multiprocessing.cpu_count()
        number_of_samplers = len(thismap_samplerlist)

        if cpucount < number_of_samplers:
            process_group_max = cpucount
        else:
            process_group_max = number_of_samplers

        process_group_max = int(math.ceil(float(process_group_max)/2))

    doMessage(logger,msg.INFO,'Maxiumum number of running processes:',process_group_max)
    lcl_samplerlist = thismap_samplerlist[:]
    while(lcl_samplerlist):
        process_ids = []
        cc, dd = multiprocessing.Pipe()
        samplergroup = []
        for idx in range(process_group_max):
            if lcl_samplerlist:
                samplergroup.append(lcl_samplerlist.pop(-1))
                
        if maptype == 'FS':
            target = do_sampler_fs
        else:
            target = do_sampler_ps

        for sampler in samplergroup:
            # create a process for each sampler
            process_ids.append(multiprocessing.Process(target=target,
                args=(dd,sampler,logger,block_found,blockid,samplermap,allscans,\
                refscans,scans,masks,opt,infile,fbeampol,opacity_coeffs)) )
        
        for pp in process_ids:
            pp.start()

        outfilenames = []
        for pp in process_ids:
            outfilenames.append(cc.recv())
            pp.join()

# ---------------------------------------------------------------- end parallelism

    if not opt.imagingoff:
        aipsNumber = str(os.getuid())
        doMessage(logger,msg.DBG,'aips number: ',aipsNumber)

        freq_set = set([])
        for outfilename in outfilenames:
            outsplit = outfilename.split('_')
            target = outsplit[0]
            scan_b = outsplit[2]
            scan_e = outsplit[3]
            freq_set.add(outsplit[4])

        doMessage(logger,msg.INFO,'Imaging center frequencies:',' & '.join(freq_set),'MHz')
        
        for freq in freq_set:
            doMessage(logger,msg.INFO,'Started imaging scans',scan_b,'to',scan_e,'with center frequency',freq,'MHz')
            filenames = target + '*' + scan_b + '_' + scan_e + '_' + freq + '*.sdf'
            doimg_cmd = ' '.join(('doImage',opt.imageScript,aipsNumber,filenames))
            doMessage(logger,msg.DBG,doimg_cmd)

            p = subprocess.Popen(doimg_cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            aips_stdout,aips_stderr = p.communicate()

            doMessage(logger,msg.DBG,aips_stdout)
            doMessage(logger,msg.DBG,aips_stderr)
            doMessage(logger,msg.INFO,'... done')
