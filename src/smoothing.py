import numpy as np
from math import *
from numpy import *
import signal # from scipy

debug = False

def median(spec,window):
    """Median filter to remove narrow RFI

    Keywords:
    spectrum -- spectrum to smooth
    kernel_size -- smoothing kernel (or cell) size
    
    Returns:
    A smoothed spectrum.
    
    """
        
    # if window is an even number, subtract 1
    if 0 == window % 2:
        window = window - 1
    return signal.medfilt(spec,window)

def savgol(spectrum,num_points,degree_of_fitting):
    """Savitzky-Golay filter for smoothing spectrum

    Keywords:
    spectrum -- spectrum to smooth
    num_points -- 2*num_points+1 values contribute to the smoother.
    degree_of_fitting -- degree of fitting polynomial
    
    Returns:
    A smoothed spectrum.
    
    """

    coeff = sg_calc_coeff(num_points, degree_of_fitting)
    return sg_smooth(spectrum, coeff) 

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

def sg_smooth(signal, coeff):
    
    """ applies coefficients calculated by calc_coeff()
        to signal
        
        Code from http://public.procoders.net/sg_filter
        
    """
    
    N = size(coeff-1)/2
    res = convolve(signal, coeff)
    return res[N:-N]
    
def sg_calc_coeff(num_points, pol_degree, diff_order=0):
    """ calculates filter coefficients for symmetric savitzky-golay filter.
        see: http://www.nrbook.com/a/bookcpdf/c14-8.pdf

        num_points   means that 2*num_points+1 values contribute to the
                     smoother.

        pol_degree   is degree of fitting polynomial

        diff_order   is degree of implicit differentiation.
                     0 means that filter results in smoothing of function
                     1 means that filter results in smoothing the first 
                                                 derivative of function.
                     and so on ...
                     
        Code from http://public.procoders.net/sg_filter

    """

    # setup interpolation matrix
    # ... you might use other interpolation points
    # and maybe other functions than monomials ....

    x = arange(-num_points, num_points+1, dtype=int)
    monom = lambda x, deg : pow(x, deg)

    A = zeros((2*num_points+1, pol_degree+1), float)
    for i in range(2*num_points+1):
        for j in range(pol_degree+1):
            A[i,j] = monom(x[i], j)
        
    # calculate diff_order-th row of inv(A^T A)
    ATA = dot(A.transpose(), A)
    rhs = zeros((pol_degree+1,), float)
    rhs[diff_order] = (-1)**diff_order
    wvec = linalg.solve(ATA, rhs)

    # calculate filter-coefficients
    coeff = dot(A, wvec)

    return coeff

