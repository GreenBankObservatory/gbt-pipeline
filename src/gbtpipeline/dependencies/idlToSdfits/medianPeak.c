/* File medianPeak.c, version 1.4, released  13/01/24 at 14:17:40 
   retrieved by SCCS 14/04/23 at 15:50:51     

%% function to median filter a scan

:: GBES-C point antenna peakUp
 
History:
  120710 GIL add parameters, use doubles
  050415 GIL separate medianPeak()
  980301 GIL initial version based on patternMedian.c
 
DESCRIPTION:
This module takes a scan of observations and returns a
the maximum of the data.  The data are smoothed in several steps.
A) The median function does not perform well if the data have a large, 
systematic slope, so a first, wide median is performed.
B) A temporary array is filled with data, excluding sources exceeding 
the maxValue threshhold.
C) A median filter value is calculated for the data excluding maximum.

*/
#include "math.h"       /* Mathematical functions */
#include "stdio.h"      /* IO function */
#include "STDDEFS.H"    /* standard definitions. */
#include "MATHCNST.H"   /* Mathematical constants. */

/* externals */
void medianFilter( int, int, double *, double *);          /* array median */
double calcRMS( int n, double a[]);

/* internals */
#define SMALL 1.0E-10
#define NMAXIMA    100
#ifndef MAXSCAN
#define MAXSCAN 131072
#endif

#define FLAGVALUE 0.0

char * medianPeak( long n, long medianWidth, double maxValue, double fluxes[],
		   long peakWidth, long quiet)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* medianPeak() does a median filter excluding peaks in scan data to keep    */
/* radio sources.  A very wide median is first done to flatten data.  This   */
/* allows sources to be identified by intensity.  Next the median is done and*/
/* the peaks found.                                                          */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i = 0, iMaxima = 0, iMax = 0,
    medWid2 = medianWidth/4, peakStart[NMAXIMA], 
    peakStop[NMAXIMA], cMax = 0, peaks[NMAXIMA];
  double nPeakPoints = 0, fl[MAXSCAN], medianL[MAXSCAN];

  if (peakWidth < 2)
    peakWidth = 2;
  if (medWid2 < 2)
    medWid2 =  2;

  for (i = 0; i < n; i++)
    fl[i] = fluxes[i];

  medianFilter ( n, medWid2, fl, medianL);   /* median with extreama */

  for (i = 0; i < n; i++)
    medianL[i] = fl[i] - medianL[i];       /* subtract median to find sources*/

  cMax = 0;                                   /* n maxima */
  for (iMaxima = 0; iMaxima < NMAXIMA; iMaxima++) {    /* remove sources */
    iMax = 0;
    for (i=0; i < n; i++) {                      /* find max > sigma */
      if (medianL[iMax] < medianL[i])            /* if new maximum */
	iMax = i;
    } /* end for all points in scan */

    if (medianL[iMax] < maxValue)                /* if no significant */
      break;                                     /* quit search */

    peaks[cMax] = iMax;
    if (iMax - peakWidth > 0)                    /* else blank peak */
      peakStart[cMax] = iMax-peakWidth;          /* first blanked point */
    else 
      peakStart[cMax] = 0;

    if (iMax + peakWidth < n)                    /* more than last blanked*/
      peakStop[cMax] = iMax+peakWidth;
    else
      peakStop[cMax] = n;

    nPeakPoints = peakStop[cMax] - peakStart[cMax];

    /* interpolate between edges */
    for (i=peakStart[cMax]; i < peakStop[cMax]; i++) {/* remove */
      if (peakStart[cMax] < 1) {
        fl[i] = fl[peakStop[cMax]+1];
        medianL[i] = medianL[peakStop[cMax]+1];
      }
      else if (peakStop[cMax] >= n - 1) {
        fl[i] = fl[peakStart[cMax]-1];
        medianL[i] = medianL[peakStart[cMax]-1];
      }
      else {                                    /* interpolate */
 	fl[i] = (fl[peakStop [cMax]]  *(double)(i-peakStart[cMax])) + 
	        (fl[peakStart[cMax]-1]*(double)(peakStop[cMax] -i));
	fl[i] /= nPeakPoints;
 	medianL[i] = (medianL[peakStop [cMax]] *(double)(i-peakStart[cMax])) + 
	        (medianL[peakStart[cMax]-1]*(double)(peakStop[cMax] -i));
	medianL[i] /= nPeakPoints;
      }
    } /* end for all points to blank */

    cMax++;
  } /* end for all maxima */

  iMax = peaks[0];
  if (!quiet) {
    if (cMax > 0)
      fprintf( stderr, "%ld peaks found, max = %f (%lf) > %lf at %ld \n", 
	   cMax, fluxes[iMax], fl[iMax], maxValue, iMax);
  }

  medianFilter ( n, medWid2, fl, medianL);   /* no extreama */

  for (i=0; i < n; i++)
    fluxes[i] = fluxes[i] - medianL[i];

  return(NULL);
} /* end of medianPeak() */







