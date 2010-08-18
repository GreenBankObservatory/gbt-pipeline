PLOT=False

import sg_filter
from scipy import signal
import pylab

def median(spectrum,kernel_size):
        """Median filter to remove narrow RFI

        Keywords:
        spectrum -- spectrum to smooth
        kernel_size -- smoothing kernel (or cell) size
        
        Returns:
        A smoothed spectrum.
        """
        
        return signal.medfilt(spectrum,kernel_size)

def savgol(spectrum,num_points,degree_of_fitting):
        """Savitzky-Golay filter for smoothing spectrum

        Keywords:
        spectrum -- spectrum to smooth
        num_points -- 2*num_points+1 values contribute to the smoother.
        degree_of_fitting -- degree of fitting polynomial
        
        Returns:
        A smoothed spectrum.
        """

        coeff = sg_filter.calc_coeff(num_points, degree_of_fitting)
        return sg_filter.smooth(spectrum, coeff) 

def smooth_spectrum(spectrum,freq=False):
    """
    Apply multiple smoothing filters to spectrum.
    
    Three filters are applied:
    1) A median filter with cell size 5
    2) A Savitzky-Golay filter
    3) A median filter with cell size 3
    
    Keywords:
    spectrum -- the spectrum to smooth
    freq -- frequency axis for plotting
    
    Returns:
    A smoothed spectrum.
    """
    
    spectrum_noRFI = median(spectrum,5)

    # flatten the first 2 and last 2 channels
    nchan = len(spectrum)
    spectrum_noRFI[:2] = spectrum_noRFI[2]
    spectrum_noRFI[nchan-2:] = spectrum_noRFI[nchan-2]

    # savgol
    numpoints = nchan/64
    degree_of_fitting = 4
    spectrum_sg = savgol(spectrum_noRFI,numpoints,degree_of_fitting) 

    if PLOT and freq:
        pylab.figure()
        pylab.subplot(411)
        pylab.title('beginning spectrum')
        pylab.plot(freq,spectrum)
        pylab.subplot(412)
        pylab.title('no rfi')
        pylab.plot(freq,spectrum_noRFI)
        pylab.subplot(413)
        pylab.title('savgol')
        pylab.plot(freq,spectrum_sg)
        pylab.show()
        
    return spectrum_sg
