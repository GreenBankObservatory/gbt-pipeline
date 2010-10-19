import unittest

import numpy as np

import smoothing
import pipeutils

class TestPipeUtils(unittest.TestCase):
    def setUp(self):
        self.freq = 23.1e9
        self.freqs = np.linspace(23,24,10)

    def test_dateToMjd(self):
        date_string = '2009-02-10T21:09:00.08'
        mjd = pipeutils.dateToMjd(date_string)
        self.assertEqual(mjd,54872.881250925828)
        
    def test_etaMB(self):
        etaMB = pipeutils.etaMB(self.freq)
        self.assertEqual(etaMB,0.84412523726701649)
    
    def test_gbtbeamsize(self):
        beamsize = pipeutils.gbtbeamsize(self.freq)
        self.assertEqual(beamsize,0.32658339154212729)

    def test_gd2d(self):
        jd = pipeutils.gd2jd('15','01','2010','08','20','23452343')
        self.assertEqual(jd,2455483.2863773149)

    def test_hz2wavelength(self):
        wavelength = pipeutils.hz2wavelength(self.freq)
        self.assertEqual(wavelength,0.012978028484848485)
        
    def test_interpolate(self):
        self.assertEqual(True,False)
        
    def test_interpolate(self):
        self.assertEqual(True,False)
        
    def test_interpolate_reference(self):
        self.assertEqual(True,False)
        
    def test_interpolate_tsys(self):
        self.assertEqual(True,False)
        
    def test_interpolated_zenith_opacity(self):
        self.assertEqual(True,False)
    
    def test_masked_array(self):
        self.assertEqual(True,False)
        
    def test_natm(self):
        self.assertEqual(True,False)
        
    def test_opacity_coefficients(self):
        self.assertEqual(True,False)
        
    def test_tatm(self):
        self.assertEqual(True,False)
        
    def test_tau(self):
        forecastscript = '/users/rmaddale/bin/getForecastValues'
        #opacity_coeffs = 
        #mjds = 
        #elevations = 
        #expected_taus = 
        #taus = pipeutils.tau(forecastscript,opacity_coeffs,mjds,elevations,self.freqs)
        self.assertEqual(True,False)

    def test_tsky(self):
        ambient_temp = 291.75
        opacity_factors = np.linspace(1.2,1.3,10)
        expected_tskys = np.array([53.521519, 56.49493672, 59.46835444,
            62.44177217, 65.41518989,  68.38860761, 71.36202533, 74.33544305,
            77.30886078,  80.2822785 ])
        tskys = pipeutils.tsky(ambient_temp,self.freqs,opacity_factors)
        for idx,ee in enumerate(tskys):
            self.assertAlmostEqual(ee,expected_tskys[idx],places=6)
        
class TestSmoothingFunctions(unittest.TestCase):
    def setUp(self):
        spec_size = 1024
        self.spectrum = np.random.random(spec_size)

    def test_median(self):
        kernel_size = 5
        median_smoothed = smoothing.median(self.spectrum,kernel_size)
        self.assertTrue(median_smoothed.std()<self.spectrum.std())

    def test_savgol(self):
        num_points = self.spectrum.size
        degree_of_fitting = 4
        sg_smoothed = smoothing.savgol(self.spectrum,num_points,degree_of_fitting)
        self.assertTrue(sg_smoothed.std()<self.spectrum.std())
        
    def test_smooth_spectrum(self):
        smoothed = smoothing.smooth_spectrum(self.spectrum)
        self.assertTrue(smoothed.std()<self.spectrum.std())

if __name__ == '__main__':
    unittest.main()


