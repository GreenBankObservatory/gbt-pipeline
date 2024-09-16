/* File calcRMS.c, version 1.2, released  95/07/25 at 10:53:13 
   retrieved by SCCS 14/04/23 at 15:50:51     

%% calcRMS() calculates the RMS of an array of values.

:: GBES-C real-time Offline
 
HISTORY:
  950724  ignore zeroed points in rms calculation.
  950529  GIL initial version

DESCRIPTION:
calcRMS() calculates the RMS of an array of values.
*/

#include "math.h"

#define SMALL 1.0E-20

double calcRMS( int n, double a[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* calcRMS() returns the rms of an array of values, 0 if not enough data     */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ double sumf = a[0], sumff = a[0]*a[0], rms = 0.0;
  int i, count = 1;                         /* first point is used for init */
 
  for (i=1; i < n; i++){                    /* for all points */
    if (a[i] != 0.0) {                      /* if not - blanked data */
      sumf  += a[i];                        /* do sums */
      sumff += a[i]*a[i];
      count ++;
    } /* end if not blanked */
  } /* end of for all points */
  
  if (count < 2)                            /* if not enough data */
    return( rms);                           /* return zero */
  rms = (sumff - (sumf*sumf/(double)count))/((double)count - 1.); 

  if (rms > SMALL)                          /* avoid negative square root */
    rms = sqrt(rms);
  else                                      /* else null return */
    rms = 0.0;
  return(rms);
} /* end of calcRMS() */

