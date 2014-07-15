/* File linearFit.c, version 1.1, released  94/07/07 at 13:36:13 
   retrieved by SCCS 14/04/23 at 15:51:06     

%% diagnostic least squares fit to a straight line

:: GBES-C 

HISTORY: 
  940707 GIL - initial version, generic vxworks/unix version.

DESCRIPTION:
Least squares fit to a straight line.  Returns chi squared of fit.  Data not
weighted.
*/

#include <math.h>

double linearFit(double x[], double y[], int ndata, double *a,
	double *b, double *siga, double *sigb)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* linear least squares fit to a straight line.                              */
/* INPUTS:                                                                   */
/* x[],y[]   arrays of data coordinates                                      */
/* ndata     number of input data points                                     */
/* OUTPUTS:                                                                  */
/* a, b      intercept and slope of line                                     */
/* siga,sigb uncertainties of intercept and slope of line                    */
/* return                                                                    */
/* chi2      chi squared of fit                                              */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ int i;
  double t,sxoss,sx=0.0,sy=0.0,st2=0.0,ss,sigdat, chi2 = 1.0E30;

  *b=0.0;                         /* initialize to zeros */
  *a=0.0;
  *sigb=0.0;  
  *siga=0.0;

  if (ndata < 2)                  /* if no data return */
    return(chi2);

  for (i=0; i<ndata; i++) {       /* accumulate sums */
    sx += x[i];
    sy += y[i];
  }
  ss=ndata;                       

  sxoss=sx/ss;                    /* calculate fit */
  for (i=0;i<ndata;i++) {
    t=x[i]-sxoss;
    st2 += t*t;
    *b += t*y[i];
  }

  *b /= st2;                           /* calculate fit */
  *a=(sy-sx*(*b))/ss;

  *siga=sqrt((1.0+sx*sx/(ss*st2))/ss); /* calculate errors */
  *sigb=sqrt(1.0/st2);
  
  chi2 = 0;
  for (i=0;i<ndata;i++)                /* calc chi squared for fit */
    chi2 += (y[i]-(*a)-(*b)*x[i])*(y[i]-(*a)-(*b)*x[i]);

  if (ndata > 2)                  /* avoid divide by zero */
    sigdat=sqrt(chi2/(ndata-2));
  else
    sigdat=1.0;
  *siga *= sigdat;
  *sigb *= sigdat;
  return(chi2);
} /* end of linearFit() */
