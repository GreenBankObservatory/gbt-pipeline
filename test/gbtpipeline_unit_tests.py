import unittest
import numpy as np
import math
#import pipeutils
import Pipeutils

#import gbtpipeline as pipe

class Pipe:
    
    def __init__(self):
        self.BB = .0132  # Ruze equation parameter
        self.spillover = .99  # rear spillover, ohmic loss, blockage (etaL)
        self.gain_coefficients = [.0910,.00434,-5.22e-5,0]
    
    # ------------------------- Unit tests: do no depend on any other equations

    def Cref(self,calON,calOFF):  # eqn. (2) in PS spec
        return np.mean((calON,calOFF),axis=0)

    def Ccal(self,calON,calOFF):  # eqn. (3) in PS spec
        return calON - calOFF

    def Csig(self,calON,calOFF):  # part of eqn. (5) in PS spec
        return np.mean((calON,calOFF),axis=0)

    # eqn. (11) in PS spec
    def aperture_efficiency(self,reference_etaA,freqHz):
        freqGHz = float(freqHz)/1e9
        return reference_etaA * math.e**-((self.BB * freqGHz)**2)
        
    def gain(self,gain_coeff,elevation):
        # comput gain based on elevation, eqn. (12) in PS specification
        gain = 0
        zz = 90. - elevation
    
        for idx,coeff in enumerate(gain_coeff):
            gain = gain + coeff * zz**idx
            
        return gain

    # ------------------------ Functional tests: depend on underlying equations
    
    # same as Tsys for the reference scan
    def Tref(self,Cref,Ccal,Tcal): # eqn. (4) in PS spec
        return Tcal*(Cref/Ccal)
    
    def Ta(self,Tref,Csig,Cref):   # eqn. (5) in PS spec
        return Tref * ((Csig-Cref)/Cref)
    
    # eqn. (13) in PS spec
    def TaStar(self,Tsrc,beam_scaling,opacity,gain,elevation):
        gain = self.gain(self.gain_coefficients,elevation)
        return Tsrc*((beam_scaling*(math.e**opacity))/(self.spillover*gain))
        
    def jansky(self,TaStar,aperture_efficiency): # eqn. (16) in PS spec
        return TaStar/(2.85*aperture_efficiency)
    
    
    # eqn. (6) and eqn. (7) is PS spec
    def refInterp(self,reference1, reference2,
                   firstRef_timestamp, secondRef_timestamp,
                   integration_timestamp):
        
        time_btwn_ref_scans = secondRef_timestamp-firstRef_timestamp
        a1 =  (secondRef_timestamp-integration_timestamp) / time_btwn_ref_scans
        a2 =  (integration_timestamp-firstRef_timestamp)  / time_btwn_ref_scans
        return a1*reference1 + a2*reference2
        
class TestSpectrumOperations(unittest.TestCase):
    
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

        self.Tcal = 1.23
        
        self.pipe = Pipe()
        
    def test_Cref(self):
       
        result = self.pipe.Cref(self.calONRef,self.calOFFRef)
        expected_result = np.array([ 0.4693969 ,  0.67110545,  0.25880392])
        np.testing.assert_allclose(result,expected_result)
        
    def test_Csig(self):
       
        result = self.pipe.Cref(self.calONSig,self.calOFFSig)
        expected_result = np.array([ 0.73443476, 0.73426757, 0.25058055])
        np.testing.assert_allclose(result,expected_result)
        
    def test_Ccal(self):
       
        result = self.pipe.Ccal(self.calONRef,self.calOFFRef)
        expected_result = np.array([ 0.06462083, 0.62347095, 0.30250886])
        np.testing.assert_allclose(result,expected_result)

    def test_Tref(self):  # same as Tsys for the reference scan
        
        Cref = self.pipe.Cref(self.calONRef,self.calOFFRef)
        Ccal = self.pipe.Ccal(self.calONRef,self.calOFFRef)
        result = self.pipe.Tref(Cref,Ccal,self.Tcal)
        
        expected_result = np.array([ 8.93455163,  1.32397459,  1.05229588])
        np.testing.assert_allclose(result,expected_result)
        
    def test_aperture_efficiency(self):
        
        result = self.pipe.aperture_efficiency(.23,27e9)
        expected_result = 0.20256449890095335
        assert result == expected_result

    def test_gain(self):
        
        gain_coefficients = (.91,.00434,-5.22e-5)
        elevation = 60
        result = self.pipe.gain(gain_coefficients, elevation)
        expected_result = 0.99321999999999999
        assert result == expected_result
        
    @unittest.skip("Ignoring test per email from Joe Masters, 2017-10-26")
    def test_number_of_atmospheres(self):
        
        elevation_deg = 55
        result = Pipeutils.natm(elevation_deg)
        expected_result =  0.8191520442889918
        assert result == expected_result
        
    @unittest.skip("Ignoring test per email from Joe Masters, 2017-10-26")
    def test_atmospheric_effective_temperature(self):
        
        freqHz = 23e9
        temp_celcius = 40
        result = Pipeutils.tatm(freqHz, temp_celcius)
        expected_result = 298.88517422006998
        assert result == expected_result
        
    @unittest.skip("Ignoring test per email from Joe Masters, 2017-10-26")
    def test_atmospheric_opacity(self):  # eqn. (9) in PS spec
        
        zenith_opacities = [.01*xx for xx in range(1,9)]
        elevation = 45.
        result = Pipeutils.corrected_opacity(zenith_opacities, elevation)
        expected_result = [0.985957394633712, 0.9721119840328972,
                           0.958460999069284, 0.9450017095003759,
                           0.9317314234233945, 0.91864748673689,
                           0.9057472826099114, 0.8930282309586327]
        assert result == expected_result
        
    # ------------------------------------------------------- Functional Tests
    def test_Ta(self):
        
        Cref = self.pipe.Cref(self.calONRef,self.calOFFRef)
        Ccal = self.pipe.Ccal(self.calONRef,self.calOFFRef)
        Tref = self.pipe.Tref(Cref,Ccal,self.Tcal)

        Csig = self.pipe.Csig(self.calONSig,self.calOFFSig)
        result = self.pipe.Ta(Tref,Csig,Cref)
        
        expected_result = np.array([ 5.04475956,  0.12460791, -0.03343619])
        np.testing.assert_allclose(result,expected_result)

    @unittest.skip("Ignoring test per email from Joe Masters, 2017-10-26")
    def test_TaStar(self):
        
        Cref = self.pipe.Cref(self.calONRef,self.calOFFRef)
        Ccal = self.pipe.Ccal(self.calONRef,self.calOFFRef)
        Tref = self.pipe.Tref(Cref,Ccal,self.Tcal)
        Csig = self.pipe.Csig(self.calONSig,self.calOFFSig)
        Ta = self.pipe.Ta(Tref,Csig,Cref)
        
        elevation = 63
        gain = self.pipe.gain((.91,.00434,-5.22e-5),elevation)
        opacity = Pipeutils.corrected_opacity((.07,), elevation)[0]
        beam_scaling = 1
        result = self.pipe.TaStar(Ta,beam_scaling,opacity,gain,elevation)
        expected_result = np.array([75.49444398748547, 1.864747919874635,
                                    -0.5003700906180537])
        np.testing.assert_equal(result,expected_result)

    @unittest.skip("Ignoring test per email from Joe Masters, 2017-10-26")
    def test_jansky(self):
        
        Cref = self.pipe.Cref(self.calONRef,self.calOFFRef)
        Ccal = self.pipe.Ccal(self.calONRef,self.calOFFRef)
        Tref = self.pipe.Tref(Cref,Ccal,self.Tcal)
        Csig = self.pipe.Csig(self.calONSig,self.calOFFSig)
        Ta = self.pipe.Ta(Tref,Csig,Cref)
        
        elevation = 63
        gain = self.pipe.gain((.91,.00434,-5.22e-5),elevation)
        opacity = Pipeutils.corrected_opacity((.07,), elevation)[0]
        beam_scaling = 1
        tastar = self.pipe.TaStar(Ta,beam_scaling,opacity,gain,elevation)
        aperture_efficiency = self.pipe.aperture_efficiency(.23,27e9)
        result = self.pipe.jansky(tastar,aperture_efficiency)
        expected_result = np.array([ 130.76960048,    3.23007002,   -0.86672864])
        np.testing.assert_allclose(result,expected_result)
        
    def test_interpolated_reference_scan(self):  # eqn. (6) in PS spec
        
        reference_scan1 = np.array([10,10,10])
        reference_scan2 = np.array([20,20,20])
        
        firstRef_timestamp = 1000.
        secondRef_timestamp = 2000.
        
        integration_timestamp = 1350.
        
        result = self.pipe.refInterp(reference_scan1, reference_scan2,
                                      firstRef_timestamp, secondRef_timestamp,
                                      integration_timestamp)
        expected_result = np.array((13.5,13.5,13.5))
        np.testing.assert_equal(result, expected_result)

    def test_interpolated_reference_system_temp(self):  # eqn. (7) in PS spec
        
        reference_Tref1 = 40.
        reference_Tref2 = 50.
        
        firstRef_timestamp = 1000.
        secondRef_timestamp = 2000.
        
        integration_timestamp = 1500.
        
        result = self.pipe.refInterp(reference_Tref1, reference_Tref2,
                                      firstRef_timestamp, secondRef_timestamp,
                                      integration_timestamp)
        expected_result = 45.
        assert result == expected_result

if __name__ == '__main__':
    unittest.main()
