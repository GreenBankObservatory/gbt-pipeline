import pylab
import smoothing
import pipeutils

import numpy as np
import math
import sys

class ScanReader:
    """The primary class for reading sdfits input.

    In addition to reading all required information from the sdfits
    input, ScanReader will perform basic averaging, and calibration
    (always for a single scan and usually for a single sampler).
    """
    
    def __init__(self):
        self.attr = {}
        self.attr['date'] = []
        self.attr['polarization'] = []
        self.attr['samplers'] = []
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

        self.sampler_map = {}

        self.ifs=set([])

        self.frequency_resolution = 0
        self.noise_diode = False

    def map_name_vals(self,scan_number,fdata,startidx,verbose):
        """Collect information for naming the output file

        Required information comes from the column values in the sdfits
        input file.  It is only necessary to read a single row, so we
        return after finding the first integration.
        
        Keyword arguments:
        scan_number -- the GBTIDL-generated index file, for the
        fdata -- sdfits input table pointer
        startidx -- row index to start search
        verbose -- verbosity level
        
        Returns:
        obj -- the "OBJECT" col. val. in the sdfits input
        centerfreq -- the freqency at the center channel
        feed -- the feed number from "FEED" col. in the sdfits input
        """
        
        # read ROWSIZE rows at a time
        # a rowsize of 30,000 was chosen because a spectrum of 4096 channels
        # is approximately 32 kb with 64-bit float values for each channel,
        # so 30,000*8,000b = 240,000,000 or 240 Mb, which will usually be
        # available
        ROWSIZE = 30000

        if verbose > 3: print 'starting search from index',startidx
        if len(fdata)-startidx < ROWSIZE:
            lcldata = fdata[startidx:]
        else:
            endidx = startidx + ROWSIZE
            if verbose > 3: print 'and stopping at index',endidx
            lcldata = fdata[startidx:endidx]

        for idx,row in enumerate(lcldata):
            if row['SCAN']==scan_number:
                obj = row['OBJECT']
                feed = row['FEED']
                centerfreq = row['CRVAL1']
                break

        return obj,centerfreq,feed

    def scan_samplers(self,scan_number,fdata,startidx,verbose):
        """Collect all samplers used in a given scan.

        Keyword arguments:
        scan_number -- the GBTIDL-generated index file, for the
        fdata -- sdfits input table pointer
        startidx -- row index to start search
        verbose -- verbosity level
        
        Returns:
        last row index read
        """

        finished_consecutive_rows_for_this_scan = False
        found_sampler = False
        
        samplers = set([])
        
        # read ROWSIZE rows at a time
        ROWSIZE = 30000
        # a rowsize of 30,000 was chosen because a spectrum of 4096 channels
        # is approximately 32 kb with 64-bit float values for each channel,
        # so 30,000*8,000b = 240,000,000 or 240 Mb, which will usually be
        # available

        if len(fdata)-startidx < ROWSIZE:
            lcldata = fdata[startidx:]
            if verbose > 3: print 'searching to the end!'
        else:
            endidx = startidx + ROWSIZE
            lcldata = fdata[startidx:endidx]
            if verbose > 3: print 'endidx',endidx
            
        #print 'starting from',startidx,'scan',lcldata[0]['SCAN']
        for idx,row in enumerate(lcldata):
            if row['SCAN']==scan_number:
                samplers.add(row['SAMPLER'])

            elif row['SCAN']>scan_number:
                # remember the last row read so we don't need to start at
                # the beginning when reading the next scan
                finished_consecutive_rows_for_this_scan = True
                break
                
        # if there could be more data for the scan
        if not finished_consecutive_rows_for_this_scan:
            
            # if we haven't reached the end of the file
            if (startidx+idx<len(fdata)-1):

                # haven't seen any rows with the scan number
                if not len(self.samplers):
                    # but more data ahead
                    if startidx+idx < len(fdata):
                        # so keep searching
                        return self.scan_samplers(scan_number,fdata,startidx+idx,verbose)
                        
                    else: # made it all the way to the end without seeing the scan
                        print 'No samplers found for scan',scan_number
                        sys.exit(9)
                        
                # have seen the scan, but there might be more data
                else:
                    if (verbose>3): print 'idx,startidx,tot',idx,startidx,idx+startidx
                    if not finished_consecutive_rows_for_this_scan and startidx+idx < len(fdata):
                        if (verbose>3): print 'have some data and looking for more from idx',startidx+idx
                        if (verbose>3): print startidx+idx,'of',len(fdata)
                        return self.scan_samplers(scan_number,fdata,startidx+idx,verbose)
                        
        return samplers

    def get_scan(self,sampler,scan_number,fdata,startidx,verbose):
        """Collect all primary needed information for a given scan.

        Keyword arguments:
        scan_number -- the GBTIDL-generated index file, for the
        fdata -- sdfits input table pointer
        startidx -- row index to start search
        verbose -- verbosity level
        
        Returns:
        last row index read
        """

        finished_consecutive_rows_for_this_scan = False
        found_sampler = False
        
        # read ROWSIZE rows at a time
        ROWSIZE = 30000
        # a rowsize of 30,000 was chosen because a spectrum of 4096 channels
        # is approximately 32 kb with 64-bit float values for each channel,
        # so 30,000*8,000b = 240,000,000 or 240 Mb, which will usually be
        # available

        if len(fdata)-startidx < ROWSIZE:
            lcldata = fdata[startidx:]
            if verbose > 3: print 'searching to the end!'
        else:
            endidx = startidx + ROWSIZE
            lcldata = fdata[startidx:endidx]
            if verbose > 3: print 'endidx',endidx
            
        #print 'starting from',startidx,'scan',lcldata[0]['SCAN']
        for idx,row in enumerate(lcldata):
            if row['SCAN']==scan_number:
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
                self.attr['samplers'].append(row['SAMPLER'])
                self.attr['exposure'].append(row['EXPOSURE'])
                self.attr['tambient'].append(row['TAMBIENT'])

                # create mask for calONs and calOFFs
                if 'T'==row['CAL']:
                    self.attr['calmask'].append(True)
                else:
                    self.attr['calmask'].append(False)

                # map a sampler to feed,pol and if(crval1,crpix1,cdelt1)
                self.sampler_map[row['SAMPLER']]=(
                    row['FEED'],row['CRVAL4'],
                    (row['CRVAL1'],row['CRPIX1'],
                    row['CDELT1']))

                self.frequency_resolution = row['FREQRES']

                # count number of feeds and cal states
                self.feeds.add(row['FEED'])
                self.cals.add(row['CAL'])

            elif row['SCAN']>scan_number:
                # remember the last row read so we don't need to start at
                # the beginning when reading the next scan
                finished_consecutive_rows_for_this_scan = True
                break
                
        # if there could be more data for the scan
        if not finished_consecutive_rows_for_this_scan:
            
            # if we haven't reached the end of the file
            if (startidx+idx<len(fdata)-1):

                # haven't seen any rows with the scan number
                if not len(self.data):
                    # but more data ahead
                    if startidx+idx < len(fdata):
                        # so keep searching
                        return self.get_scan(sampler,scan_number,fdata,startidx+idx,verbose)
                        
                    else: # made it all the way to the end without seeing the scan
                        print 'No data found for scan',scan_number
                        sys.exit(9)
                        
                # have seen the scan, but there might be more data
                else:
                    if (verbose>3): print 'idx,startidx,tot',idx,startidx,idx+startidx
                    if not finished_consecutive_rows_for_this_scan and startidx+idx < len(fdata):
                        if (verbose>3): print 'have some data and looking for more from idx',startidx+idx
                        if (verbose>3): print startidx+idx,'of',len(fdata)
                        return self.get_scan(sampler,scan_number,fdata,startidx+idx,verbose)

        # make sure the sampler is present
        for ii,e in enumerate(self.sampler_map):
            if e==sampler:
                found_sampler = True
                break

        # if it isn't complain and quit
        if not found_sampler:
            if verbose > 0: print "ERROR: sampler",sampler,"not found in scan"

        # convert attr lists to numpy arrays
        for xx in self.attr: self.attr[xx]=np.array(self.attr[xx])

        # change data into a masked array to remove effect of nans
        self.data = np.ma.masked_array(self.data,np.isnan(self.data))

        # set a flag if the noise diode is firing
        if len(self.cals)==2:
            self.noise_diode = True
        else:
            self.noise_diode = False
            
        if verbose > 3:
            print 'feeds',len(self.feeds)
            print 'n_polarizations',len(set(self.attr['polarization']))
            print 'n_cals',len(self.cals)
            print 'n_channels',len(self.data[0])
            print 'n_samplers',len(self.sampler_map)

            # print all the sampler names
            print 'sampler (feed, pol, (IF))'
            for ii,e in enumerate(self.sampler_map):
                print e,self.sampler_map[e]

            # determine number of IFs
            for ii,e in enumerate(self.sampler_map):
                self.ifs.add(self.sampler_map[e][2])
            print 'n_ifs',len(self.ifs)

            # check to see if feed,pol,if maps to more than one sampler
            for Aidx,Ae in enumerate(self.sampler_map):
                for Bidx,Be in enumerate(self.sampler_map):
                    if not(Ae==Be) and \
                       self.sampler_map[Ae] == self.sampler_map[Be]:
                        print 'Sampler',Ae,'== sampler',Be
   
            print 'nrecords',len(self.data)
            print 'frequency_resolution',self.frequency_resolution,'Hz'

        return startidx+idx

    def calonoff_ave(self,sampler):
        """Get average of Cal-on spectra and Cal-off for given sampler

        Keyword arguments:
        sampler -- the sampler number
        
        Returns:
        The mean of the CAL ON and CAL OFF spectra.  The vector size is
        the same as the number of channels in each input spectrum.
        """
        
        return (self.calon_ave(sampler)+self.caloff_ave(sampler))/2.

    def calonoff_diff(self,sampler):
        """Get CalON minus CalOFF for given sampler

        Keyword arguments:
        sampler -- the sampler number
        
        Returns:
        The CAL (ON-OFF) for the sampler.  The vector size is
        the same as the number of channels in each input spectrum.
        """
        
        return self.calon_ave(sampler) - self.caloff_ave(sampler)

    def calon_ave(self,sampler):
        """Get the exposure-weighted average of Cal-on spectra for given sampler

        Keyword arguments:
        sampler -- the sampler number

        Returns:
        The exposure-weighted mean of the CALON spectra.  The vector size is
        the same as the number of channels in each input spectrum.
        """
        
        # apply sampler filter
        data = self.data[self.attr['samplers']==sampler]
        exposure = self.attr['exposure'][self.attr['samplers']==sampler]
        calmask = self.attr['calmask'][self.attr['samplers']==sampler]

        return np.ma.average(data[calmask],axis=0,weights=exposure[calmask])

    def elevation_ave(self,sampler):
        """Get an exposure-weighted average elevation for given sampler

        Keyword arguments:
        sampler -- the sampler number

        Returns:
        The exposure-weighted mean of elevation
        """
        
        # apply sampler filter
        elevation = self.attr['elevation'][self.attr['samplers']==sampler]
        exposure = self.attr['exposure'][self.attr['samplers']==sampler]
        calmask = self.attr['calmask'][self.attr['samplers']==sampler]

        return np.ma.average(elevation[calmask],axis=0,weights=exposure[calmask])

    def caloff_ave(self,sampler):
        """Get the exposure-weighted average of Cal-off spectra for given sampler

        Keyword arguments:
        sampler -- the sampler number
        
        Returns:
        A exposure-weighted mean of the CALOFF spectra.  The vector size is
        the same as the number of channels in each input spectrum.
        """
        
        # apply sampler filter
        data = self.data[self.attr['samplers']==sampler]
        exposure = self.attr['exposure'][self.attr['samplers']==sampler]
        calmask = self.attr['calmask'][self.attr['samplers']==sampler]
        
        return np.ma.average(data[~calmask],axis=0,weights=exposure[~calmask])

    def max_tcal(self,sampler,verbose=0):
        """Get max tcal value for all spectra for given sampler

        Keyword arguments:
        sampler -- the sampler number
        verbose -- verbosity level, default to 0
        
        Returns:
        The max tcal value for the sampler.
        """
        
        # apply sampler filter
        tcal = self.attr['tcal'][self.attr['samplers']==sampler]
        return tcal.max()

    def mean_date(self,sampler,verbose=0):
        """Get mean date (as mjd) for all spectra for given sampler

        Keyword arguments:
        sampler -- the sampler number
        verbose -- verbosity level, default to 0
        
        Returns:
        A vector of mean dates (as mjd) for the sampler.
        """
        
        # apply sampler filter
        dates = self.attr['date'][self.attr['samplers']==sampler]
        mjds = np.array([ pipeutils.dateToMjd(xx) for xx in dates ])
        return mjds.mean()

    def min_date(self,sampler,verbose=0):
        """Get mean date for all spectra for given sampler

        Keyword arguments:
        sampler -- the sampler number
        verbose -- verbosity level, default to 0
        
        Returns:
        A vector of minumum dates for the sampler, one for each integration.
        If noise diode is firing, there is one date for each pair of integrations.
        """
        
        # apply sampler filter
        dates = self.attr['date'][self.attr['samplers']==sampler]
        calmask = self.attr['calmask'][self.attr['samplers']==sampler]
        
        if self.noise_diode:
            dates = dates[calmask]

        return pipeutils.dateToMjd(dates[0])
        
    def freq_axis(self,sampler,verbose=0):
        """ frequency axis to return for plotting

        Keyword arguments:
        sampler -- the sampler number
        verbose -- verbosity level, default to 0
        
        Returns:
        A mean frequency axis for the scan.
        """
        
        # apply sampler filter
        data = self.data[self.attr['samplers']==sampler]
        crpix1 = self.attr['crpix1'][self.attr['samplers']==sampler].mean()
        cdelt1 = self.attr['cdelt1'][self.attr['samplers']==sampler].mean()
        crval1 = self.attr['crval1'][self.attr['samplers']==sampler].mean()

        faxis = np.zeros(len(data[0]))
        for idx,e in enumerate(data[0]):
            faxis[idx] = ((idx-crpix1)*cdelt1+crval1)

        return faxis

    def average_tsys(self,sampler,verbose=0):
        """Get the total power for a single scan and sampler (i.e. feed,pol,IF)

        Keyword arguments:
        sampler -- the sampler number
        verbose -- verbosity level, default to 0
        
        Returns:
        An averaged, weighted sytem temperature, using the center 80% of
        the band.
        """

        # apply sampler filter
        data = self.data[self.attr['samplers']==sampler]
        exposure = self.attr['exposure'][self.attr['samplers']==sampler]
        tcal = self.attr['tcal'][self.attr['samplers']==sampler]

        chanlo = int(len(data)*.1)
        chanhi = int(len(data)*.9)

        ref = self.calonoff_ave(sampler)
        cal = self.calonoff_diff(sampler)

        ratios = ref[chanlo:chanhi] / cal[chanlo:chanhi]
        mytsys = ratios.mean() * self.max_tcal(sampler)

        Tsys = mytsys
        if (verbose > 0):
            print 'Tsys', Tsys
            print 'Tcal', tcal.mean()

        return Tsys

    def _average_coordinates(self,sampler):
        """Get exposure-weighted average coordinates

        Keyword arguments:
        sampler -- the sampler number
        
        NB: not used yet
        """
        
        calmask = self.attr['calmask'][self.attr['samplers']==sampler]
        elevation = self.attr['elevation'][self.attr['samplers']==sampler]
        azimuth = self.attr['azimuth'][self.attr['samplers']==sampler]
        longitude_axis = self.attr['longitude_axis'][self.attr['samplers']==sampler]
        latitude_axis = self.attr['latitude_axis'][self.attr['samplers']==sampler]
        target_longitude = self.attr['target_longitude'][self.attr['samplers']==sampler]
        target_latitude = self.attr['target_latitude'][self.attr['samplers']==sampler]

        tSum = exposure.sum()
        if self.noise_diode:
            exposure = self.attr['exposure'][self.attr['samplers']==sampler][calmask]
            el = (exposure * elevation[calmask]).sum() / tSum
            az = (exposure * azimuth[calmask]).sum() / tSum
            lon = (exposure * longitude_axis[calmask]).sum() / tSum
            lat = (exposure * latitude_axis[calmask]).sum() / tSum
            tLon = (exposure * target_longitude[calmask]).sum() / tSum
            tLat = (exposure * target_latitude[calmask]).sum() / tSum
        else:
            exposure = self.attr['exposure'][self.attr['samplers']==sampler]
            el = (exposure * elevation).sum() / tSum
            az = (exposure * azimuth).sum() / tSum
            lon = (exposure * longitude_axis).sum() / tSum
            lat = (exposure * latitude_axis).sum() / tSum
            tLon = (exposure * target_longitude).sum() / tSum
            tLat = (exposure * target_latitude).sum() / tSum

    def no_calibration(self,sampler,verbose):
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
        
        input_rows = self.attr['row'][self.attr['samplers']==sampler]
        
        if self.noise_diode:
            calmask = self.attr['calmask'][self.attr['samplers']==sampler]
            return input_rows[calmask]
        else:
            return input_rows

    def calibrate_to(self,sampler,refs,\
        ref_dates,ref_tsyss,k_per_count,forecastscript,opacity_coefficients,\
        ref_tskys,units,verbose):
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
        crpix1 = self.attr['crpix1'][self.attr['samplers']==sampler]
        cdelt1 = self.attr['cdelt1'][self.attr['samplers']==sampler]
        crval1 = self.attr['crval1'][self.attr['samplers']==sampler]
        
        input_rows = self.attr['row'][self.attr['samplers']==sampler]
        data = self.data[self.attr['samplers']==sampler]
        tcal = self.attr['tcal'][self.attr['samplers']==sampler]
        dates = self.attr['date'][self.attr['samplers']==sampler]
        elevations = self.attr['elevation'][self.attr['samplers']==sampler]
        temps = self.attr['tambient'][self.attr['samplers']==sampler]
        ambient_temp = temps.mean()
        
        # average signal CALON and CALOFF
        if self.noise_diode:
            calmask = self.attr['calmask'][self.attr['samplers']==sampler]
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

        #freq = self.freq_axis(sampler,verbose)

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
        if 6<= freq.mean() <=50 or 70<= freq.mean() <=116:
            opacities = pipeutils.tau(forecastscript,opacity_coefficients,mjds,elevations,freq)
        else:
            opacities = False
            
        if np.any(opacities):
            all_opacities = np.zeros(sig_counts.shape)
            dOpacity = (opacities[:,1]-opacities[:,0])/float(sig_counts.shape[1])
            for idx in range(sig_counts.shape[1]):
                all_opacities[:,idx] = opacities[:,0]+(idx*dOpacity)
            
            # get sky temperature contribution to signal
            tsky_sig = np.array([pipeutils.tsky(ambient_temp,freq[idx],opacity) for idx,opacity in enumerate(opacities)])
            allfreq = self.freq_axis(sampler)
            
            # tsky interpolation over frequency band (idl-like)
            all_tsky_sig = np.zeros(sig_counts.shape)
            dT = (tsky_sig[:,1]-tsky_sig[:,0])/float(sig_counts.shape[1])
            for idx in range(sig_counts.shape[1]):
                all_tsky_sig[:,idx] = tsky_sig[:,0]+(idx*dT)
            
            if verbose > 3:
                print 'TSKY SIG (interpolated)',all_tsky_sig[0][0],'to',all_tsky_sig[0][-1],'for first integration'
        
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

        if verbose > 3: # debug output
            print 'freqs',freq[0],'to',freq[-1]
            if np.any(opacities):
                print 'opacities',opacities.shape,opacities[0].mean()
                print 'TSKY REF',tsky_ref[0][0],'to',tsky_ref[0][-1]
                print 'Shapes Ta,all_tsky_sig,tsky_ref',Ta.shape,all_tsky_sig.shape,tsky_ref.shape
            print 'refs',ref.shape
            print 'tsys (mean)',tsys_ref.mean()
            print tsys_ref.mean(),sig_counts.shape,ref.shape
            print '1st int SIG aves[0],[1000],[nChan]',sig_counts[0][0],sig_counts[0][1000],sig_counts[0][-1]
            if len(refs) > 1:
                print 'B-REF [0],[1000],[nChan]',refs[0][0],refs[0][1000],refs[0][-1]
                print 'E-REF [0],[1000],[nChan]',refs[1][0],refs[1][1000],refs[1][-1]
                print '1st int REF [0],[1000],[nChan]',ref[0][0],ref[0][1000],ref[0][-1]
            print '1st int SIG [0],[1000],[nChan]',sig_counts[0][0],sig_counts[0][1000],sig_counts[0][-1]
            
        if not np.any(opacities) and not units=='Ta':
            if verbose > 0: print 'No opacities, calibrating to units of Ta'
            units=='Ta'
            
        if units=='TaTsky':
            # remove the elevation contribution to sky temperatures
            if np.any(all_tsky_sig) and np.any(tsky_ref):
                Ta = Ta - (all_tsky_sig - tsky_ref)
                Units = Ta
            
        if units=='Ta*' or units=='Tmb' or units=='Tb*':
            # Braatz 2007 (eqn. 3), modified with denominator == 1
            Ta_adjusted = Ta * all_opacities
            Units = Ta_adjusted
        
        if units=='Tmb' or units=='Tb*':
            # calculate main beam efficiency approx. = 1.32 * etaA
            #   where etaA is aperture efficiency
            # note to self: move to the top level so as to only call once?

            #etaMB = np.array([pipeutils.etaGBT(ff) for ff in freq]) # all frequencies
            allfreq = self.freq_axis(sampler)
            midfreq = allfreq[len(allfreq)/2] #reference freq of first integration
            etaMB = pipeutils.etaGBT(midfreq) # idl-like version

            # Braatz 2007 ("Calibration to Tmb and other units")
            Tmb = Ta_adjusted / etaMB
            Units = Tmb
            
        if not (units=='Ta' or units=='TaTsky' or units=='Ta*' or units=='Tmb' or units=='Tb*'):
            print 'Unable to calibrate to units of',units
            print '  calibrated to Ta'

        # compute system temperature for each integration
        #   using the scaling factor (Tcal/(calON-calOFF))
        #   from the reference scan(s)
        #   [using the center 80% of the band]
        chanlo = int(len(data[0])*.1)
        chanhi = int(len(data[0])*.9)
        tsys = k_per_count * sig_counts
        tsys = tsys[:,chanlo:chanhi].mean(1)

        for idx,row in enumerate(input_rows):
            row.setfield('DATA',Units[idx])
            row.setfield('TSYS',tsys[idx])

        return input_rows

    def average_reference(self,sampler,forecastscript,opacity_coefficients,verbose):
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
        
        crpix1 = self.attr['crpix1'][self.attr['samplers']==sampler].mean()
        cdelt1 = self.attr['cdelt1'][self.attr['samplers']==sampler].mean()
        crval1 = self.attr['crval1'][self.attr['samplers']==sampler].mean()
        data = self.data[self.attr['samplers']==sampler]
        
        max_tcal = self.max_tcal(sampler)
        mean_tsys = self.average_tsys(sampler,verbose)
        
        spectrum = self.calonoff_ave(sampler)
        date = self.min_date(sampler)

        elevations = self.attr['elevation'][self.attr['samplers']==sampler]
        exposure = self.attr['exposure'][self.attr['samplers']==sampler]

        dates = self.attr['date'][self.attr['samplers']==sampler]
        calmask = self.attr['calmask'][self.attr['samplers']==sampler]
        
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
            
        temps = self.attr['tambient'][self.attr['samplers']==sampler]
        ambient_temp = temps.mean()

        # idl-like version uses a single avg elevation
        if 6<= freq.mean() <=50 or 70<= freq.mean() <=116:
            opacities = pipeutils.tau(forecastscript,opacity_coefficients,[mjds.mean()],[self.elevation_ave(sampler)],freq,verbose)
            #opacities = pipeutils.tau(forecastscript,opacity_coefficients,mjds,elevations,freq)
        else:
            opacities = False
            
        allfreq = self.freq_axis(sampler)
        
        if np.any(opacities):
            tskys = pipeutils.tsky(ambient_temp,freq,opacities)
            all_tskys = pipeutils.interpolate(allfreq,freq,tskys)
            tskys = all_tskys
        else:
            tskys = False
        
        return spectrum,max_tcal,date,allfreq,tskys,mean_tsys
