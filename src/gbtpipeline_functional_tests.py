import unittest
import numpy as np
import math
from Calibration import Calibration

class CalibrationFunctionalTests(unittest.TestCase):
    
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

    # ------------------------------------------------------- Functional Tests
    def test_Ta(self):
        
        Cref = self.calibration.Cref(self.calONRef,self.calOFFRef)
        Ccal = self.calibration.Ccal(self.calONRef,self.calOFFRef)
        Tref = self.calibration.Tref(Cref,Ccal,self.Tcal)

        Csig = self.calibration.Csig(self.calONSig,self.calOFFSig)
        result = self.calibration.Ta(Tref,Csig,Cref)
        
        expected_result = np.array([ 5.04475956,  0.12460791, -0.03343619])
        np.testing.assert_allclose(result,expected_result)
    
    def test_TaStar(self):
        
        Cref = self.calibration.Cref(self.calONRef,self.calOFFRef)
        Ccal = self.calibration.Ccal(self.calONRef,self.calOFFRef)
        Tref = self.calibration.Tref(Cref,Ccal,self.Tcal)
        Csig = self.calibration.Csig(self.calONSig,self.calOFFSig)
        Ta = self.calibration.Ta(Tref,Csig,Cref)
        
        elevation = 63
        gain = self.calibration.gain((.91,.00434,-5.22e-5),elevation)
        opacity = self.calibration.corrected_opacity((.07,), elevation)[0]
        beam_scaling = 1
        result = self.calibration.TaStar(Ta,beam_scaling,opacity,gain,elevation)
        expected_result = np.array([75.49444398748547, 1.864747919874635,
                                    -0.5003700906180537])
        np.testing.assert_equal(result,expected_result)

    def test_jansky(self):
        
        Cref = self.calibration.Cref(self.calONRef,self.calOFFRef)
        Ccal = self.calibration.Ccal(self.calONRef,self.calOFFRef)
        Tref = self.calibration.Tref(Cref,Ccal,self.Tcal)
        Csig = self.calibration.Csig(self.calONSig,self.calOFFSig)
        Ta = self.calibration.Ta(Tref,Csig,Cref)
        
        elevation = 63
        gain = self.calibration.gain((.91,.00434,-5.22e-5),elevation)
        opacity = self.calibration.corrected_opacity((.07,), elevation)[0]
        beam_scaling = 1
        tastar = self.calibration.TaStar(Ta,beam_scaling,opacity,gain,elevation)
        aperture_efficiency = self.calibration.aperture_efficiency(.23,27e9)
        result = self.calibration.jansky(tastar,aperture_efficiency)
        expected_result = np.array([ 130.76960048,    3.23007002,   -0.86672864])
        np.testing.assert_allclose(result,expected_result)
        
    def test_interpolated_reference_scan(self):  # eqn. (6) in PS spec
        
        reference_scan1 = np.array([10,10,10])
        reference_scan2 = np.array([20,20,20])
        
        firstRef_timestamp = 1000.
        secondRef_timestamp = 2000.
        
        integration_timestamp = 1350.
        
        result = self.calibration.interpolate_by_time(reference_scan1,
                                                      reference_scan2,
                                                      firstRef_timestamp,
                                                      secondRef_timestamp,
                                                      integration_timestamp)
        expected_result = np.array((13.5,13.5,13.5))
        np.testing.assert_equal(result, expected_result)

    def test_interpolated_reference_system_temp(self):  # eqn. (7) in PS spec
        
        reference_Tref1 = 40.
        reference_Tref2 = 50.
        
        firstRef_timestamp = 1000.
        secondRef_timestamp = 2000.
        
        integration_timestamp = 1500.
        
        result = self.calibration.interpolate_by_time(reference_Tref1,
                                                      reference_Tref2,
                                                      firstRef_timestamp,
                                                      secondRef_timestamp,
                                                      integration_timestamp)
        expected_result = 45.
        assert result == expected_result

if __name__ == '__main__':
    unittest.main()
