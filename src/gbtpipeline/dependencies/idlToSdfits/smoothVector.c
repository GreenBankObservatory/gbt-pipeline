/* File smoothVector.c, version 1.3, released  07/05/31 at 08:51:47 
   retrieved by SCCS 14/04/23 at 15:51:07     

%% Utility function for smoothing vectors.
:: spectrometer data reduction

HISTORY
060504 GIL free convolving function
030626 GIL add a convolving function
030625 GIL initial version from plotspec.c

DESCRIPTON
Selection of averaging functions for vector processing.

OMISSIONS
*/

#include "stdio.h"
#include "stdlib.h"
#include "string.h"
#include "math.h"

#include "STDDEFS.H"

/* externals */
extern void medianFilter ( int count, 
			   int medWid2, double inarr[], double outarr[]);
/* internals */
#define EPSILON .001

char * smoothCal( long n, double arrayIn[], double arrayOut[], long nSmooth)
/* smoothCal() takes an input array and fills a smooth output array          */
/* a major feature of smoothCal() is is rejection of high and low points     */
/* INPUTS n            number of points in the input/output arrays           */
/* arrayIn[]           array of vector points to smooth                      */
/* nSmooth             half width of smoothing function (pixels)             */
/* OUTPUT arrayOut[]   array of smoothed data                                */
/* returns error message on input error, else NULL for OK                    */
{ long i = 0, filterWidth = nSmooth/10, j = 0, count = 0, jStart = 0, jEnd =n;
  double factor = 1., yMax = 0, yMin = 0, * yTemp;

  if (nSmooth < 2) {
    for (i = 0; i < n; i++)
      arrayOut[i] = arrayIn[i];
    return(NULL);
  }

  if (n < 1) 
    return("smoothCal: No data to smooth");

  yTemp = (double*) malloc( n * sizeof(double));

  /* if doing any cal filtering before smoothing */
  if (filterWidth > 2) {
    medianFilter ( n, filterWidth, arrayIn, arrayOut);
    for (i = 0; i < n; i++) 
      yTemp[i] = arrayOut[i];
  }
  else {
    for (i = 0; i < n; i++) 
      yTemp[i] = arrayIn[i];
  }

  /* if no smoothing of cal data, transfer and exit */ 
  if (nSmooth < 1) {
    for (i = 0; i < n; i++)
      arrayOut[i] = yTemp[i];
    free( yTemp);
    return(NULL);
  }

  /* smooth the calibration signal */
  for( i=1; i < n-1; i++ ) {
    count = 0;
    arrayOut[i] = 0;                       /* initialize the sum */
    jStart = i - nSmooth;                  /* symetric smoothing */
    if (jStart < 2)
      jStart = 2;
    jEnd = i + nSmooth;
    if (jEnd > n-1)
      jEnd = n-1;
    for (j = jStart; j < jEnd; j ++) {
      if (yTemp[j] > EPSILON) {           /* cal values must be positive */
	arrayOut[i] += yTemp[j];
	if (count == 0) {                  /* prepare to reject extreama  */
	  yMax = yMin = yTemp[j];
	}
	else if (yTemp[j] > yMax)
	  yMax = yTemp[j];
	else if (yTemp[j] < yMin)
	  yMin = yTemp[j];
	count ++;
      }
    } /* end for all values to average */

    if (count > 4) {                       /* if values, reject extreama */
      arrayOut[i] -= (yMax + yMin);
      count = count - 2;
    }

    /* if a few data points to average */
    if (count > 1) {
      factor = count;
      arrayOut[i] = arrayOut[i]/factor;
    }
  } /* end for all call values to smooth */

  arrayOut[0]   = arrayOut[1];               /* do not smooth the ends */
  arrayOut[n-1] = arrayOut[n-2];

  free( yTemp);                            /* free scratch area */

  return(NULL);
} /* end of smoothCal() */

char * smoothVector( long n, long halfWidth, double y[])
/* smoothVector() performs an average of a vector with length n              */
{ double factor = 0, * yTemp, * convolve, width = (2*halfWidth)+1;
  long i = 0, j = 0;

  fprintf( stderr, "smoothVector: smoothing %ld, width %ld\n", n, halfWidth);

  if (halfWidth < 1) 
    return(NULL);

  yTemp = (double*)malloc( n*sizeof(double));
  convolve = (double*)malloc( width*sizeof(double));

  for (j = 0; j < width; j++) {
    if (j < halfWidth) 
      convolve[j] = (double)(j+1)/(double)halfWidth;
    else if (j == halfWidth)
      convolve[j] = 1.;
    else
      convolve[j] = (double)(width-j)/(double)halfWidth;
    factor += convolve[j];
  } /* end for size of convolving function */

  factor = 1./factor;

  /* average the data over the width, do not mess with ends */
  for (i = halfWidth; i < n - (halfWidth + 1); i++) {
    yTemp[i] = 0;
    for (j = 0; j < width; j++) 
      yTemp[i] += (y[i-halfWidth+j]*convolve[j]);
  } /* end for all values to average */


  /* transfer back out to input vector */
  for (i = halfWidth; i < n - (halfWidth+1); i++) 
    y[i] = yTemp[i]*factor;

  for (i = 0; i < halfWidth; i++) 
    y[i] = y[halfWidth];

  for (i = n-(halfWidth+1); i < n; i++) 
    y[i] = y[n-(halfWidth+2)];

  free( yTemp);
  free( convolve);

  return(NULL);
} /* end of smoothVector() */
