from math import *
from numpy import *

def calc_coeff(num_points, pol_degree, diff_order=0):

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

def smooth(signal, coeff):
    
    """ applies coefficients calculated by calc_coeff()
        to signal """
    
    N = size(coeff-1)/2
    res = convolve(signal, coeff)
    return res[N:-N]

if __name__ == "__main__":

    x=arange(0, 10., .1)
    y=sin(x)
    coeff = calc_coeff(5, 2, diff_order=1)
    yPrime=smooth(y, coeff)

    # calibrate due to unknown correction
    # factor:
    N = len(x)
    dy =cos(x)  # exakt
    corrfac = dy[N/2]/yPrime[N/2]

    import pylab
    pylab.plot(x,y)
    pylab.plot(x,corrfac*yPrime)
    pylab.show()


    
