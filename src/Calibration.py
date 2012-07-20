import numpy as np
import math

class Calibration:
    """Class containing all the calibration methods for the GBT Pipeline.
    
    This includes both Position-switched and Frequency-switched calibration.
    
    """

    def __init__(self):
        
        # set calibration constants
        self.BB = .0132  # Ruze equation parameter
        self.SPILLOVER = .99  # rear spillover, ohmic loss, blockage (etaL)
        self.GAIN_COEFFICIENTS = [.910,.00434,-5.22e-5,0]
    
    # ------------- Unit methods: do not depend on any other pipeline methods

    def Cref(self,calON,calOFF):  # eqn. (2) in PS spec
        return np.mean((calON,calOFF),axis=0)

    def Ccal(self,calON,calOFF):  # eqn. (3) in PS spec
        return calON - calOFF

    def Csig(self,calON,calOFF):  # part of eqn. (5) in PS spec
        if 0 == len(calON) and len(calOFF) > 0:
            return calOFF
        elif 0 == len(calON) and 0 == len(calOFF):
            print 'No integrations provided to Csig method'
            raise
        else:
            return np.mean((calON,calOFF),axis=0)

    def tsky_corr(self, tsky_sig, tsky_ref):
        return self.SPILLOVER*(tsky_sig-tsky_ref)
    
    # eqn. (11) in PS spec
    def aperture_efficiency(self, reference_etaA, freqHz):
        """Determine aperture efficiency
        
        Keyword attributes:
        freqHz -- input frequency in Hz
    
        Returns:
        eta -- point or main beam efficiency (range 0 to 1)
        
        EtaA model is from memo by Jim Condon, provided by Ron Maddalena
    
        >>> aperture_efficiency(.71, 23e9)
        0.64748265789117276
    
        >>> aperture_efficiency(.91, 23e9)
        0.82987213898727774
        """
      
        freqGHz = float(freqHz)/1e9
        return reference_etaA * math.e**-((self.BB * freqGHz)**2)
        
    def main_beam_efficiency(self, reference_etaB, freqHz):
        """Determine main beam efficiency, given reference etaB value and freq.
        
        This is the same equation as is used to determine aperture efficiency.
        The only difference is the reference value.
        
        """
        
        return self.aperture_efficiency( reference_etaB, freqHz )
    
    def gain(self, gain_coeff, elevation):
        # comput gain based on elevation, eqn. (12) in PS specification
        gain = 0
        zz = 90. - elevation
    
        for idx,coeff in enumerate(gain_coeff):
            gain = gain + coeff * zz**idx
            
        return gain

    def elevation_adjusted_opacity(self, zenith_opacity, elevation):
        """Compute elevation-corrected opacities.

        Keywords:

        zenith_opacity -- opacity based only on time
        elevation -- (float) elevation angle of integration or scan
        
        """
        number_of_atmospheres = self.natm( elevation )
    
        corrected_opacity = zenith_opacity * number_of_atmospheres
    
        return corrected_opacity
    
    def natm(self,elDeg):
        """Compute number of atmospheres at elevation (deg)
    
        Keyword arguments:
        elDeg -- input elevation in degrees
    
        Returns:
        nAtmos -- output number of atmospheres
    
        Estimate the number of atmospheres along the line of site
        at an input elevation
    
        This comes from a model reported by Ron Maddale
    
        1) A = 1/sin(elev) is a good approximation down to about 15 deg but
        starts to get pretty poor below that.  Here's a quick-to-calculate,
        better approximation that I determined from multiple years worth of
        weather data and which is good down to elev = 1 deg:
        
        if (elev LT 39):
        A = -0.023437  + 1.0140 / math.sin( (math.pi/180.)*(elev + 5.1774 /
            (elev + 3.3543) ) )
        else:
        A = math.sin(math.pi*elev/180.)
    
        natm model is provided by Ron Maddalena
        
        """
    
        DEGREE = math.pi/180.
    
        if (elDeg < 39.):
            nAtmos = -0.023437 + \
                (1.0140 / math.sin( DEGREE*(elDeg + 5.1774 / (elDeg + 3.3543))))
        else:
            nAtmos = math.sin(DEGREE*elDeg)
    
        #print 'Model Number of Atmospheres:', nAtmos,' at elevation ',elDeg
        return nAtmos
        
    
    def tatm(self,freqHz, tmpC):
        """Estimates the atmospheric effective temperature
        
        Keyword arguments:
        freqHz -- input frequency in Hz
        where: tmpC     - input ground temperature in Celsius
    
        Returns:
        airTempK -- output Air Temperature in Kelvin
    
        Based on local ground temperature measurements.  These estimates
        come from a model reported by Ron Maddalena
        
        1) A = 1/sin(elev) is a good approximation down to about 15 deg but
        starts to get pretty poor below that.  Here's a quick-to-calculate,
        better approximation that I determined from multiple years worth of
        weather data and which is good down to elev = 1 deg:
    
            if (elev LT 39) then begin
                A = -0.023437  + 1.0140 / sin( (!pi/180.)*(elev + 5.1774 / (elev
        + 3.3543) ) )
            else begin
                A = sin(!pi*elev/180.)
            endif 
    
        2) Using Tatm = 270 is too rough an approximation since Tatm can vary
        from 244 to 290, depending upon the weather conditions and observing
        frequency.  One can derive an approximation for the default Tatm that is
        accurate to about 3.5 K from the equation:
    
        TATM = (A0 + A1*FREQ + A2*FREQ^2 +A3*FREQ^3 + A4*FREQ^4 + A5*FREQ^5)
                    + (B0 + B1*FREQ + B2*FREQ^2 + B3*FREQ^3 + B4*FREQ^4 +
        B5*FREQ^5)*TMPC
    
        where TMPC = ground-level air temperature in C and Freq is in GHz.  The
        A and B coefficients are:
    
                                    A0=    259.69185966 +/- 0.117749542
                                    A1=     -1.66599001 +/- 0.0313805607
                                    A2=     0.226962192 +/- 0.00289457549
                                    A3=   -0.0100909636 +/- 0.00011905765
                                    A4=   0.00018402955 +/- 0.00000223708
                                    A5=  -0.00000119516 +/- 0.00000001564
                                    B0=      0.42557717 +/- 0.0078863791
                                    B1=     0.033932476 +/- 0.00210078949
                                    B2=    0.0002579834 +/- 0.00019368682
                                    B3=  -0.00006539032 +/- 0.00000796362
                                    B4=   0.00000157104 +/- 0.00000014959
                                    B5=  -0.00000001182 +/- 0.00000000105
    
    
        tatm model is provided by Ron Maddalena
    
        >>> tatm(23e9,40)
        298.88517422006998
        >>> tatm(23e9,30)
        289.78060278466995
        >>> tatm(1.42e9,30)
        271.97866556636637
    
        """
    
        # where TMPC = ground-level air temperature in C and Freq is in GHz.
        # The A and B coefficients are:
        A = [259.69185966, -1.66599001, 0.226962192,
             -0.0100909636,  0.00018402955, -0.00000119516 ]
        B = [0.42557717,    0.033932476,0.0002579834,
             -0.00006539032, 0.00000157104, -0.00000001182]
        freqGHz = float(freqHz)/1e9
        FREQ  = float(freqGHz)
        FREQ2 = FREQ*FREQ
        FREQ3 = FREQ2*FREQ
        FREQ4 = FREQ3*FREQ
        FREQ5 = FREQ4*FREQ
    
        TATM = A[0] + A[1]*FREQ + A[2]*FREQ2 +A[3]*FREQ3 + A[4]*FREQ4 + A[5]*FREQ5
        TATM = TATM + (B[0] + B[1]*FREQ + B[2]*FREQ2 + B[3]*FREQ3 + B[4]*FREQ4 + B[5]*FREQ5)*float(tmpC)
    
        airTempK = TATM
        return airTempK
    
    def corrected_opacity(self,zenith_opacities,elevation):
        """Compute elevation-corrected opacities.
        
        Keywords:
        zenith_opacities -- opacity based only on time
        elevation -- (float) elevation angle of integration or scan
    
        """
        n_atmos = self.natm(elevation)
    
        corrected_opacities = [math.exp(-xx/n_atmos) for xx in zenith_opacities]
    
        return corrected_opacities

    def fractional_shift(self, spectra, delta_f):
        """Returns gain factor set for a given beam and polarization
    
        Keywords:
        spectra -- (numpy 2d array) of one or more spectra to be shifted
        delta_f -- (float) the channel amount to shift the spectra (< 1)
    
        Returns:
        (numpy 2d array) of shifted spectra
    
        """
        N_CHANNELS_start = spectra.shape[-1]
        N_CHANNELS_doubled = N_CHANNELS_start*2
    
        # double the size of the array
        spectra = np.append(spectra, np.zeros(shape=spectra.shape),axis=1)
    
        # shift the spectra to the center, with zeros padding either end
        ROLLDISTANCE = N_CHANNELS_start/2
        spectra = np.roll(np.array(spectra),ROLLDISTANCE)
    
        # pad out spectrum on both sides with end values
        for idx,row in enumerate(spectra):
            spectra[idx][:ROLLDISTANCE] = spectra[idx][ROLLDISTANCE]
            spectra[idx][-ROLLDISTANCE:] = spectra[idx][-ROLLDISTANCE-1]
    
        # inverse fft of spetrum, 0
        ifft = np.fft.ifft(spectra)
        real = ifft.real
        imag = ifft.imag
    
        # eqn. 9
        delta_p = 2.0 * np.pi * delta_f / N_CHANNELS_doubled
    
        # eqn. 7
        amplitude = np.sqrt(real**2 + imag**2)
    
        # eqn. 8
        phase = np.arctan2(imag,real)
    
        # eqn. 10
        kk = [np.mod(ii,N_CHANNELS_doubled/2) for ii in range(N_CHANNELS_doubled)]
        kk = np.array(kk,dtype=float)
    
        ## eqn. 11
        amplitude = amplitude * (1 - (kk/N_CHANNELS_doubled)**2)
    
        ## eqn. 12
        phase = phase + delta_p * kk
    
        # eqn. 13
        real = amplitude * np.cos(phase)
    
        # eqn. 14
        imag = amplitude * np.sin(phase)
    
        # finally fft to get back to spectra
        shifted = np.fft.fft(real+imag*1j)
    
        shifted = np.roll(shifted,-ROLLDISTANCE)
        shifted = shifted[:,:N_CHANNELS_start]
    
        return abs(shifted)

    def zenith_opacity_per_frequency(self, coeffs, freqs):
        """Interpolate low and high opacities across a vector of frequencies
    
        Keywords:
        coeffs -- (list) opacitiy coefficients from archived text file, produced by
            GBT weather prediction code
        freqs -- (list) of frequency values in GHz
    
        Returns:
        A (numpy 1d array) of a zenith opacity at each requested frequency.
        
        """
        # interpolate between the coefficients based on time for a given frequency
        def interpolated_zenith_opacity(f):
            # for frequencies < 2 GHz, return a default zenith opacity
            if np.array(f).mean() < 2:
                result = np.ones(np.array(f).shape)*0.008
                return result
            result=0
            for idx,term in enumerate(coeffs):
                if idx>0: result = result + term*f**idx
                else:
                    result=term
            return result
    
        zenith_opacities = [ interpolated_zenith_opacity(f) for f in freqs ]
        return np.array(zenith_opacities)
        
    # -------------- Functional methods: depend on underlying methods
    
    # same as Tsys for the reference scan
    def Tref(self,Cref,Ccal,Tcal): # eqn. (4) in PS spec
        return Tcal*(Cref/Ccal)
    
    def Ta(self,Tref,Csig,Cref):   # eqn. (5) in PS spec
        return Tref * ((Csig-Cref)/Cref)
    
    # eqn. (13) in PS spec
    def TaStar(self, Tsrc, beam_scaling, opacity, gain, elevation):
        if not gain:
            gain = self.gain(self.GAIN_COEFFICIENTS, elevation)
        return Tsrc*((beam_scaling*(math.e**opacity))/(self.SPILLOVER*gain))
        
    def jansky(self,TaStar,aperture_efficiency): # eqn. (16) in PS spec
        return TaStar/(2.85*aperture_efficiency)
    
    
    # eqn. (6) and eqn. (7) is PS spec
    def interpolate_by_time(self,reference1, reference2,
                   firstRef_timestamp, secondRef_timestamp,
                   integration_timestamp):
        
        time_btwn_ref_scans = secondRef_timestamp-firstRef_timestamp
        a1 =  (secondRef_timestamp-integration_timestamp) / time_btwn_ref_scans
        a2 =  (integration_timestamp-firstRef_timestamp)  / time_btwn_ref_scans
        return a1*reference1 + a2*reference2

    def getReferenceAverage(self, crefs, trefs, exposures, timestamps, tambients, elevations):
        
        # middle 80%
        number_of_data_channels = len(crefs[0])
        lo = int(.1*number_of_data_channels)
        hi = int(.9*number_of_data_channels)
        
        # convert to numpy arrays
        crefs = np.array(crefs)
        trefs = np.array(trefs)
        exposures = np.array(exposures)
        timestamps = np.array(timestamps)
        tambients = np.array(tambients)
        elevations = np.array(elevations)        
        
        tref80s = trefs[:,lo:hi].mean(axis=1)
        weights = exposures / tref80s**2
        avgTref = np.average(trefs[:,lo:hi],axis=0,weights=weights)
        
        avgTref80 = avgTref.mean(0) # single value for mid 80% of band
        avgCref = np.average(crefs,axis=0,weights=weights)
        
        avgTimestamp = timestamps.mean()
        avgTambient = tambients.mean() # do not know if this should be weighted
        avgElevation = elevations.mean() # do not know if this should be weighted
        
        return avgCref, avgTref80, avgTimestamp, avgTambient, avgElevation

    def tsky(self, ambient_temp_k, freqHz, tau):
        """Determine the sky temperature contribution at a frequency
        
        Keywords:
        ambient_temp_k -- (float) mean ambient temperature value, in kelvin
        freq -- (float)
        tau -- (float) opacity value
        Returns:
        the sky model temperature contribution at frequncy channel
        
        """
        ambient_temp_c = ambient_temp_k-273.15 # convert to celcius
        airTemp = self.tatm(freqHz, ambient_temp_c)
        
        tsky = airTemp * (1-math.e**(-tau))
        
        return tsky
