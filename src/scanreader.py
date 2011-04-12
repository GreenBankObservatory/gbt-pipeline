import smoothing
import pipeutils
from pipeutils import *

import numpy as np
import math
import sys

class ScanReader():
    """The primary class for reading sdfits input.

    In addition to reading all required information from the sdfits
    input, ScanReader will perform basic averaging, and calibration
    (always for a single scan and usually for a single sampler).
    """
    
    def __init__(self):
        self.attr = {}
        self.attr['date'] = []
        self.attr['polarization'] = []
        self.attr['elevation'] = []
        self.attr['ra'] = []
        self.attr['dec'] = []
        self.attr['calmask'] = []
        
        self.attr['exposure'] = []
        self.attr['tcal'] = []
        self.attr['crpix1'] = []
        self.attr['crval1'] = []
        self.attr['cdelt1'] = []
        self.attr['row'] = []
        self.attr['tambient'] = []

        self.data = []
        self.statemask = []

        self.feeds = set([])
        self.integrations = set([])
        self.n_channels = set([])
        self.cals = set([])

        self.ifs=set([])

        self.frequency_resolution = 0
        self.noise_diode = False
        
    def setLogger(self,logger):
        self.logger = logger

    def map_name_vals(self,first_map_scan,fdata,verbose):
        """Collect information for naming the output file

        Required information comes from the column values in the sdfits
        input file.  It is only necessary to read a single row, so we
        return after finding the first integration with a scan
        number from the map.  For convenience, we use the first scan 
        number from the map.
        
        Keyword arguments:
        first_map_scan -- first scan number of the map
        fdata -- sdfits input table pointer
        verbose -- verbosity level
        
        Returns:
        obj -- the "OBJECT" col. val. in the sdfits input
        centerfreq -- the freqency at the center channel
        feed -- the feed number from "FEED" col. in the sdfits input
        """

        scanmask = fdata.field('SCAN')==int(first_map_scan)
        lcldata = fdata[scanmask]

        obj = lcldata.field('OBJECT')[0]
        feed = lcldata.field('FEED')[0]
        centerfreq = lcldata.field('CRVAL1')[0]

        return obj,centerfreq,feed

    def get_scan(self,scan_number,fdata,verbose):
        """Collect all primary needed information for a given scan.

        Keyword arguments:
        scan_number -- 
        fdata -- sdfits input table pointer
        verbose -- verbosity level

        """
        doMessage(self.logger,msg.DBG,type(fdata),len(fdata),scan_number)
        scanmask = fdata.field('SCAN')==int(scan_number)
        #doMessage(self.logger,msg.DBG,scanmask)
        lcldata = fdata[scanmask]
        
        for idx,row in enumerate(lcldata):
            self.attr['row'].append(row)
            self.attr['date'].append(row['DATE-OBS'])
            self.attr['polarization'].append(row['CRVAL4'])
            self.attr['elevation'].append(row['ELEVATIO'])
            self.attr['crval1'].append(row['CRVAL1'])
            self.attr['crpix1'].append(row['CRPIX1'])
            self.attr['cdelt1'].append(row['CDELT1'])
            self.attr['ra'].append(row['CRVAL2'])
            self.attr['dec'].append(row['CRVAL3'])

            if len(self.data):
                self.data = np.vstack((self.data,row['DATA']))
            else:
                self.data = np.array(row['DATA'],ndmin=2)
            self.attr['tcal'].append(row['TCAL'])
            self.attr['exposure'].append(row['EXPOSURE'])
            self.attr['tambient'].append(row['TAMBIENT'])

            # create mask for calONs and calOFFs
            if 'T'==row['CAL']:
                self.attr['calmask'].append(True)
            else:
                self.attr['calmask'].append(False)

            # create mask for frequency-swithced states
            if 'T'==row['SIG']:
                self.statemask.append(True)
            else:
                self.statemask.append(False)

            self.frequency_resolution = row['FREQRES']

            # count number of feeds and cal states
            self.feeds.add(row['FEED'])
            self.cals.add(row['CAL'])

        # convert attr lists to numpy arrays
        for xx in self.attr: self.attr[xx]=np.array(self.attr[xx])
        
        # add an axis, allowing attributes to be stored
        #   into two states for frequency switched mode
        # to keep code consistent, will add an axis for PS mode
        #   so all attributes are accesible with first dim=0
        #   in other words, a NxM array would be accessed
        #   after this call with a[0][N][M]
        for xx in self.attr: self.attr[xx]=np.array(self.attr[xx],ndmin=2)

        # convert statemask to numpy array
        self.statemask = np.array(self.statemask)

        # change data into a masked array to remove effect of nans
        self.data = np.ma.masked_array(self.data,np.isnan(self.data),ndmin=3)

        # set a flag if the noise diode is firing
        if len(self.cals)==2:
            self.noise_diode = True
        else:
            self.noise_diode = False
            
        doMessage(self.logger,msg.DBG,'feeds',len(self.feeds))
        doMessage(self.logger,msg.DBG,'n_polarizations',len(set(self.attr['polarization'][0])))
        doMessage(self.logger,msg.DBG,'n_cals',len(self.cals))
        doMessage(self.logger,msg.DBG,'n_channels',len(self.data[0][0]))

        doMessage(self.logger,msg.DBG,'nrecords',len(self.data[0]))
        doMessage(self.logger,msg.DBG,'frequency_resolution',self.frequency_resolution,'Hz')

    def calonoffave_ave(self,state=0):
        """Get average of average Cal-on spectra and average Cal-off

        Keyword arguments:
        
        Returns:
        The mean of the CAL ON and CAL OFF spectra.  The vector size is
        the same as the number of channels in each input spectrum.
        """
        
        return (self.calon_ave(state)+self.caloff_ave(state))/2.

    def calonoff_ave(self,state=0):
        """Get average of Cal-on spectra and Cal-off

        Keyword arguments:
        
        Returns:
        The mean of the CAL ON and CAL OFF spectra.  The vector size is
        the same as the number of channels in each input spectrum.
        """

        data = self.data[state]
        calmask = self.attr['calmask'][state]
        
        return (data[calmask]+data[~calmask])/2.

    def calonoff_ave_diff(self,state=0):
        """Get average CalON minus average CalOFF

        Keyword arguments:
        
        Returns:
        The CAL (ON-OFF).  The vector size is
        the same as the number of channels in each input spectrum.
        """
        
        return self.calon_ave(state) - self.caloff_ave(state)

    def calonoff_diff(self,state=0):
        """Get CalON minus CalOFF

        Keyword arguments:
        
        Returns:
        The CAL (ON-OFF).  The vector size is
        the same as the number of channels in each input spectrum.
        """

        data = self.data[state]
        calmask = self.attr['calmask'][state]
        
        return data[calmask]-data[~calmask]

    def calon_ave(self,state=0):
        """Get the exposure-weighted average of Cal-on spectra for given

        Keyword arguments:

        Returns:
        The exposure-weighted mean of the CALON spectra.  The vector size is
        the same as the number of channels in each input spectrum.
        """
        
        data = self.data[state]
        exposure = self.attr['exposure'][state]
        calmask = self.attr['calmask'][state]

        return np.ma.average(data[calmask],axis=0,weights=exposure[calmask])

    def elevation_ave(self):
        """Get an exposure-weighted average elevation

        Keyword arguments:

        Returns:
        The exposure-weighted mean of elevation
        """
        
        # apply sampler filter
        elevation = self.attr['elevation']
        exposure = self.attr['exposure']
        calmask = self.attr['calmask']

        return np.ma.average(elevation[calmask],axis=0,weights=exposure[calmask])

    def caloff_ave(self,state=0):
        """Get the exposure-weighted average of Cal-off spectra

        Keyword arguments:
        
        Returns:
        A exposure-weighted mean of the CALOFF spectra.  The vector size is
        the same as the number of channels in each input spectrum.
        """
        
        data = self.data[state]
        exposure = self.attr['exposure'][state]
        calmask = self.attr['calmask'][state]
        
        return np.ma.average(data[~calmask],axis=0,weights=exposure[~calmask])

    def max_tcal(self,verbose=0):
        """Get max tcal value for all spectra for given sampler

        Keyword arguments:
        sampler -- the sampler number
        verbose -- verbosity level, default to 0
        
        Returns:
        The max tcal value for the sampler.
        """
        
        # apply sampler filter
        tcal = self.attr['tcal']
        return tcal.max()

    def mean_date(self,verbose=0):
        """Get mean date (as mjd) for all spectra for given sampler

        Keyword arguments:
        sampler -- the sampler number
        verbose -- verbosity level, default to 0
        
        Returns:
        A vector of mean dates (as mjd) for the sampler.
        """
        
        # apply sampler filter
        dates = self.attr['date']
        mjds = np.array([ pipeutils.dateToMjd(xx) for xx in dates ])
        return mjds.mean()

    def min_date(self,verbose=0):
        """Get mean date for all spectra for given sampler

        Keyword arguments:
        sampler -- the sampler number
        verbose -- verbosity level, default to 0
        
        Returns:
        A vector of minumum dates for the sampler, one for each integration.
        If noise diode is firing, there is one date for each pair of integrations.
        """
        
        # apply sampler filter
        dates = self.attr['date']
        calmask = self.attr['calmask']
        
        if self.noise_diode:
            dates = dates[calmask]

        return pipeutils.dateToMjd(dates[0])
        
    def freq_axis_mean(self,state=0,verbose=0):
        """ frequency axis to return for plotting

        Keyword arguments:
        sampler -- the sampler number
        verbose -- verbosity level, default to 0
        
        Returns:
        A single mean frequency axis for the scan.
        """
        
        # apply sampler filter
        data = self.data[state]

        crpix1 = self.attr['crpix1'][state].mean()
        cdelt1 = self.attr['cdelt1'][state].mean()
        crval1 = self.attr['crval1'][state].mean()

        faxis = np.zeros(len(data[0]))
        for idx,e in enumerate(data[0]):
            faxis[idx] = ((idx-crpix1)*cdelt1+crval1)

        return faxis

    def freq_axis(self,state=0,verbose=0):
        """ frequency axis to return for plotting

        Keyword arguments:
        sampler -- the sampler number
        verbose -- verbosity level, default to 0
        
        Returns:
        A frequency axis vector for the scan.
        """
        
        # apply sampler filter
        calmask = self.attr['calmask'][state]
        data = self.data[state][calmask]
        crpix1 = self.attr['crpix1'][state][calmask]
        cdelt1 = self.attr['cdelt1'][state][calmask]
        crval1 = self.attr['crval1'][state][calmask]

        faxis = np.zeros(data.shape)
        
        for idx,ee in enumerate(data):
            for chan,ee in enumerate(data[0]):
                faxis[idx][chan] = ((chan-crpix1[idx])*cdelt1[idx]+crval1[idx])

        return faxis

        #refChan = crpix1-1
        #observed_frequency = crval1
        #nchan = np.array([len(data[0])] * len(data))
        #delChan = cdelt1
        #freq_lo = observed_frequency + (0-refChan)*delChan
        #freq_hi = observed_frequency + (nchan-refChan)*delChan
        #freq = np.array([freq_lo,freq_hi])
        #faxis = freq.transpose()

        #return faxis

    def average_tsys(self,state=0,verbose=0):
        """Get the total power for a single scan (i.e. feed,pol,IF)

        Keyword arguments:
        verbose -- verbosity level, default to 0
        
        Returns:
        An averaged, weighted sytem temperature, using the center 80% of
        the band.
        """

        # apply sampler filter
        data = self.data[state]

        tcal = self.attr['tcal'][state]

        chanlo = int(len(data)*.1)
        chanhi = int(len(data)*.9)

        ref = self.calonoffave_ave(state)
        cal = self.calonoff_ave_diff(state)

        ratios = ref[chanlo:chanhi] / cal[chanlo:chanhi]
        mytsys = ratios.mean() * self.max_tcal()

        Tsys = mytsys
        doMessage(self.logger,msg.DBG,'Tsys', Tsys)
        doMessage(self.logger,msg.DBG,'Tcal', tcal.mean())

        return Tsys

    def tsys(self,state,verbose=0):
        """Get the total power for every integration of scan
        
        (i.e. feed,pol,IF)

        Keyword arguments:
        verbose -- verbosity level, default to 0
        
        Returns:
        An averaged, weighted sytem temperature, using the center 80% of
        the band.
        """

        # apply sampler filter
        data = self.data[state]

        calmask = self.attr['calmask'][state]
        tcal = self.attr['tcal'][state][calmask]
        
       
        calon = data[calmask]
        caloff = data[~calmask]

        Tsys = np.ones(calon.shape)
        mean_tsys = np.ones(calon.shape)

        # determine the channel numbers bounding the center 80% of the band
        chanlo = int(len(data[0])*.1)
        chanhi = int(len(data[0])*.9)
        
        # comput the tsys and average the center 80% for each integration
        for idx,ee in enumerate(Tsys):
            # compute the tsys at every channel across the band for
            #   a single (SIG or REF) integration
            Tsys[idx] = tcal[idx] * ( (calon[idx]+caloff[idx]) / (2*(calon[idx]-caloff[idx])) )
            # average the tsys across the center 80% of the band for
            #   each integration's spectrum
            mean_tsys[idx] = (Tsys[idx][chanlo:chanhi]).mean()

        # return a vector of average (center 80%) tsys values for each
        #   integration of a single state (SIG or REF).
        #   this is likely 1/4 of the original rows for the scan/sampler
        return mean_tsys

    def _average_coordinates(self):
        """Get exposure-weighted average coordinates

        Keyword arguments:
        sampler -- the sampler number
        
        NB: not used yet
        """
        
        calmask = self.attr['calmask']
        elevation = self.attr['elevation']
        azimuth = self.attr['azimuth']
        longitude_axis = self.attr['longitude_axis']
        latitude_axis = self.attr['latitude_axis']
        target_longitude = self.attr['target_longitude']
        target_latitude = self.attr['target_latitude']

        tSum = exposure.sum()
        if self.noise_diode:
            exposure = self.attr['exposure'][calmask]
            el = (exposure * elevation[calmask]).sum() / tSum
            az = (exposure * azimuth[calmask]).sum() / tSum
            lon = (exposure * longitude_axis[calmask]).sum() / tSum
            lat = (exposure * latitude_axis[calmask]).sum() / tSum
            tLon = (exposure * target_longitude[calmask]).sum() / tSum
            tLat = (exposure * target_latitude[calmask]).sum() / tSum
        else:
            exposure = self.attr['exposure']
            el = (exposure * elevation).sum() / tSum
            az = (exposure * azimuth).sum() / tSum
            lon = (exposure * longitude_axis).sum() / tSum
            lat = (exposure * latitude_axis).sum() / tSum
            tLon = (exposure * target_longitude).sum() / tSum
            tLat = (exposure * target_latitude).sum() / tSum

    def no_calibration(self,verbose):
        """

        Keyword arguments:
        verbose -- verbosity level, default to 0
        
        Returns:
        Raw CALON spectra, no calibration
        """
        
        input_rows = self.attr['row']
        
        if self.noise_diode:
            calmask = self.attr['calmask']
            return input_rows[calmask]
        else:
            return input_rows

    def centerfreq(self,state):
        
        # apply sampler filter
        data = self.data[state]
        calmask = self.attr['calmask'][state]
        #crpix1 = self.attr['crpix1'][state][calmask]
        crval1 = self.attr['crval1'][state][calmask]
        #cdelt1 = self.attr['cdelt1'][state][calmask]
        
        return crval1

    def freqdelta(self,state):
        
        # apply sampler filter
        data = self.data[state]
        calmask = self.attr['calmask'][state]
        #crpix1 = self.attr['crpix1'][state][calmask]
        #crval1 = self.attr['crval1'][state][calmask]
        cdelt1 = self.attr['cdelt1'][state][calmask]
        
        return cdelt1

    def calibrate_fs(self, logger, opacity_coefficients, gain_coeff, spillover,\
                     aperture_eff, mainbeam_eff, units, gain_factor, verbose):
        
        # split the data into to states
        # SIG is element [0] and REF is element [1]
        self.split_fs_states()

        # smooth the reference spectra using a median filter of this size
        WINDOW = 16
        
        # --------------------------------- calibrate to Ta for the first state
        
        # identify which spectra are signal and which are reference
        sig_state = 0
        ref_state = 1
        
        # get signal spectra
        sig = self.calonoff_ave(state=sig_state)
        
        # get reference spectra
        ref = self.calonoff_ave(state=ref_state)
        
        # smooth reference spectra
        for idx,spectrum in enumerate(ref):
            ref[idx] = smoothing.median(spectrum,WINDOW)

        # compute the reference tsys values
        tsys = self.tsys(state=ref_state)
        
        # calculate Ta for first SIG/REF set
        ta0 = np.ones(sig.shape)
        for idx,ee in enumerate(tsys):
            ta0[idx] = tsys[idx] * ((sig[idx]-ref[idx])/ref[idx])

        # ------------------------------ calibrate to Ta for the second state
        
        # identify which spectra are signal and which are reference
        sig_state = 1
        ref_state = 0

        # get signal spectra
        sig = self.calonoff_ave(state=sig_state)

        # get reference spectra
        ref = self.calonoff_ave(state=ref_state)

        # smooth reference spectra
        for idx,spectrum in enumerate(ref):
            ref[idx] = smoothing.median(spectrum,WINDOW)

        # compute the reference tsys values
        tsys = self.tsys(state=ref_state)

        ta1 = np.ones(sig.shape)
        for idx,ee in enumerate(tsys):
            ta1[idx] = tsys[idx] * ((sig[idx]-ref[idx])/ref[idx])

        # --------------------------------- shift spectra to match in frequency

        sig_state = 0
        ref_state = 1

        sig_centerfreq = self.centerfreq(state=sig_state)
        ref_centerfreq = self.centerfreq(state=ref_state)
        sig_delta = self.freqdelta(state=sig_state)
        channel_shift = ((sig_centerfreq-ref_centerfreq)/sig_delta).mean()

        # do integer channel shift to second spectrum
        ta1 = np.roll(ta1,int(channel_shift),axis=1)
        if channel_shift > 0:
            ta1[:,:channel_shift]=0
        elif channel_shift < 0:
            ta1[:,channel_shift:]=0

        # average shifted spectra
        Ta = (ta0+ta1)/2.
        Units = Ta
        calmask = self.attr['calmask'][sig_state]

        # apply a relative gain factor, if not 1
        # this is the same as fbeampol in eqn. 13 of the PS document
        if float(1) != gain_factor:
            Units = Units * gain_factor
        
        if units=='ta*' or units=='tmb' or units=='tb*' or units=='jy':
            # calculate correction to ta* for each frequency, time and elevation
            if (sig_centerfreq.mean()/1e9 <=50 or 70<= sig_centerfreq.mean()/1e9 <=116):
                sigstate = 0
                calmask = self.attr['calmask'][sigstate]
                elevations = self.attr['elevation'][sigstate][calmask]
                dates = self.attr['date'][sigstate][calmask]
                mjds = np.array([ pipeutils.dateToMjd(xx) for xx in dates ])
                freqs = self.freq_axis(sigstate)
                # get first and last frequency of each frequency axis
                hiandlofreqs = freqs[:,[0,-1]]
                ta_correction = pipeutils.ta_correction(gain_coeff,spillover,\
                            opacity_coefficients,mjds,elevations,hiandlofreqs/1e9)
            else:
                ta_correction = False
            
            # compute sky temperatures (tsky) at ends of bands and interpolate
            #   in between the low and high frequency channels
            if np.any(ta_correction):
                all_ta_correction = np.zeros(sig.shape)
                dOpacity = (ta_correction[:,1]-ta_correction[:,0])/float(sig.shape[1])
                for idx in range(sig.shape[1]):
                    all_ta_correction[:,idx] = ta_correction[:,0]+(idx*dOpacity)
                ta_correction = all_ta_correction
                temps = self.attr['tambient'][sigstate][calmask]
                ambient_temp = temps.mean()

                # get sky temperature contribution to signal
                tsky_sig = np.array([pipeutils.tsky(ambient_temp,hiandlofreqs[idx],opacity)\
                                    for idx,opacity in enumerate(ta_correction)])
                allfreq = self.freq_axis_mean()
                
                # tsky interpolation over frequency band (idl-like)
                all_tsky_sig = np.zeros(sig.shape)
                dT = (tsky_sig[:,1]-tsky_sig[:,0])/float(sig.shape[1])
                for idx in range(sig.shape[1]):
                    all_tsky_sig[:,idx] = tsky_sig[:,0]+(idx*dT)
                
                doMessage(self.logger,msg.DBG,'TSKY SIG (interpolated):',\
                        all_tsky_sig[0][0],'to',all_tsky_sig[0][-1],\
                        'for first integration')
                        
                Ta_adjusted = Units * ta_correction
                Units = Ta_adjusted

            else:
                if not units=='ta':
                    doMessage(self.logger,msg.WARN,'WARNING: Opacities not available, calibrating to units of Ta')
                    units = 'ta'

        if units=='tmb' or units=='tb*':
            # PS specification section 4.11
            midfreq = sig_centerfreq.mean()
            etaMB = pipeutils.eta(mainbeam_eff,midfreq) # idl-like version
            doMessage(logger,msg.DBG,"main beam efficiency",etaMB)
            Tmb = Ta_adjusted / etaMB
            Units = Tmb

        if units=='jy':
            # PS specification section 4.12
            midfreq = sig_centerfreq.mean()
            etaA = pipeutils.eta(aperture_eff,midfreq)
            doMessage(logger,msg.DBG,"aperture efficiency",etaA)
            Jy = Ta_adjusted / (2.85 * etaA)
            Units = Jy

        if not (units=='ta' or units=='tatsky' or units=='ta*' or units=='tmb'\
                or units=='tb*' or units=='jy'):
            doMessage(self.logger,msg.WARN,'Unable to calibrate to units of',units)
            doMessage(self.logger,msg.WARN,'  calibrated to Ta')

        # set the calibrated data into the output structure
        input_rows = self.attr['row'][sig_state][calmask]
        for idx,row in enumerate(input_rows):
            row.setfield('DATA',Units[idx])
            row.setfield('TSYS',tsys[idx].mean())

        return input_rows
    
    def calibrate_to(self,logger,refs,ref_dates,ref_tsyss,\
        k_per_count,opacity_coefficients,gain_coeff,spillover,aperture_eff,\
        mainbeam_eff,ref_tskys,units,gain_factor,verbose):
        """

        Keyword arguments:
        sampler -- the sampler number
        mean_tsys -- 
        refspec -- reference spectrum
        k_per_count -- kelvin per count scaling factor
        verbose -- verbosity level, default to 0
        
        Returns:
        Spectra, calibrated to antenna temperature.
        """
        onlystate = 0
        
        crpix1 = self.attr['crpix1'][onlystate]
        cdelt1 = self.attr['cdelt1'][onlystate]
        crval1 = self.attr['crval1'][onlystate]
        
        input_rows = self.attr['row'][onlystate]
        data = self.data
        tcal = self.attr['tcal'][onlystate]
        dates = self.attr['date'][onlystate]
        elevations = self.attr['elevation'][onlystate]
        temps = self.attr['tambient'][onlystate]
        ambient_temp = temps.mean()
        
        # average signal CALON and CALOFF
        if self.noise_diode:
            calmask = self.attr['calmask'][onlystate]
            input_rows = input_rows[calmask]
            sig = (data[onlystate][calmask] + data[onlystate][~calmask]) / 2.
            elevations = elevations[calmask]
            crpix1 = crpix1[calmask]
            crval1 = crval1[calmask]
            cdelt1 = cdelt1[calmask]
            mjds = np.array([ pipeutils.dateToMjd(xx) for xx in dates[calmask] ])
        else:
            sig = data[onlystate]
            mjds = np.array([ pipeutils.dateToMjd(xx) for xx in dates ])

        # create an array of low and high frequencies for each integration
        #glen's version
        refChan = crpix1-1
        observed_frequency = crval1
        nchan = np.zeros(len(sig))
        for idx,ee in enumerate(nchan):
            nchan[idx] = len(sig[idx])
        delChan = cdelt1
        freq_los = observed_frequency + (0-refChan)*delChan
        freq_his = observed_frequency + (nchan-refChan)*delChan
        freq = np.array([freq_los,freq_his])
        freq = freq.transpose()
        
        # calculate correction to ta* for each frequency, time and elevation
        if not units=='ta' and \
          (freq.mean()/1e9 <=50 or 70<= freq.mean()/1e9 <=116):
            ta_correction = pipeutils.ta_correction(gain_coeff,spillover,\
                        opacity_coefficients,mjds,elevations,freq/1e9)
        else:
            ta_correction = False

        # compute sky temperatures (tsky) at ends of bands and interpolate
        #   in between the low and high frequency channels
        if np.any(ta_correction):
            all_ta_correction = np.zeros(sig.shape)
            dOpacity = (ta_correction[:,1]-ta_correction[:,0])/float(sig.shape[1])
            for idx in range(sig.shape[1]):
                all_ta_correction[:,idx] = ta_correction[:,0]+(idx*dOpacity)
            
            # get sky temperature contribution to signal
            tsky_sig = np.array([pipeutils.tsky(ambient_temp,freq[idx],opacity)\
                                for idx,opacity in enumerate(ta_correction)])
            allfreq = self.freq_axis_mean()
            
            # tsky interpolation over frequency band (idl-like)
            all_tsky_sig = np.zeros(sig.shape)
            dT = (tsky_sig[:,1]-tsky_sig[:,0])/float(sig.shape[1])
            for idx in range(sig.shape[1]):
                all_tsky_sig[:,idx] = tsky_sig[:,0]+(idx*dT)
            
            doMessage(self.logger,msg.DBG,'TSKY SIG (interpolated):',\
                      all_tsky_sig[0][0],'to',all_tsky_sig[0][-1],\
                      'for first integration')
        else:
            if not units=='ta':
                doMessage(self.logger,msg.WARN,'WARNING: Opacities not available, calibrating to units of Ta')
                units = 'ta'
        
        # interpolate (by time) the reference spectrum and tskys
        if ( len(refs)>1 and \
             len(ref_dates)>1 and \
             len(ref_tskys)>1 ):
            ref,tsky_ref,tsys_ref = pipeutils.interpolate_reference(refs,ref_dates,ref_tskys,ref_tsyss, mjds)
        else:
            ref = np.array(refs[0],ndmin=2)
            tsky_ref = np.array(ref_tskys[0],ndmin=2)
            tsys_ref = np.array(ref_tsyss[0],ndmin=2)

        # PS specification (eqn. 5)
        Ta = tsys_ref * ((sig-ref)/ref)
        Units = Ta

        doMessage(self.logger,msg.DBG,'freqs',freq[0],'to',freq[-1])
        if np.any(ta_correction):
            doMessage(self.logger,msg.DBG,'ta_correction',ta_correction.shape,ta_correction[0].mean())
            doMessage(self.logger,msg.DBG,'TSKY REF',tsky_ref[0][0],'to',tsky_ref[0][-1])
            doMessage(self.logger,msg.DBG,'Shapes Ta,all_tsky_sig,tsky_ref',Ta.shape,all_tsky_sig.shape,tsky_ref.shape)
        doMessage(self.logger,msg.DBG,'refs',ref.shape)
        doMessage(self.logger,msg.DBG,'tsys (mean)',tsys_ref.mean())
        doMessage(self.logger,msg.DBG,tsys_ref.mean(),sig.shape,ref.shape)
        doMessage(self.logger,msg.DBG,'1st int SIG aves[0],[1000],[nChan]',sig[0][0],sig[0][1000],sig[0][-1])
        if len(refs) > 1:
            doMessage(self.logger,msg.DBG,'B-REF [0],[1000],[nChan]',refs[0][0],refs[0][1000],refs[0][-1])
            doMessage(self.logger,msg.DBG,'E-REF [0],[1000],[nChan]',refs[1][0],refs[1][1000],refs[1][-1])
            doMessage(self.logger,msg.DBG,'1st int REF [0],[1000],[nChan]',ref[0][0],ref[0][1000],ref[0][-1])
        doMessage(self.logger,msg.DBG,'1st int SIG [0],[1000],[nChan]',sig[0][0],sig[0][1000],sig[0][-1])

        if not np.any(ta_correction) and not units=='ta':
            doMessage(self.logger,msg.WARN,'WARNING: No opacities, calibrating to units of Ta')
            units=='ta'

        # apply a relative gain factor, if not 1
        # this is the same as fbeampol in eqn. 13 of the PS document
        if float(1) != gain_factor:
            Ta = Ta * gain_factor

        if units=='tatsky' or units=='ta*' or units=='tmb' or \
           units=='tb*' or units=='jy':
            # remove the elevation contribution to sky temperatures
            if np.any(all_tsky_sig) and np.any(tsky_ref):
                Ta = Ta - (all_tsky_sig - tsky_ref)
                Units = Ta

        if units=='ta*' or units=='tmb' or units=='tb*' or units=='jy':
            # Braatz 2007 (eqn. 3), modified with denominator == 1
            Ta_adjusted = Ta * all_ta_correction
            Units = Ta_adjusted
        
        if units=='tmb' or units=='tb*':
            # calculate main beam efficiency approx. = 1.37 * etaA
            #   where etaA is aperture efficiency
            # note to self: move to the top level so as to only call once?

            #etaMB = np.array([pipeutils.etaMB(ff) for ff in freq]) # all frequencies
            allfreq = self.freq_axis_mean()
            midfreq = allfreq[len(allfreq)/2] #reference freq of first integration
            etaMB = pipeutils.eta(mainbeam_eff,midfreq) # idl-like version
            doMessage(logger,msg.DBG,"main beam efficiency",etaMB)
            
            # PS specification section 4.11
            Tmb = Ta_adjusted / etaMB
            Units = Tmb
        
        if units=='jy':
            allfreq = self.freq_axis_mean()
            midfreq = allfreq[len(allfreq)/2] #reference freq of first integration
            etaA = pipeutils.eta(aperture_eff,midfreq)
            doMessage(logger,msg.DBG,"aperture efficiency",etaA)
            Jy = Ta_adjusted / (2.85 * etaA)
            Units = Jy
            
        if not (units=='ta' or units=='tatsky' or units=='ta*' or units=='tmb'\
                or units=='tb*' or units=='jy'):
            doMessage(self.logger,msg.WARN,'Unable to calibrate to units of',units)
            doMessage(self.logger,msg.WARN,'  calibrated to Ta')

        # compute system temperature for each integration
        #   using the scaling factor (Tcal/(calON-calOFF))
        #   from the reference scan(s)
        #   [using the center 80% of the band]
        chanlo = int(len(data[onlystate][0])*.1)
        chanhi = int(len(data[onlystate][0])*.9)
        tsys = k_per_count * sig
        tsys = tsys[:,chanlo:chanhi].mean(1)

        for idx,row in enumerate(input_rows):
            row.setfield('DATA',Units[idx])
            row.setfield('TSYS',tsys[idx])

        return input_rows

    def average_reference(self,logger,units,gain_coeff,spillover,\
            opacity_coefficients,verbose):
        """

        Keyword arguments:
        sampler -- the sampler number
        verbose -- verbosity level, default to 0
        
        Returns:
        spectrum -- single spectrum average of CALON and CALOFF spectra
        max_tcal -- mean tcal for reference spectra
        mean_tsys -- mean system temperature for reference spectra
        freq -- the frequency axis, to be used for plotting
        """
        
        onlystate = 0

        crpix1 = self.attr['crpix1'][onlystate].mean()
        cdelt1 = self.attr['cdelt1'][onlystate].mean()
        crval1 = self.attr['crval1'][onlystate].mean()
        data = self.data
        
        max_tcal = self.max_tcal()
        mean_tsys = self.average_tsys(verbose=verbose)
        
        spectrum = self.calonoffave_ave()
        date = self.min_date()

        elevations = self.attr['elevation'][onlystate]
        exposure = self.attr['exposure'][onlystate]

        dates = self.attr['date'][onlystate]
        calmask = self.attr['calmask'][onlystate]
        
        # idl-like version of frequency interpolation across band
        refChan = crpix1-1
        observed_frequency = crval1
        nchan = len(data[onlystate][0])
        delChan = cdelt1
        freq_lo = observed_frequency + (0-refChan)*delChan
        freq_hi = observed_frequency + (nchan-refChan)*delChan
        freq = np.array([freq_lo,freq_hi])

        if self.noise_diode:
            mjds = np.array([ pipeutils.dateToMjd(xx) for xx in dates[calmask] ])
            elevations = elevations[calmask]
            exposure = exposure[calmask]
        else:
            mjds = np.array([ pipeutils.dateToMjd(xx) for xx in dates ])
            
        temps = self.attr['tambient'][onlystate]
        ambient_temp = temps.mean()

        # idl-like version uses a single avg elevation
        if not units=='ta' and (6<= freq.mean()/1e9 <=50 or 70<= freq.mean()/1e9 <=116):
            ta_correction = pipeutils.ta_correction(gain_coeff,spillover,\
                        opacity_coefficients,\
                        [mjds.mean()],[self.elevation_ave()],freq/1e9,verbose)
        else:
            ta_correction = False
            
        allfreq = self.freq_axis_mean()
        
        if np.any(ta_correction):
            tskys = pipeutils.tsky(ambient_temp,freq,ta_correction)
            all_tskys = pipeutils.interpolate(allfreq,freq,tskys)
            tskys = all_tskys
        else:
            tskys = False
        
        return spectrum,max_tcal,date,allfreq,tskys,mean_tsys

    def split_fs_states(self):

        statemask = self.statemask

        for xx in self.attr:
            self.attr[xx]= np.array([self.attr[xx][0][statemask],self.attr[xx][0][~statemask]])
        
        # split into two states for frequency swithced mode
        states = []
        states.append(self.data[0][statemask])
        states.append(self.data[0][~statemask])
        self.data = np.array(states)
