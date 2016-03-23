"""Calibration methods for the GBT Pipeline.

This module contains all the core calibration methods for GBT
single dish mapping needed by the pipeline.  It includes both
position-switched and frequency-switched calibration methods.

"""
# Copyright (C) 2007 Associated Universities, Inc. Washington DC, USA.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Correspondence concerning GBT software should be addressed as follows:
#       GBT Operations
#       National Radio Astronomy Observatory
#       P. O. Box 2
#       Green Bank, WV 24944-0002 USA

# $Id$

import numpy as np
import math
import smoothing
from Pipeutils import Pipeutils


class Calibration(object):

    def __init__(self, smoothing_window_size=0):

        # set calibration constants
        self.BB = .0132  # Ruze equation parameter
        self.UNDER_2GHZ_TAU_0 = 0.008
        self.SMOOTHING_WINDOW = smoothing_window_size
        self.pu = Pipeutils()

    # ------------- Unit methods: do not depend on any other pipeline methods

    def total_power(self, cal_on, cal_off, t_on, t_off):
        r"""Calculate the total power of spectrum with noise diode-switching.

        Args:
            cal_on(1d array): Spectrum *with* noise diode applied.
            cal_off(1d array): Spectrum *without* noise diode applied.
            t_on(float): Exposure time of the spectrum *with* noise diode.
            t_off(float): Exposure time of the spectrum *without* noise diode.

        Returns:
            1d array and float:

            A spectrum and a total exposure time.
            The spectrum is the average of the input spectra.
            The exposure time is the sum of the input exposure times.

        """
        return np.ma.mean((cal_on, cal_off), axis=0), t_on + t_off

    def tsky_correction(self, tsky_sig, tsky_ref, spillover):
        r"""Correction factor for sky brightness variation between reference and current integration.

        Args:
            tsky_sig(float): Sky brightness at current temperature, \
                frequency and elevation.
            tsky_ref(float): Sky brightness at reference temperature, \
                frequency and elevation.
            spillover(float): Spillover factor.

        Returns:
            float:
            A sky brightness correction factor.

            .. math::

               spillover * (tsky\_{sig} - tsky\_{ref})

        """
        return spillover * (tsky_sig - tsky_ref)

    def aperture_efficiency(self, reference_eta_a, freq_hz):
        r"""Determine telescope aperture efficiency at a given frequency.

        EtaA model is from memo by Jim Condon, provided by Ron Maddalena.

        Args:
            reference_eta_a(float): Reference aperture efficiency.
            freq_hz(float): Frequency in Hertz.

        Returns:
            float:
            Point or main beam efficiency (ranges from 0 to 1).

        .. testsetup::

           from Calibration import Calibration

        .. doctest:: :hide:

           >>> cal = Calibration()
           >>> print '{0:.6f}'.format(cal.aperture_efficiency(.71, 23e9))
           0.647483
           >>> print '{0:.6f}'.format(cal.aperture_efficiency(.91, 23e9))
           0.829872

        """
        freq_ghz = float(freq_hz)/1e9
        return reference_eta_a * math.e**-((self.BB * freq_ghz)**2)

    def main_beam_efficiency(self, reference_eta_b, freq_hz):
        r"""Determine main beam efficiency, given a reference etaB value and frequency.

        This is the same equation as is used to determine aperture efficiency.
        The only difference is the reference value.

        Args:
            reference_eta_b(float): The main beam efficiency. \
             For the GBT, the default is :math:`1.28 * \eta_A`, where :math:`\eta_A` is aperture efficiency.
            freq_hz(float): The frequency in Hertz.

        Returns:
            float:
            An aperture efficiency at a given frequency.
        """
        return self.aperture_efficiency(reference_eta_b, freq_hz)

    def elevation_adjusted_opacity(self, zenith_opacity, elev):
        r"""Compute elevation-corrected opacities.

        We need to estimate the number of atmospheres along the
        line of site at an input elevation

        This comes from a model reported by Ron Maddalena:

        :math:`A = \frac{1}{\sin(elev)}` is a good approximation down to about 15 deg but
        starts to get pretty poor below that.  Here's a quick-to-calculate,
        better approximation that I determined from multiple years worth of
        weather data and which is good down to elev = 1 deg:

        .. math::

           A = -0.023437  + \frac{1.0140}{\sin( \frac{pi}{180} * (elev + \frac{5.1774}{elev + 3.3543} )}

        Args:
            zenith_opacity(float): Opacity at zenith based only on time.
            elev(float): Elevation angle of integration or scan.

        Returns:
            float:
            Elevation-adjusted opacity

        .. testsetup::

           from Calibration import Calibration

        .. doctest:: :hide:

           >>> cal = Calibration()
           >>> print ['{0:.6f}'.format(cal.elevation_adjusted_opacity(1, el)) for el in range(90)]
           ['37.621216', '26.523488', '19.566942', '15.217485', '12.341207', '10.331365', '8.861127', '7.745094', '6.872195', '6.172545', '5.600276', '5.124171', '4.722318', '4.378917', '4.082311', '3.823718', '3.596410', '3.395144', '3.215779', '3.055004', '2.910137', '2.778989', '2.659751', '2.550918', '2.451229', '2.359617', '2.275175', '2.197126', '2.124803', '2.057628', '1.995099', '1.936775', '1.882273', '1.831253', '1.783416', '1.738495', '1.696253', '1.656478', '1.618982', '1.583595', '1.550162', '1.518545', '1.488619', '1.460271', '1.433397', '1.407903', '1.383703', '1.360719', '1.338878', '1.318115', '1.298369', '1.279585', '1.261710', '1.244698', '1.228504', '1.213089', '1.198415', '1.184446', '1.171152', '1.158501', '1.146467', '1.135024', '1.124146', '1.113814', '1.104005', '1.094700', '1.085882', '1.077533', '1.069639', '1.062184', '1.055156', '1.048543', '1.042331', '1.036512', '1.031074', '1.026009', '1.021309', '1.016966', '1.012972', '1.009322', '1.006009', '1.003029', '1.000376', '0.998047', '0.996038', '0.994346', '0.992968', '0.991902', '0.991147', '0.990701']

        """
        deg2rad = (math.pi/180)  # factor to convert degrees to radians
        num_atmospheres = -0.023437 + 1.0140 / math.sin(deg2rad * (elev + 5.1774 / (elev + 3.3543)))
        corrected_opacity = zenith_opacity * num_atmospheres

        return corrected_opacity

    def _tatm(self, freq_hz, tmp_c):
        """Estimates the atmospheric effective temperature.

        Keyword arguments:
        freq_hz -- input frequency in Hz
        where: tmp_c -- input ground temperature in Celsius

        Returns:
        air_temp_k -- output Air Temperature in Kelvin

        Based on local ground temperature measurements.  These estimates
        come from a model reported by Ron Maddalena

        Using Tatm = 270 is too rough an approximation since Tatm can vary
        from 244 to 290, depending upon the weather conditions and observing
        frequency.  One can derive an approximation for the default Tatm that
        is accurate to about 3.5 K from the equation:

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

        >>> print '{0:.6f}'.format(Calibration()._tatm(23e9, 40))
        298.885174
        >>> print '{0:.6f}'.format(Calibration()._tatm(23e9, 30))
        289.780603
        >>> print '{0:.6f}'.format(Calibration()._tatm(1.42e9, 30))
        271.978666

        """

        # where TMPC = ground-level air temperature in C and Freq is in GHz.
        # The A and B coefficients are:
        aaa = [259.69185966, -1.66599001, 0.226962192, -0.0100909636,  0.00018402955, -0.00000119516]
        bbb = [0.42557717, 0.033932476, 0.0002579834, -0.00006539032, 0.00000157104, -0.00000001182]
        freq_ghz = float(freq_hz)/1e9

        air_temp_k_A = air_temp_k_B = 0
        for idx, term in enumerate(zip(aaa, bbb)):
            if idx > 0:
                air_temp_k_A = air_temp_k_A + term[0] * (freq_ghz**idx)
                air_temp_k_B = air_temp_k_B + term[1] * (freq_ghz**idx)
            else:
                air_temp_k_A = term[0]
                air_temp_k_B = term[1]

        air_temp_k = air_temp_k_A + (air_temp_k_B * float(tmp_c))
        return air_temp_k

    def zenith_opacity(self, coeffs, freq_ghz):
        r"""Interpolate low and high opacities across a vector of frequencies.

        Args:
            coeffs(1d array): Opacitiy coefficients from archived text file, \
                produced by GBT weather prediction code.
            freq_ghz(float): Frequency value in GHz.

        Returns:
            float:
            A zenith opacity at requested frequency.

        """
        # interpolate between the coefficients based on time for a
        # given frequency
        def _interpolated_zenith_opacity(freq):
            # for frequencies < 2 GHz, return a default zenith opacity
            if np.array(freq).mean() < 2:
                result = np.ones(np.array(freq).shape)*self.UNDER_2GHZ_TAU_0
                return result
            result = 0
            for idx, term in enumerate(coeffs):
                if idx > 0:
                    result = result + term*freq**idx
                else:
                    result = term
            return result

        zenith_opacity = _interpolated_zenith_opacity(freq_ghz)
        return zenith_opacity

    def tsys(self, tcal, cal_on, cal_off):
        r"""Calculate the system temperature for an integration.

        Args:
            tcal(float): Lab-measured receiver calibration temperature.
            cal_on(1d array): Spectrum *with* noise diode applied.
            cal_off(1d array): Spectrum *without* noise diode applied.

        Returns:
            float:
            .. math::
               tcal * \frac{cal\_{off}}{cal\_{on} - cal\_{off}} + \frac{tcal}{2}

        """
        nchan = len(cal_off)
        low = int(.1 * nchan)
        high = int(.9 * nchan)
        cal_off = (cal_off[low:high]).mean()
        cal_on = (cal_on[low:high]).mean()
        return np.float(tcal * (cal_off / (cal_on - cal_off)) + tcal / 2)

    def antenna_temp(self, tsys, sig, ref, t_sig, t_ref):
        r"""Calibrate a spectrum to units of antenna temperature.

        Args:
            tsys(float): System temperature of the reference scan.
            sig(1d array): Signal ("on") spectrum.
            ref(1d array): Reference ("off") spectrum.
            t_sig(float): Exposure time of the signal spectrum.
            t_ref(float): Exposure time of the reference spectrum.

        Returns:
            1d array or float:
            A calibrated spectrum with an exposure time.
            The spectrum is

            .. math:: tsys * \frac{sig - ref}{ref}.

            The exposure time is

            .. math::
               \frac{t\_{sig} * t\_{ref} * window\_{size}}{t\_{sig} + (t\_{ref} * window\_{size})}

            where the window size is an optional smoothing kernel size for the
            reference spectrum.

        """
        if self.SMOOTHING_WINDOW > 1:
            ref = smoothing.boxcar(ref, self.SMOOTHING_WINDOW)
            window_size = self.SMOOTHING_WINDOW
        else:
            window_size = 1

        ref = self.pu.masked_array(ref)

        spectrum = tsys * ((sig-ref)/ref)
        exposure_time = (t_sig * t_ref * window_size / (t_sig + t_ref*window_size))
        return spectrum, exposure_time

    def _ta_fs_one_state(self, sigref_state, sigid, refid, scale):

        sig = sigref_state[sigid]['TP']

        ref = sigref_state[refid]['TP']
        ref_cal_on = sigref_state[refid]['cal_on']
        ref_cal_off = sigref_state[refid]['cal_off']

        tcal = ref_cal_off['TCAL'] * scale

        tsys = self.tsys(tcal,  ref_cal_on['DATA'],  ref_cal_off['DATA'])

        a_temp_params = {'tsys': tsys, 'sig': sig, 'ref': ref,
                         't_sig': sigref_state[sigid]['EXPOSURE'],
                         't_ref': sigref_state[refid]['EXPOSURE']}
        antenna_temp, exposure = self.antenna_temp(**a_temp_params)

        return antenna_temp, tsys, exposure

    def ta_fs(self, sigref_state, scale):
        r"""Calibrate a frequency-switched integration to units of antenna temperature.

        Args:
            sigref_state(struct): A structure holding the noise diode off and on \
                integrations (which are full rows from the FITS table, including the DATA column), \
                a total power integration, FITS table row number and \
                exposure time.
            scale(float): A relative beam scaling factor.  Default is 1, or no scaling.

        Returns:
            1d array, float, float:
            An averaged spectrum calibrated to units of antenna temperature, \
            a system temperature and a total exposure time for the spectrum.

        """

        ta0, tsys0, exposure0 = self._ta_fs_one_state(sigref_state, 0, 1, scale)
        ta1, tsys1, exposure1 = self._ta_fs_one_state(sigref_state, 1, 0, scale)

        # shift in frequency
        sig_centerfreq = sigref_state[0]['cal_off']['OBSFREQ']
        ref_centerfreq = sigref_state[1]['cal_off']['OBSFREQ']

        sig_delta = sigref_state[0]['cal_off']['CDELT1']
        channel_shift = -((sig_centerfreq-ref_centerfreq)/sig_delta)

        # do integer channel shift to second spectrum
        ta1_ishifted = np.roll(ta1, int(channel_shift))
        if channel_shift > 0:
            ta1_ishifted[:channel_shift] = float('nan')
        elif channel_shift < 0:
            ta1_ishifted[channel_shift:] = float('nan')

        # do fractional channel shift
        fractional_shift = channel_shift - int(channel_shift)
        # doMessage(logger, msg.DBG, 'Fractional channel shift is',
        #          fractional_shift)
        xxp = range(len(ta1_ishifted))
        yyp = ta1_ishifted
        xxx = xxp-fractional_shift

        yyy = np.interp(xxx, xxp, yyp)
        ta1_shifted = self.pu.masked_array(yyy)

        exposures = np.array([exposure0, exposure1])
        tsyss = np.array([tsys0, tsys1])
        tas = [ta0, ta1_shifted]

        # average shifted spectra
        ta = self.average_spectra(tas, tsyss, exposures)

        # average tsys
        tsys = self.average_tsys(tsyss, exposures)

        # only sum the exposure if frequency switch is "in band" (i.e.
        # overlapping channels); otherwise use the exposure from the
        # first state only
        if abs(channel_shift) < len(ta1):
            exposure_sum = exposure0 + exposure1
        else:
            exposure_sum = exposure0

        return ta, tsys, exposure_sum

    def ta_star(self, antenna_temp, opacity, spillover):
        r"""Calibrate a spectrum to units of **ta***.

        Args:
            antenna_temp(1d array): Spectrum calibrated to units of antenna temperature.
            opacity(float): Elevation-adjusted atmospheric opacity.
            spillover(float): Correction factor for rear-spillover,	ohmic loss and blockage	efficiency.

        Returns:
            1d array:
            A calibrated spectrum.

            .. math::
               antenna\_{temp} * e^{opacity} * \frac{1}{spillover}

        """
        # opacity is corrected for elevation
        return antenna_temp * math.e**opacity * 1 / spillover

    def jansky(self, spectrum, aperture_efficiency):
        r"""Calibrate a spectrum to units of **Jansky**.

        Args:
            spectrum(1d array): A spectrum previously calibrated to **ta***.
            aperture_efficiency(float): The aperture efficiency factor.

        Returns:
            1d array:

            .. math::
               \frac{spectrum}{2.85 * aperture\_{efficiency}}

        """
        return spectrum / (2.85 * aperture_efficiency)

    def interpolate_by_time(self, reference1, reference2,
                            first_ref_timestamp, second_ref_timestamp,
                            integration_timestamp):
        r"""Calculate interpolated value(s).

        This function can be used to calculate a single interpolated value
        or an array of values at a specified time.

        Args:
            reference1(float or 1d array): Value(s) for first time.
            reference2(float or 1d array): Value(s) for second time.
            first_ref_timestamp(float): First time.
            second_ref_timestamp(float): Second time.
            integration_timestamp(float): The time for which we want a value.

        Returns:
            float or 1d array:
            Interpolated value(s) for a specific time.

        .. testsetup::

           from Calibration import Calibration
           import numpy as np

        .. doctest:: :hide:

           >>> cal = Calibration()
           >>> cal.interpolate_by_time(1, 2, 0, 100, 75)
           1.75
           >>> cal.interpolate_by_time(np.array([1, 2]), np.array([2, 3]), 0, 100, 75)
           array([ 1.75,  2.75])

        """

        time_btwn_ref_scans = float(second_ref_timestamp) - float(first_ref_timestamp)
        aa1 = (second_ref_timestamp - integration_timestamp) / time_btwn_ref_scans
        aa2 = (integration_timestamp - first_ref_timestamp) / time_btwn_ref_scans
        return aa1 * reference1 + aa2 * reference2

    def make_weights(self, tsyss, exposures):
        r"""Create weights for integration averaging.

        Args:
            tsyss(1d array): A list of system temperatures.
            exposures(1d array): A list of exposure times.  \
            The number of exposure times must match the number of system temperatures.

        Returns:
            1d array:
            A list of weights.  The weights are computed with the following formula.

            .. math::

               \frac{exposure\ time}{tsys^2}

        """
        return exposures / tsyss**2

    def average_tsys(self, tsyss, exposures):
        r"""Compute a weighted average multiple system temperatures.

        Args:
            tsyss(1d array): The system temperatures to average.
            exposures(1d array): The exposure times corresponding to each system temperature.

        Returns:
            1d array:
            A weighted average system temperature.  See the *make_weights* method to see how
            the weights are computed.

        """
        weights = self.make_weights(tsyss, exposures)
        return np.sqrt(np.average(tsyss**2, axis=0, weights=weights))

    def average_spectra(self, specs, tsyss, exposures):
        r"""Perform a weighted average of two spectra.

        Args:
            specs(two 1d arrays): The two input spectra to be averaged.
            tsyss(two floats): System temperatures corresponding to each input spectrum.
            exposures(two floats): Exposure times corresponding to each input spectrum.

        Returns:
            1d array:
            A weighted average spectrum.  See the *make_weights* method to see how the weights
            are computed.

        """
        weights = self.make_weights(tsyss, exposures)

        if float('nan') in specs[0] or float('nan') in specs[1]:

            weight0 = np.ma.array([weights[0]] * len(specs[0]), mask=specs[0].mask)
            weight1 = np.ma.array([weights[1]] * len(specs[1]), mask=specs[1].mask)
            weights = [weight0.filled(0), weight1.filled(0)]

        return np.ma.average(specs, axis=0, weights=weights)

    def getReferenceAverage(self, crefs, tsyss, exposures, timestamps,
                            tambients, elevations):
        r"""Average the total power integrations from a reference scan.

        Args:
            crefs(stack of 1d arrays): The total power integrations (spectra) for a single reference scan.
            tsyss(1d array): The system temperatures; one for each input spectrum.
            exposures(1d array): The exposure times; one for each input spectrum.
            timestamps(1d array): The timestamps; one for each input spectrum.
            tambients(1d array): Ambient temperatures in Kelvin; one for each input spectrum.
            elevations(1d array): Elevation in degrees; one for each input spectrum.

        Returns:
            1d array, float, float, float, float, float:
            An average value for each of the input parameters.  An average spectrum along with
            average system temperature, exposure time, timestamp, ambient temperature and elevation.

        """

        # convert to numpy arrays
        crefs = np.array(crefs)
        tsyss = np.array(tsyss)
        exposures = np.array(exposures)
        timestamps = np.array(timestamps)
        tambients = np.array(tambients)
        elevations = np.array(elevations)

        avg_tsys = self.average_tsys(tsyss, exposures)

        avg_tsys80 = avg_tsys.mean(0)  # single value for mid 80% of band
        avg_cref = self.average_spectra(crefs, tsyss, exposures)
        exposure = np.sum(exposures)

        avg_timestamp = timestamps.mean()
        avg_tambient = tambients.mean()
        avg_elevation = elevations.mean()

        return avg_cref, avg_tsys80, avg_timestamp, avg_tambient, avg_elevation, exposure

    def tsky(self, ambient_temp_k, freq_hz, tau):
        r"""Determine the sky brightness temperature at a frequency.

        Args:
            ambient_temp_k(float): Mean ambient temperature in Kelvin.
            freq_hz(float): Frequency in Hz.
            tau(float): Atmospheric opacity value.

        Returns:
            float:
            The sky model temperature contribution at frequency channel.

        """
        ambient_temp_c = ambient_temp_k - 273.15  # convert to Celsius
        airTemp = self._tatm(freq_hz, ambient_temp_c)

        tsky = airTemp * (1 - math.e**(-tau))

        return tsky

if __name__ == "__main__":
    import doctest
    doctest.testmod()
