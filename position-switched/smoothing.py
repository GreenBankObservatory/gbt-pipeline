import sg_filter
#from scipy import signal
import numpy as np

debug = False

def median(spec,window):
        """Median filter to remove narrow RFI

        Keywords:
        spectrum -- spectrum to smooth
        kernel_size -- smoothing kernel (or cell) size
        
        Returns:
        A smoothed spectrum.
        """
        
    #def myfilt(spec,window):
    # if window is not an odd number, add 1
        if window % 2:
            window = window + 1
        
        speclen = len(spec)
        smoothed_spec = np.zeros(speclen)
        start = 0
        end = 0

        while end < speclen:
            end = start + window
            if debug:
                print 'start',start
                print 'end',end
                print spec[start:end]
                        
            mywin = spec[start:end].copy()
            mywin.sort()
            
            if debug:
                print 'median value',mywin[window/2]
            
            smoothed_spec[start+window/2] = mywin[window/2]
            if debug:
                print 'median value set', smoothed_spec[start+window/2]
            
            start = start + 1
            
        return smoothed_spec
    #return signal.medfilt(spectrum,kernel_size)

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

    return spectrum_sg
