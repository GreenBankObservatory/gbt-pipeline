/* File fgauss.c, version 1.1, released  01/09/07 at 14:48:06 
   retrieved by SCCS 14/04/23 at 15:51:11     

%% Multiple Gaussian Fitting function for mrq minization
:: general purpose

HISTORY
010904 GIL initial version

DESCRIPTON
fgauss() returns the values of a gaussian and its derivatives
in the an array.  The elements in the array are placed
in the order expected for mrq minization.

Documentation:
See Levenberg-Marquardt Mimization.

OMISSIONS
*/

#include <math.h>

#define SMALL 1.E-20

void fgauss(float x, float a[], float *y, float dyda[], int na)
{ long i = 0;
  double fac = 0, ex = 0, arg = 0;

  *y=0.0;
  for (i=1;i<=na-1;i+=3) {
    if (a[i+2] == 0.) {
      dyda[i] = SMALL;
      dyda[i+1] = SMALL;
      dyda[i+2] = SMALL;
    }
    else {
      arg=(x-a[i+1])/a[i+2];
      ex=exp(-arg*arg);
      fac=a[i]*ex*2.0*arg;
      *y += a[i]*ex;
      dyda[i]=ex;
      dyda[i+1]=fac/a[i+2];
      dyda[i+2]=fac*arg/a[i+2];
    }
  } /* end of non-zero value in array */
} /* end of fgauss() */
