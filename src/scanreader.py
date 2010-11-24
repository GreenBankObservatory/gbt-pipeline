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

            self.frequency_resolution = row['FREQRES']

            # count number of feeds and cal states
            self.feeds.add(row['FEED'])
            self.cals.add(row['CAL'])

        # convert attr lists to numpy arrays
        for xx in self.attr: self.attr[xx]=np.array(self.attr[xx])

        # change data into a masked array to remove effect of nans
        self.data = np.ma.masked_array(self.data,np.isnan(self.data))

        # set a flag if the noise diode is firing
        if len(self.cals)==2:
            self.noise_diode = True
        else:
            self.noise_diode = False
            
        doMessage(self.logger,msg.DBG,'feeds',len(self.feeds))
        doMessage(self.logger,msg.DBG,'n_polarizations',len(set(self.attr['polarization'])))
        doMessage(self.logger,msg.DBG,'n_cals',len(self.cals))
        doMessage(self.logger,msg.DBG,'n_channels',len(self.data[0]))

        doMessage(self.logger,msg.DBG,'nrecords',len(self.data))
        doMessage(self.logger,msg.DBG,'frequency_resolution',self.frequency_resolution,'Hz')

    def calonoff_ave(self):
        """Get average of Cal-on spectra and Cal-off

        Keyword arguments:
        
        Returns:
        The mean of the CAL ON and CAL OFF spectra.  The vector size is
        the same as the number of channels in each input spectrum.
        """
        
        return (self.calon_ave()+self.caloff_ave())/2.

    def calonoff_diff(self):
        """Get CalON minus CalOFF

        Keyword arguments:
        
        Returns:
        The CAL (ON-OFF).  The vector size is
        the same as the number of channels in each input spectrum.
        """
        
        return self.calon_ave() - self.caloff_ave()

    def calon_ave(self):
        """Get the exposure-weighted average of Cal-on spectra for given

        Keyword arguments:

        Returns:
        The exposure-weighted mean of the CALON spectra.  The vector size is
        the same as the number of channels in each input spectrum.
        """
        
        data = self.data
        exposure = self.attr['exposure']
        calmask = self.attr['calmask']

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

    def caloff_ave(self):
        """Get the exposure-weighted average of Cal-off spectra

        Keyword arguments:
        
        Returns:
        A exposure-weighted mean of the CALOFF spectra.  The vector size is
        the same as the number of channels in each input spectrum.
        """
        
        data = self.data
        exposure = self.attr['exposure']
        calmask = self.attr['calmask']
        
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
        
    def freq_axis(self,verbose=0):
        """ frequency axis to return for plotting

        Keyword arguments:
        sampler -- the sampler number
        verbose -- verbosity level, default to 0
        
        Returns:
        A mean frequency axis for the scan.
        """
        
        # apply sampler filter
        data = self.data
        crpix1 = self.attr['crpix1'].mean()
        cdelt1 = self.attr['cdelt1'].mean()
        crval1 = self.attr['crval1'].mean()

        faxis = np.zeros(len(data[0]))
        for idx,e in enumerate(data[0]):
            faxis[idx] = ((idx-crpix1)*cdelt1+crval1)

        return faxis

    def average_tsys(self,verbose=0):
        """Get the total power for a single scan (i.e. feed,pol,IF)

        Keyword arguments:
        verbose -- verbosity level, default to 0
        
        Returns:
        An averaged, weighted sytem temperature, using the center 80% of
        the band.
        """

        # apply sampler filter
        data = self.data
        exposure = self.attr['exposure']
        tcal = self.attr['tcal']

        chanlo = int(len(data)*.1)
        chanhi = int(len(data)*.9)

        ref = self.calonoff_ave()
        cal = self.calonoff_diff()

        ratios = ref[chanlo:chanhi] / cal[chanlo:chanhi]
        mytsys = ratios.mean() * self.max_tcal()

        Tsys = mytsys
        doMessage(self.logger,msg.DBG,'Tsys', Tsys)
        doMessage(self.logger,msg.DBG,'Tcal', tcal.mean())

        return Tsys

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
        sampler -- the sampler number
        mean_tsys -- 
        refspec -- reference spectrum
        k_per_count -- kelvin per count scaling factor
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

    def calibrate_to(self,refs,ref_dates,ref_tsyss,\
        k_per_count,opacity_coefficients,gain_coeff,spillover,aperture_eff,\
        fbeampol,ref_tskys,units,gain_factor,verbose):
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
        crpix1 = self.attr['crpix1']
        cdelt1 = self.attr['cdelt1']
        crval1 = self.attr['crval1']
        
        input_rows = self.attr['row']
        data = self.data
        tcal = self.attr['tcal']
        dates = self.attr['date']
        elevations = self.attr['elevation']
        temps = self.attr['tambient']
        ambient_temp = temps.mean()
        
        # average signal CALON and CALOFF
        if self.noise_diode:
            calmask = self.attr['calmask']
            input_rows = input_rows[calmask]
            sig_counts = (data[calmask] + data[~calmask]) / 2.
            elevations = elevations[calmask]
            crpix1 = crpix1[calmask]
            crval1 = crval1[calmask]
            cdelt1 = cdelt1[calmask]
            mjds = np.array([ pipeutils.dateToMjd(xx) for xx in dates[calmask] ])
        else:
            sig_counts = data
            mjds = np.array([ pipeutils.dateToMjd(xx) for xx in dates ])

        #freq = self.freq_axis(verbose)

        #glen's version
        refChan = crpix1-1
        observed_frequency = crval1
        nchan = np.zeros(len(sig_counts))
        for idx,ee in enumerate(nchan):
            nchan[idx] = len(sig_counts[idx])
        delChan = cdelt1
        freq_los = observed_frequency + (0-refChan)*delChan
        freq_his = observed_frequency + (nchan-refChan)*delChan
        freq = np.array([freq_los,freq_his])
        freq = freq.transpose()
        
        # calculate weather-dependent opacities for each frequency, time and elevation
        if not units=='ta' and (6<= freq.mean()/1e9 <=50 or 70<= freq.mean()/1e9 <=116):
            opacities = pipeutils.ta_correction(gain_coeff,spillover,aperture_eff,\
                        fbeampol,opacity_coefficients,mjds,elevations,freq/1e9)
        else:
            opacities = False
            
        if np.any(opacities):
            all_opacities = np.zeros(sig_counts.shape)
            dOpacity = (opacities[:,1]-opacities[:,0])/float(sig_counts.shape[1])
            for idx in range(sig_counts.shape[1]):
                all_opacities[:,idx] = opacities[:,0]+(idx*dOpacity)
            
            # get sky temperature contribution to signal
            tsky_sig = np.array([pipeutils.tsky(ambient_temp,freq[idx],opacity) for idx,opacity in enumerate(opacities)])
            allfreq = self.freq_axis()
            
            # tsky interpolation over frequency band (idl-like)
            all_tsky_sig = np.zeros(sig_counts.shape)
            dT = (tsky_sig[:,1]-tsky_sig[:,0])/float(sig_counts.shape[1])
            for idx in range(sig_counts.shape[1]):
                all_tsky_sig[:,idx] = tsky_sig[:,0]+(idx*dT)
            
            doMessage(self.logger,msg.DBG,'TSKY SIG (interpolated)',all_tsky_sig[0][0],'to',all_tsky_sig[0][-1],'for first integration')
        else:
            if not units=='ta':
                doMessage(self.logger,msg.WARN,'WARNING: Opacities not available, calibrating to units of Ta')
                units = 'ta'
        
        # interpolate (by time) reference spectrum and tskys
        if ( len(refs)>1 and \
             len(ref_dates)>1 and \
             len(ref_tskys)>1 ):
            ref,tsky_ref,tsys_ref = pipeutils.interpolate_reference(refs,ref_dates,ref_tskys,ref_tsyss, mjds)
        else:
            ref = np.array(refs[0],ndmin=2)
            tsky_ref = np.array(ref_tskys[0],ndmin=2)
            tsys_ref = np.array(ref_tsyss[0],ndmin=2)

        # Braatz 2007 eqn. (2)
        Ta = tsys_ref * ((sig_counts-ref)/ref)
        Units = Ta

        doMessage(self.logger,msg.DBG,'freqs',freq[0],'to',freq[-1])
        if np.any(opacities):
            doMessage(self.logger,msg.DBG,'opacities',opacities.shape,opacities[0].mean())
            doMessage(self.logger,msg.DBG,'TSKY REF',tsky_ref[0][0],'to',tsky_ref[0][-1])
            doMessage(self.logger,msg.DBG,'Shapes Ta,all_tsky_sig,tsky_ref',Ta.shape,all_tsky_sig.shape,tsky_ref.shape)
        doMessage(self.logger,msg.DBG,'refs',ref.shape)
        doMessage(self.logger,msg.DBG,'tsys (mean)',tsys_ref.mean())
        doMessage(self.logger,msg.DBG,tsys_ref.mean(),sig_counts.shape,ref.shape)
        doMessage(self.logger,msg.DBG,'1st int SIG aves[0],[1000],[nChan]',sig_counts[0][0],sig_counts[0][1000],sig_counts[0][-1])
        if len(refs) > 1:
            doMessage(self.logger,msg.DBG,'B-REF [0],[1000],[nChan]',refs[0][0],refs[0][1000],refs[0][-1])
            doMessage(self.logger,msg.DBG,'E-REF [0],[1000],[nChan]',refs[1][0],refs[1][1000],refs[1][-1])
            doMessage(self.logger,msg.DBG,'1st int REF [0],[1000],[nChan]',ref[0][0],ref[0][1000],ref[0][-1])
        doMessage(self.logger,msg.DBG,'1st int SIG [0],[1000],[nChan]',sig_counts[0][0],sig_counts[0][1000],sig_counts[0][-1])
            
        if not np.any(opacities) and not units=='ta':
            doMessage(self.logger,msg.WARN,'WARNING: No opacities, calibrating to units of Ta')
            units=='ta'
            
        if units=='tatsky':
            # remove the elevation contribution to sky temperatures
            if np.any(all_tsky_sig) and np.any(tsky_ref):
                Ta = Ta - (all_tsky_sig - tsky_ref)
                Units = Ta
            
        if units=='ta*' or units=='tmb' or units=='tb*' or units=='jy':
            # Braatz 2007 (eqn. 3), modified with denominator == 1
            Ta_adjusted = Ta * all_opacities
            Units = Ta_adjusted
        
        if units=='tmb' or units=='tb*':
            # calculate main beam efficiency approx. = 1.32 * etaA
            #   where etaA is aperture efficiency
            # note to self: move to the top level so as to only call once?

            #etaMB = np.array([pipeutils.etaMB(ff) for ff in freq]) # all frequencies
            allfreq = self.freq_axis()
            midfreq = allfreq[len(allfreq)/2] #reference freq of first integration
            etaMB = pipeutils.etaMB(midfreq) # idl-like version

            # Braatz 2007 ("Calibration to Tmb and other units")
            Tmb = Ta_adjusted / etaMB
            Units = Tmb
        
        if units=='jy':
            allfreq = self.freq_axis()
            midfreq = allfreq[len(allfreq)/2] #reference freq of first integration
            etaA = pipeutils.etaA(midfreq)
            Jy = Ta_adjusted / (2.85 * etaA)
            Units = Jy
            
        if not (units=='ta' or units=='tatsky' or units=='ta*' or units=='tmb' or units=='tb*' or units=='jy'):
            doMessage(self.logger,msg.WARN,'Unable to calibrate to units of',units)
            doMessage(self.logger,msg.WARN,'  calibrated to Ta')

        # compute system temperature for each integration
        #   using the scaling factor (Tcal/(calON-calOFF))
        #   from the reference scan(s)
        #   [using the center 80% of the band]
        chanlo = int(len(data[0])*.1)
        chanhi = int(len(data[0])*.9)
        tsys = k_per_count * sig_counts
        tsys = tsys[:,chanlo:chanhi].mean(1)

        # apply a relative gain factor, if not 1
        if float(1) != gain_factor:
            Units = Units * gain_factor

        for idx,row in enumerate(input_rows):
            row.setfield('DATA',Units[idx])
            row.setfield('TSYS',tsys[idx])

        return input_rows

    def average_reference(self,units,gain_coeff,spillover,aperture_eff,\
            fbeampol,opacity_coefficients,verbose):
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
        
        crpix1 = self.attr['crpix1'].mean()
        cdelt1 = self.attr['cdelt1'].mean()
        crval1 = self.attr['crval1'].mean()
        data = self.data
        
        max_tcal = self.max_tcal()
        mean_tsys = self.average_tsys(verbose)
        
        spectrum = self.calonoff_ave()
        date = self.min_date()

        elevations = self.attr['elevation']
        exposure = self.attr['exposure']

        dates = self.attr['date']
        calmask = self.attr['calmask']
        
        # idl-like version of frequency interpolation across band
        refChan = crpix1-1
        observed_frequency = crval1
        nchan = len(data[0])
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
            
        temps = self.attr['tambient']
        ambient_temp = temps.mean()

        # idl-like version uses a single avg elevation
        if not units=='ta' and (6<= freq.mean()/1e9 <=50 or 70<= freq.mean()/1e9 <=116):
            opacities = pipeutils.ta_correction(gain_coeff,spillover,aperture_eff,\
                        fbeampol,opacity_coefficients,\
                        [mjds.mean()],[self.elevation_ave()],freq/1e9,verbose)
        else:
            opacities = False
            
        allfreq = self.freq_axis()
        
        if np.any(opacities):
            tskys = pipeutils.tsky(ambient_temp,freq,opacities)
            all_tskys = pipeutils.interpolate(allfreq,freq,tskys)
            tskys = all_tskys
        else:
            tskys = False
        
        return spectrum,max_tcal,date,allfreq,tskys,mean_tsys
