USE_MAP_SCAN_FOR_SCALE=True

import os
import sys

import numpy as np
import pyfits

import scanreader
import smoothing
import pipeutils
from pipeutils import *

def process_a_single_map(scans,masks,opt,infile,samplerlist,gaincoeffs,fbeampol,opacity_coeffs):
    
    allscans = scans[1]
    refscans = [scans[0]]
    if scans[2]:
        refscans.append(scans[2])

    logfilename = 'scans_'+str(allscans[0])+'_'+str(allscans[-1])+'.log'
    logger = pipeutils.configure_logfile(opt,logfilename,toconsole=False)
    
    doMessage(logger,msg.INFO,'finding scans')
    
    block_found = False
    
    for blockid in range(1,len(infile)):
        if allscans[-1] <= infile[blockid].data[-1].field('SCAN'):
            block_found = True
            doMessage(logger,msg.DBG,'scan',allscans[-1],'found in extension',blockid)
            break
    if not block_found:
    	doMessage(logger,msg.ERR,'ERROR: map scans not found for scan',allscans[-1])
        sys.exit(9)

    doMessage(logger,msg.INFO,'done')

    doMessage(logger,msg.INFO,'sampler list', samplerlist)

    if type(samplerlist[0])!=type([]):
        samplerlist = [samplerlist]
    
    doMessage(logger,msg.DBG,scans,blockid,samplerlist[blockid-1])

    for sampler in samplerlist[blockid-1]:
        
        doMessage(logger,msg.INFO,'-----------')
        doMessage(logger,msg.INFO,'SAMPLER',sampler)
        doMessage(logger,msg.INFO,'-----------')

        samplermask = masks[blockid-1].pop(sampler)

        doMessage(logger,msg.INFO,'appying mask')
        if block_found:
            doMessage(logger,msg.DBG,'to extension',blockid)
            sdfitsdata = infile[blockid].data[samplermask]
            doMessage(logger,msg.DBG,'length of sampler-filtered data block is',len(sdfitsdata))
            del samplermask
        doMessage(logger,msg.INFO,'done')
        
        freq=0
        refspec = []
        refdate = []
        ref_tsky = []
        ref_tsys = []
        
        # ------------------------------------------- name output file
        scan=allscans[0]
        mapscan = scanreader.ScanReader()
        mapscan.setLogger(logger)
        
        obj,centerfreq,feed = mapscan.map_name_vals(sdfitsdata,opt.verbose)
        outfilename = obj + '_' + str(feed) + '_' + \
                      str(allscans[0]) + '_' + str(allscans[-1]) + '_' + \
                      str(centerfreq)[:6] + '_' + sampler + '.fits'
        logfile = open(outfilename.split('.')[:-1][0]+'.log', 'w')
        class Log(object):
            def write(self, msg):
                logfile.write("LOG: "+msg)
        log = Log()
        saved_handler = np.seterrcall(log)
        np.seterr(all='log')
        import warnings
        #warnings.simplefilter('once', UserWarning)
        warnings.filterwarnings('ignore', '.*converting a masked element to nan.*',)

        doMessage(logger,msg.INFO,'outfile name',outfilename)
        if (False == opt.clobber) and os.path.exists(outfilename):
            doMessage(logger,msg.ERR,'Outfile exits:',outfilename)
            doMessage(logger,msg.ERR,'Please remove or rename outfile(s) and try again')
            sys.exit(1)

        # ------------------------------------------- get the first reference scan
        scan=refscans[0]
        doMessage(logger,msg.INFO,'Processing reference scan:',scan)
        
        ref1 = scanreader.ScanReader()
        ref1.setLogger(logger)
		
        ref1.get_scan(scan,sdfitsdata,opt.verbose)
        
        ref1spec,ref1_max_tcal,ref1_mean_date,freq,tskys_ref1,ref1_tsys = \
            ref1.average_reference(opt.units,gaincoeffs,opt.spillover,\
            opt.aperture_eff,fbeampol,opacity_coeffs,opt.verbose)
        
        refdate.append(ref1_mean_date)
        ref_tsky.append(tskys_ref1)
        
        # determine scale factor used to compute Tsys of each integration
        try:
            k_per_count = ref1_max_tcal / ref1.calonoff_diff() # dcSCal in scaleIntsRef
        except FloatingPointError:
            doMessage(logger,msg.ERR,ref1_max_tcal)
            doMessage(logger,msg.ERR,ref1.calonoff_diff())
            
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
        doMessage(logger,msg.DBG,'dcCal (avg. calON-calOFF):',ref1.calonoff_diff().mean())
        doMessage(logger,msg.DBG,'avg. K/count from ref1:',k_per_count.mean())
        doMessage(logger,msg.DBG,'ON AVE [0][1000][nChan]',onave1[0],onave1[1000],onave1[-1])
        doMessage(logger,msg.DBG,'OFF AVE [0][1000][nChan]',offave1[0],offave1[1000],offave1[-1])
        doMessage(logger,msg.DBG,'dcRef1',dcRef1[0],dcRef1[1000],dcRef1[-1])
        doMessage(logger,msg.DBG,'ref1 Tsys:',tsysRef1)
        
        # ------------------------------------------- gather all map CALON-CALOFFS to scale
        # -------------------------------------------  reference scan counts to kelvin
        if USE_MAP_SCAN_FOR_SCALE:
            calonAVEs=[]
            caloffAVEs=[]
            maxTCAL=0
            
            for scan in allscans:
                doMessage(logger,msg.INFO,'Processing map scan:',scan)
                mapscan = scanreader.ScanReader()
                mapscan.setLogger(logger)
                
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
            doMessage(logger,msg.INFO,'Processing reference scan:',scan)
            
            ref2 = scanreader.ScanReader()
            ref2.setLogger(logger)
            
            ref2.get_scan(scan,sdfitsdata,opt.verbose)
            
            ref2spec,ref2_max_tcal,ref2_mean_date,freq,tskys_ref2,ref2_tsys = \
                ref2.average_reference(opt.units,gaincoeffs,opt.spillover,\
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
            tsysRef2 = ratios.mean()*ref2_max_tcal
            ref_tsys.append(tsysRef2)
            
            doMessage(logger,msg.DBG,'REF 2')
            doMessage(logger,msg.DBG,'ON AVE [0][1000][nChan]',onave2[0],onave2[1000],onave2[-1])
            doMessage(logger,msg.DBG,'OFF AVE [0][1000][nChan]',offave2[0],offave2[1000],offave2[-1])
            doMessage(logger,msg.DBG,'dcRef2',dcRef2[0],dcRef2[1000],dcRef2[-1])
            doMessage(logger,msg.DBG,'ref2 Tsys:',tsysRef2)

        # --------------------------  calibrate all integrations to Tb
        # ----------------------------  if not possible, calibrate to Ta

        calibrated_integrations = []
        nchans = False # number of channels, used to filter of 2% from either edge
        
        for scan in allscans:
            doMessage(logger,msg.INFO,'Calibrating scan:',scan)

            mapscan = scanreader.ScanReader()
            mapscan.setLogger(logger)
            
            mapscan.get_scan(scan,sdfitsdata,opt.verbose)
            nchans = len(mapscan.data[0])

            mapscan.mean_date()
            cal_ints = mapscan.calibrate_to(refspec,refdate,ref_tsys,\
                k_per_count,opacity_coeffs,gaincoeffs,opt.spillover,\
                opt.aperture_eff,fbeampol,ref_tsky,opt.units,opt.verbose)
            
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
        
        if opt.nodisplay:
            options = options + ' -l '
            
        idlcmd = 'idlToSdfits -o ' + aipsinname + options + outfilename
        doMessage(logger,msg.INFO,idlcmd)
        
        os.system(idlcmd)
