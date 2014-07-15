/* File calcAveRmsRange.c, version 1.4, released  02/06/13 at 14:36:33 
   retrieved by SCCS 14/04/23 at 15:50:56     

%% calcRMS() calculates the RMS of an array of values.

:: GBES-C real-time Offline
 
HISTORY:
  020613  GIL update count of data points
  011011  GIL fix RMS calc
  010831  add functions to do calculations on ranges of inputs
  950724  ignore zeroed points in rms calculation.
  950529  GIL initial version

DESCRIPTION:
calcAveRms() calculates the Average, RMS of an array of values,
within specific array values.
*/

#include "math.h"
#include "STDDEFS.H"

#define SMALL 1.0E-20

char * calcAveRmsRange( double a[], long aStart, long aEnd, 
		long bStart, long bEnd, double * aveOut, double * rmsOut)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* calcRMS() returns the rms of an array of values, 0 if not enough data     */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ double sumf = 0, sumff = 0, rms = 0.0;
  long i, count = 0;                        /* first point is used for init */
 
  *aveOut = *rmsOut = 0;

  for (i=aStart; i < aEnd; i++) {           /* for all points */
    sumf  += a[i];                          /* do sums */
    count ++;
  } /* end of for all points */

  for (i=bStart; i < bEnd; i++){            /* for all points */
    sumf  += a[i];                          /* do sums */
    count ++;
  } /* end of for all points */

  if (count < 2)                            /* if not enough data */
    return( "Not enought data for Ave and RMS");

  *aveOut = sumf / (double)count;
  sumf = *aveOut;

  for (i=aStart; i < aEnd; i++)             /* for all points */
    sumff  += ((a[i] - sumf)*(a[i] - sumf));  

  for (i=bStart; i < bEnd; i++)             /* for all points */
    sumff  += ((a[i] - sumf)*(a[i] - sumf));  

  rms = sumff /((double)count - 1.); 

  if (rms > SMALL)                          /* avoid negative square root */
    rms = sqrt(rms);
  else                                      /* else null return */
    rms = 0.0;

  *rmsOut = rms;

  return(NULL);
} /* end of calcAveRmsRange() */

char * linearFitRange( double x[], double y[], long aStart, long aEnd, 
		       long bStart, long bEnd, double * ave, 
		       double *a, double *b, double *siga, double *sigb, 
		       double *chi2Out)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* linear least squares fit to a straight line.                              */
/* INPUTS:                                                                   */
/* x[],y[]   arrays of data coordinates                                      */
/* aStart, aEnd    end points of first range of data to fit                  */
/* bStart, bEnd    end points of second range of data to fit                 */
/* OUTPUTS:                                                                  */
/* ave       average of input data in ranges                                 */
/* a, b      intercept and slope of line                                     */
/* siga,sigb uncertainties of intercept and slope of line                    */
/* chi2      chi squared of fit                                              */
/* returns NULL on OK else error message                                     */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i = 0;
  double t = 0, sxoss = 0, sx=0.0, sy=0.0, st2=0.0, ss = 0, sigdat = 0,
    chi2 = 0.;

  *b=0.0;                         /* initialize to zeros */
  *a=0.0;
  *sigb=0.0;  
  *siga=0.0;

  for (i=aStart; i < aEnd; i++) {      /* accumulate sums */
    sx += x[i];
    sy += y[i];
    ss++;
  }
  for (i=bStart; i < bEnd; i++) {      /* accumulate sums */
    sx += x[i];
    sy += y[i];
    ss++;
  }

  if (ss < 3)
    return( "Not Enough data for fit");

  sxoss=sx/ss;                         /* calculate average fit */
  *ave = sxoss;                        /* return average */

  for (i=aStart; i < aEnd; i++) {      /* accumulate sums */
    t   =  x[i]-sxoss;
    st2 += t*t;
    *b  += t*y[i];
  }

  for (i=bStart; i < bEnd; i++) {      /* accumulate sums */
    t   =  x[i]-sxoss;
    st2 += t*t;
    *b  += t*y[i];
  }

  *b /= st2;                           /* calculate fit */
  *a=(sy-sx*(*b))/ss;

  *siga=sqrt((1.0+sx*sx/(ss*st2))/ss); /* calculate errors */
  *sigb=sqrt(1.0/st2);
  
  for (i=aStart; i < aEnd; i++)        /* accumulate sums */
    chi2 += (y[i]-(*a)-(*b)*x[i])*(y[i]-(*a)-(*b)*x[i]);

  for (i=bStart; i < bEnd; i++)        /* accumulate sums */
    chi2 += (y[i]-(*a)-(*b)*x[i])*(y[i]-(*a)-(*b)*x[i]);

  sigdat=sqrt(chi2/(ss-2));

  *siga *= sigdat;
  *sigb *= sigdat;
  *chi2Out = chi2;

  return(NULL);
} /* end of linearFitRange() */

char * subFitRange( double x[], double y[], long nData, 
		    long aStart, long aEnd, 
		    long bStart, long bEnd, double * ave, 
		    double *a, double *b, double *siga, double *sigb, 
		    double *chi2Out)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* SUBtrack linear Fit over a range                                          */
/* INPUTS:                                                                   */
/* x[],y[]   arrays of data coordinates                                      */
/* aStart, aEnd    end points of first range of data to fit                  */
/* bStart, bEnd    end points of second range of data to fit                 */
/* OUTPUTS:                                                                  */
/* ave       average of input data in ranges                                 */
/* a, b      intercept and slope of line                                     */
/* siga,sigb uncertainties of intercept and slope of line                    */
/* chi2      chi squared of fit                                              */
/* returns NULL on OK else error message                                     */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i = 0;
  char * errMsg = NULL;

  errMsg = linearFitRange( x, y, aStart, aEnd, bStart, bEnd, ave, 
			   a, b, siga, sigb, chi2Out);
  if (errMsg)
    return(errMsg);

  for (i=0; i < nData; i++)            /* subtract fit  */
    y[i] -= ((*a)+((*b)*x[i]));

  return(errMsg);
} /* end of linearFitRange() */

