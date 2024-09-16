/* File medianVector.c, version 1.6, released  04/03/18 at 10:34:41 
   retrieved by SCCS 14/04/23 at 15:51:09     

%% function to return median of an array

:: GBES-C point antenna peakUp
 
History:
  031217 GIL - add a medianValue() function on a vector;
  030924 GIL - fix end by copying last point
  030922 GIL - fix end by copying last point
  030915 GIL - create a smoothed array based on an input
 
DESCRIPTION:
Do iterative median filtering 4 values at a time.
*/
#include "math.h"
#include "stdio.h"
#include "stdlib.h"
#include "STDDEFS.H"

extern double median3( double a, double b, double c);
extern double median4( double a, double b, double c, double d);
extern double median5( double a, double b, double c, double d, double e);
extern double medianLow3( double a, double b, double c);
extern double medianLow4( double a, double b, double c, double d);
extern double medianLow5( double a, double b, double c, double d, double e);
void shellSort(long n, double a[]);
#define MAXTEMP 512

char * medianVector(long n, long nSkip, double inArray[], double outArray[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* medianVector() interatively median filters an input array and returns     */
/* a median filtered vector.                                                 */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i = 0, dN = nSkip/4, twoDn = nSkip/2, j = 1, k=1;
  double tVector[MAXTEMP+4], x = 0, dX = (double)nSkip/(double)MAXTEMP;

  if (twoDn < 2) {
    twoDn = 2;
    dN    = 1;
    nSkip = (twoDn * 2);
  } /* end if not many points */

  if (dX < 1)
    dX = 1;

  /* for all points not at the end */
  for (i = twoDn; i < n - twoDn; i++) {
    /* take the end points as the first values in the array */
    tVector[1] =  inArray[i-twoDn];
    tVector[2] =  inArray[i+twoDn];
    j = 2;
    x = dX;
    k = x;
    /* while more values to sort, put in array from middle */
    while ((j < MAXTEMP) && (k < nSkip/2)) {
      tVector[j+1] = inArray[i+k];
      tVector[j+2] = inArray[i-k];
      x = x + dX;
      k = x;
      j = j + 2;
    }
    /* sort the J values (note values run 1 to J, not 0 to J-1 */
    shellSort( j, tVector);
    /* now average middle two so there are no zeros in the difference */
    outArray[i] = (tVector[(j/2)] + tVector[(j/2)+1])/2.;

    if (i == n/2) 
      fprintf( stderr, "medainVector: %f => %f (x=%f dx=%f n=%ld) j=%ld\n",
	       inArray[i], outArray[i], x, dX, nSkip, j);
    outArray[i] = median5( inArray[i-twoDn], inArray[i-dN], 
                           ((inArray[i-1]+(2.*inArray[i])+inArray[i+1])/4.), 
			   inArray[i+dN], inArray[i+twoDn]);
  }
  /* now do edges of vector, on pixel at a time */
  for (i = 1; i < twoDn; i++) {
    outArray[i] = median3( inArray[i-1], inArray[i], inArray[i+1]);
    outArray[n-i-1] = median3( inArray[n-i-2], inArray[n-i-1], inArray[n-i]);
  }

  /* finally the ends are just copies of the adjacent pixel */
  outArray[0] = outArray[1];
  outArray[n-1] = outArray[n-2];

  return(NULL);
} /*end of medianVector() */

#define TEMPARRAY 65000
#define MAXVALUES  2048
double tArray[TEMPARRAY];

double medianValue( long n, double inArray[])
/* medianValue() returns the median value of an array, but uses only */
/* every few values, to speed execution */
{ long nSkip = n/MAXVALUES, i = 0, j = 0;
  
  if (nSkip < 1)
    nSkip = 1;
 
  j = 1;
  for (i = 0; i < n; i = i + nSkip) {
    tArray[j] = inArray[i];
    j++;
  }

  shellSort( j, tArray);
  return( tArray[j/2]);
} /* end of medianValue() */
 
char * medianLoop( long n, long nSkip, double inArray[], double outArray[])
{ long i = 0, m = 4;

  medianVector( n, m, inArray, outArray);
  m = m * 2;

  while (m < nSkip) {
    for (i = 0; i < n; i++)
      tArray[i] = outArray[i];
    medianVector( n, m, tArray, outArray);
    m = m * 2;
  }

  return(NULL);
} /* end of medianLoop(); */
