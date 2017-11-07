import unittest
import nose.tools as ntest

import numpy as np

from Calibration import Calibration


class test_Calibration:

    def __init__(self):
        self.cal = None

    def setup(self):
        self.cal = Calibration()

    @unittest.skip("Ignoring test per email from Joe Masters, 2017-10-26")
    def test_total_power(self):
        array1 = np.ones(10)
        array2 = np.ones(10) * 2
        result = self.cal.total_power(array1, array2)
        expected_result = np.ones(10) * 1.5
        np.testing.assert_equal(result, expected_result)

    def test_tsky(self):
        ambient_temp_k = 310.1
        freq_hz = 18.458
        tau = .05
        tsky = self.cal.tsky(ambient_temp_k, freq_hz, tau)
        expected_result = 13.432242475061472
        ntest.assert_almost_equal(tsky, expected_result)

    def test_tsky_correction(self):
        array_size = 128
        tsky_sig = np.ones(array_size) * 2
        tsky_ref = np.ones(array_size)
        spillover = .123
        tsky_correction = self.cal.tsky_correction(tsky_sig, tsky_ref, spillover)
        expected_result = np.ones(array_size) * .123
        np.testing.assert_equal(tsky_correction, expected_result)

    def test_aperture_efficiency(self):
        reference_eta_a = .71
        freq_hz = 23e9
        efficiency = self.cal.aperture_efficiency(reference_eta_a, freq_hz)
        expected_result = 0.64748265789117276
        ntest.assert_almost_equal(efficiency, expected_result)

    def test_main_beam_efficiency(self):
        reference_eta_a = .7
        freq_hz = 23.7e9
        efficiency = self.cal.main_beam_efficiency(reference_eta_a, freq_hz)
        expected_result = 0.6347374630868166
        ntest.assert_almost_equal(efficiency, expected_result)

    @unittest.skip("This test is outdated, and should be revisited in the future.")
    def test_elevation_adjusted_opacity(self):
        zenith_opacity = .1
        elevation = 45.
        adjusted_opacity = self.cal.elevation_adjusted_opacity(.1, 45.)
        expected_result = 0.07071067811865475
        ntest.assert_almost_equal(adjusted_opacity, expected_result)

    def test__tatm(self):
        freq_hz = 23e9
        temp_c = 40.
        atmospheric_effective_temp = self.cal._tatm(freq_hz, temp_c)
        expected_result = 298.88517422006998
        ntest.assert_almost_equal(atmospheric_effective_temp, expected_result)

    def test_zenith_opacity(self):
        opacity_coefficients = [2, 1, 0]
        freq_ghz = 16.79
        zenith_opacity = self.cal.zenith_opacity(opacity_coefficients, freq_ghz)
        expected_result = 18.79
        ntest.assert_equal(zenith_opacity, expected_result)

    def test_tsys(self):
        tcal = 1.
        cal_off = np.ones(128)
        cal_on = np.ones(128)*3
        tsys = self.cal.tsys(tcal, cal_on, cal_off)
        expected = 1.
        ntest.assert_equal(tsys, expected)

    @unittest.skip("Ignoring test per email from Joe Masters, 2017-10-26")
    def test_antenna_temp(self):
        tsys = .5
        sig = np.ones(128) * 2
        ref = np.ones(128)
        antenna_temp = self.cal.antenna_temp(tsys, sig, ref)
        expected_result = np.ones(128) * .5
        np.testing.assert_equal(antenna_temp, expected_result)

    @unittest.skip("This is a stub test that we would like to expand in the future.")
    def test__ta_fs_one_state(self):
        sigref_state = [{'cal_on': None, 'cal_off': None, 'TP': None},
                        {'cal_on': None, 'cal_off': None, 'TP': None}]

        sigref_state[0]['cal_on'] = np.ones(128)
        sigref_state[0]['cal_off'] = np.ones(128)

        sigref_state[1]['cal_on'] = np.ones(128)
        sigref_state[1]['cal_off'] = np.ones(128)

        sigid = 0
        refid = 1

        assert False

    @unittest.skip("This is a stub test that we would like to expand in the future.")
    def test_ta_fs(self):
        assert False

    @unittest.skip("Ignoring test per email from Joe Masters, 2017-10-26")
    def test_ta_star(self):
        antenna_temp = np.ones(128)
        beam_scaling = 1.
        opacity = 0
        spillover = 2.
        ta_star = self.cal.ta_star(antenna_temp, beam_scaling, opacity, spillover)
        expected = np.ones(128) * .5
        np.testing.assert_equal(ta_star, expected)

    def test_jansky(self):
        ta_star = np.ones(128)
        aperture_efficiency = .1
        jansky = self.cal.jansky(ta_star, aperture_efficiency)
        expected = np.ones(128) / .285
        np.testing.assert_almost_equal(jansky, expected)

    def test_interpolate_by_time(self):
        reference1 = 0.
        reference1_time = 10000.
        reference2 = 100.
        reference2_time = 20000.
        result_time = 15000.
        result_value = self.cal.interpolate_by_time(reference1, reference2,
                                                    reference1_time, reference2_time,
                                                    result_time)
        expected = 50.
        ntest.assert_equal(result_value, expected)
