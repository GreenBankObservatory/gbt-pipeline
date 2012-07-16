import unittest
import numpy as np
import math
from Calibration import Calibration

class CalibrationUnitTests(unittest.TestCase):
    
    # -------------------------------------------------------- Unit Tests
    
    def setUp(self):

        self.calONSig = np.array([0.6152100923665527, 0.500503480229196,
                                  0.14375595767163507])
        self.calOFFSig = np.array([0.8536594292721693, 0.968031662525558,
                                  0.35740514248237065])
        
        self.calONRef = np.array([0.5017073137242803, 0.982840923900886,
                                  0.4100583472818239])
        self.calOFFRef = np.array([0.43708647917671695, 0.3593699707018171,
                                   0.1075494918610801])

        self.signalSpectrum = np.array([0.19939720911472025,
                                        0.8967892966777684,
                                        0.43736262766783573,
                                        0.030255998719607935,
                                        0.27094536850779716,
                                        0.9093809936259405,
                                        0.41766409532371673,
                                        0.24996799132042768,
                                        0.6884521496518952,
                                        0.8271642209248296])
        self.referenceSpectrum = np.array([0.22093756087501182,
                                           0.7847365501830393,
                                           0.8954022648599212,
                                           0.2610437899155805,
                                           0.019954443457148252,
                                           0.43053368695417804,
                                           0.9345353067198212,
                                           0.7273991761793167,
                                           0.9560557601634491,
                                           0.6045882035561838])
        self.Tcal = 1.23
        
        self.calibration = Calibration()
        
    def test_Cref(self):
       
        result = self.calibration.Cref(self.calONRef,self.calOFFRef)
        expected_result = np.array([ 0.4693969 ,  0.67110545,  0.25880392])
        np.testing.assert_allclose(result,expected_result)
        
    def test_Csig(self):
       
        result = self.calibration.Cref(self.calONSig,self.calOFFSig)
        expected_result = np.array([ 0.73443476, 0.73426757, 0.25058055])
        np.testing.assert_allclose(result,expected_result)
        
    def test_Ccal(self):
       
        result = self.calibration.Ccal(self.calONRef,self.calOFFRef)
        expected_result = np.array([ 0.06462083, 0.62347095, 0.30250886])
        np.testing.assert_allclose(result,expected_result)

    def test_Tref(self):  # same as Tsys for the reference scan
        
        Cref = self.calibration.Cref(self.calONRef,self.calOFFRef)
        Ccal = self.calibration.Ccal(self.calONRef,self.calOFFRef)
        result = self.calibration.Tref(Cref,Ccal,self.Tcal)
        
        expected_result = np.array([ 8.93455163,  1.32397459,  1.05229588])
        np.testing.assert_allclose(result,expected_result)
        
    def test_aperture_efficiency(self):
        
        result = self.calibration.aperture_efficiency(.23,27e9)
        expected_result = 0.20256449890095335
        assert result == expected_result

    def test_gain(self):
        
        gain_coefficients = (.91,.00434,-5.22e-5)
        elevation = 60
        result = self.calibration.gain(gain_coefficients, elevation)
        expected_result = 0.99321999999999999
        assert result == expected_result
        
    def test_number_of_atmospheres(self):
        
        elevation_deg = 55
        result = self.calibration.natm(elevation_deg)
        expected_result =  0.8191520442889918
        assert result == expected_result
        
    def test_atmospheric_effective_temperature(self):
        
        freqHz = 23e9
        temp_celcius = 40
        result = self.calibration.tatm(freqHz, temp_celcius)
        expected_result = 298.88517422006998
        assert result == expected_result
        
    def test_atmospheric_opacity(self):  # eqn. (9) in PS spec
        
        zenith_opacities = [.01*xx for xx in range(1,9)]
        elevation = 45.
        result = self.calibration.corrected_opacity(zenith_opacities, elevation)
        expected_result = [0.985957394633712, 0.9721119840328972,
                           0.958460999069284, 0.9450017095003759,
                           0.9317314234233945, 0.91864748673689,
                           0.9057472826099114, 0.8930282309586327]
        assert result == expected_result
        
    def test_fractional_shift(self):
        
        spectra = np.array((self.signalSpectrum, self.referenceSpectrum))
        delta = .3
        result = delta
        result = self.calibration.fractional_shift(spectra, delta)
        expected_result = np.array([[0.29669266147078993, 0.8708622982701492,
                                     0.48828238252762146, 0.22764594712929065,
                                     0.3600770623516156, 0.9056863218854628,
                                     0.5116716578740499, 0.32729011378297557,
                                     0.7278360399849315, 0.8285624301488091],
            [0.35805286161824795, 0.7719686982271986, 0.8846714114742777,
             0.30813832149817155, 0.2291567578690566, 0.48735050763974735,
             0.9767073343655476, 0.7113385132940765, 0.8574580502212051,
             0.5579028921151957]])
        np.testing.assert_equal(result, expected_result)
        
if __name__ == '__main__':
    unittest.main()