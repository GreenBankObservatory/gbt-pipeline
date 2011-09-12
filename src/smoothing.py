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
from math import *
from numpy import *

debug = False

def medfilt1(x=None,L=None):

    '''
    a simple median filter for 1d numpy arrays.

    performs a discrete one-dimensional median filter with window
    length L to input vector x. produces a vector the same size 
    as x. boundaries handled by shrinking L at edges; no data
    outside of x used in producing the median filtered output.
    (upon error or exception, returns None.)

    inputs:
        x, Python 1d list or tuple or Numpy array
        L, median filter window length
    output:
        xout, Numpy 1d array of median filtered result; same size as x
    
    bdj, 5-jun-2009
    '''

    # input checks and adjustments --------------------------------------------
    try:
        N = len(x)
        if N < 2:
            print 'Error: input sequence too short: length =',N
            return None
        elif L < 2:
            print 'Error: input filter window length too short: L =',L
            return None
        elif L > N:
            print 'Error: input filter window length too long: L = %d, len(x) = %d'%(L,N)
            return None
    except:
        print 'Exception: input data must be a sequence'
        return None

    xin = np.array(x)
    if xin.ndim != 1:
        print 'Error: input sequence has to be 1d: ndim =',xin.ndim
        return None
    
    xout = np.zeros(xin.size)

    # ensure L is odd integer so median requires no interpolation
    L = int(L)
    if L%2 == 0: # if even, make odd
        L += 1 
    else: # already odd
        pass 
    Lwing = (L-1)/2

    # body --------------------------------------------------------------------

    for i,xi in enumerate(xin):
  
        # left boundary (Lwing terms)
        if i < Lwing:
            xout[i] = np.median(xin[0:i+Lwing+1]) # (0 to i+Lwing)

        # right boundary (Lwing terms)
        elif i >= N - Lwing:
            xout[i] = np.median(xin[i-Lwing:N]) # (i-Lwing to N-1)
            
        # middle (N - 2*Lwing terms; input vector and filter window overlap completely)
        else:
            xout[i] = np.median(xin[i-Lwing:i+Lwing+1]) # (i-Lwing to i+Lwing)

    return xout


def median(spec,window):
    """Median filter to remove narrow RFI

    Keywords:
    spectrum -- spectrum to smooth
    kernel_size -- smoothing kernel (or cell) size
    
    Returns:
    A smoothed spectrum.
    
    """
        
    return medfilt1(spec,window)

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

