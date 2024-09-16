/* File fftFilter.c, version 1.7, released  05/05/04 at 16:29:02 
   retrieved by SCCS 14/04/23 at 15:50:52     

%% utility filtering functions for smoothing and baselining
:: utility

HISTORY
050504 GIL make fftSmooth and fftSmoothF return identical values
050415 GIL try savgol for filtering
050414 GIL try to smooth filter to reject ripple.
050407 GIL add medianRms()
050406 GIL add medianSmooth for a float array
050405 GIL initial version based on IDL code

DESCRIPTION:
fftSmooth() median rejects outliers and fourier smooths the remaining points.
*/
#include "stdio.h"
#include "stdlib.h"
#include "string.h"
#include "math.h"
#include "MATHCNST.H"
#include "STDDEFS.H"

extern void realft( float data[], long n, int isign);
extern void medianFilter ( int count, int medWid2, double inarr[], 
			   double outarr[]);
extern double calcRMS( long n, double a[]);
extern char * calcAveRmsRange( double a[], long aStart, long aEnd, 
       long bStart, long bEnd, double * aveOut, double * rmsOut);
double medianSelect(unsigned long k, unsigned long n, double arr[]);

#define MAXTEMP 262144

char * fftFilter( float data[], long n, long nKeep)
/* fftFilter smooths a band pass by rejecting high frequency components     */
/* the original data is modified in place after two fourier transforms.     */
{ long i = 0;
  double factor = 1.;

  if (n < 4 || nKeep < 4)
    return("Need more points for filter");

  realft( &data[-1], n, 1);   /* realft expects arrays with range 1..n */

  for (i = nKeep; i < n; i++)  /* zero high frequency components */
    data[i] = 0;

  realft( &data[-1], n, -1);   /* realft expects arrays with range 1..n */

  factor = 2./(double)n;

  for (i = 0;  i < n;  i++)    /* scale data back to original scale */
    data[i] *= factor;

 return(NULL);
} /* end of fftFilter */

#define NEDGE 64
char * fftSmooth( double data[], long n, long nKeep)
/* fftSmooth flattens out a band pass, removing spikes but keeping  */
/* the general shape */
{ long i = 0, nKeep2 = nKeep/2;
  float fData[MAXTEMP]; 
  double outD[MAXTEMP], tempD[MAXTEMP], factor = 1.;

  for (i = 0; i < n; i++) 
    tempD[i] = data[i];

  for (i = 1; i < NEDGE; i++) {             /* smooth ends to zero */
    factor = exp(-0.1*(double)(NEDGE-i));
    tempD[i]   *= factor;
    tempD[n-i] *= factor;
  }
  tempD[0] = tempD[n-1] = 0.;

  for (i = nKeep2; i < n-nKeep2; i++) 
    tempD[i] -= (0.5*(data[i-nKeep2]+data[i+nKeep2]));

  for (i = 0; i < nKeep2; i++)
    tempD[i] -= tempD[i+nKeep2];

  for (i = nKeep2+1; i < n-nKeep2; i++)
    tempD[i] -= tempD[i-nKeep2];

  /* reject high peaks in input data */
  medianFilter( (int)n, (int)nKeep, tempD, outD);

  for (i = 0; i < n; i++) 
    fData[i] = outD[i];

  realft( &fData[-1], n, 1);   /* realft expects arrays with range 1..n */

  for (i = nKeep; i < nKeep+NEDGE; i++) /* zero high frequency components */
    fData[i] *= exp(-0.1*(double)(i-nKeep));

  for (i = nKeep+NEDGE; i < n; i++) /* zero high freq. components to smooth */
    fData[i] = 0;

  realft( &fData[-1], n, -1);  /* realft expects arrays with range 1..n */

  factor = 2./(double)n;

  for (i = 0;  i < n;  i++)
    data[i] = fData[i]*factor;

  return(NULL);
} /* end of fftSmooth() */
 
double medianFftValue( double data[], long n, long nKeep)
/* medianFftValue() smooths a function after median filtering to get a  */
/* representative value for the array of values                            */
/* the input data is not modified                                          */
{ long i = 0;
  float fData[MAXTEMP]; 
  double outD[MAXTEMP], midPoint = 0.;

  /* reject high peaks in input data */
  medianFilter( (int)n, (int)(nKeep/2), data, outD);

  for (i = 0; i < n; i++) 
    fData[i] = outD[i];

  realft( &fData[-1], n, 1);   /* realft expects arrays with range 1..n */

  for (i = nKeep; i < n; i++) /* zero high frequency components to smooth */
    fData[i] = 0;

  realft( &fData[-1], n, -1);  /* realft expects arrays with range 1..n */

  midPoint = 2.*fData[n/2]/(double)n;

  return(midPoint);
} /* end of medianFftValue() */
 
char * fftSmoothF( float data[], long n, long nKeep)
/* fftSmooth flattens out a band pass, removing spikes but keeping  */
/* the general shape */
{ long i = 0, nKeep2 = nKeep/2;
  double tempD[MAXTEMP], outD[MAXTEMP], factor = 1.;

  for (i = 0; i < n; i++) 
    tempD[i] = data[i];

  for (i = 1; i < NEDGE; i++) {             /* smooth ends to zero */
    factor = exp(-0.1*(double)(NEDGE-i));
    tempD[i]   *= factor;
    tempD[n-i] *= factor;
  }
  tempD[0] = tempD[n-1] = 0.;

  for (i = nKeep2; i < n-nKeep2; i++) 
    tempD[i] -= (0.5*(data[i-nKeep2]+data[i+nKeep2]));

  for (i = 0; i < nKeep2; i++)
    tempD[i] -= tempD[i+nKeep2];

  for (i = nKeep2+1; i < n-nKeep2; i++)
    tempD[i] -= tempD[i-nKeep2];

  /* reject high peaks in input data */
  medianFilter( (int)n, (int)nKeep, tempD, outD);

  for (i = 0; i < n; i++) 
    data[i] -= outD[i];

  realft( &data[-1], n, 1);   /* realft expects arrays with range 1..n */

  for (i = nKeep; i < nKeep+NEDGE; i++) /* zero high frequency components */
    data[i] *= exp(-0.1*(double)(i-nKeep));

  for (i = nKeep+NEDGE; i < n; i++) /* zero high freq. components to smooth */
    data[i] = 0;

  realft( &data[-1], n, -1);  /* realft expects arrays with range 1..n */

  factor = 2./(double)n;

  for (i = 0;  i < n;  i++)
    data[i] *= factor;

  return(NULL);
} /* end of fftSmooth() */
 
char * medianBaseline( float data[], long n, long medianWidth)
/* medianBaseline flattens out a band pass, removing lumps wider than width*/
{ long i = 0;
  double tempD[MAXTEMP], outD[MAXTEMP];

  for (i = 0; i < n; i++) 
    tempD[i] = data[i];

  medianFilter( n, medianWidth/2, tempD, outD);

  for (i = 0; i < n; i++) 
    data[i] -= outD[i];

  return(NULL);
} /* end of medianBaseline() */
 
char * aveRmsRange( float data[], long aStart, long aEnd, 
       long bStart, long bEnd, double * aveOut, double * rmsOut)
/* aveRmsRange() is a floating point wrapper for calcAveRmsRange() */
{ long i = 0;
  double tempD[MAXTEMP];

  for (i = aStart; i < aEnd; i++)  /* transfer*/  
    tempD[i] = data[i];
    
  for (i = bStart; i < bEnd; i++)  /* transfer*/
    tempD[i] = data[i];

  return( calcAveRmsRange( tempD, aStart, aEnd, bStart, bEnd, 
			   aveOut, rmsOut));
} /* end of aveRmsRange() */

#define NRMS 16

double medianRms( long n, float data[])
/* medianRms() divides the data array into blocks and computes the RMS for */
/* for each block.  The median of the blocks of the RMS values is returned */
/* medianRms() gives a representiative RMS value in the presences of a few */
/* strong signals in the spectra                                           */
{ long i = 0, iRms = 0, nBlock = 0, j = 0;
  double rmss[NRMS], anRms = 0;
  double tempD[MAXTEMP];

  if (n < 128) {
    for (i = 0; i < n; i++)  /* transfer*/  
      tempD[i] = data[i];
    return( calcRMS( (int)n, tempD));
  }

  nBlock = n / NRMS;
    
  for (iRms = 0; iRms < NRMS; iRms++) {
    j = 0;
    for (i = nBlock*iRms; i < nBlock*(iRms+1); i++) { /* transfer*/  
      tempD[j] = data[i];
      j++;
    }
    rmss[iRms] = calcRMS( (int)j, tempD);
  }

  anRms = medianSelect( (unsigned long)NRMS/2, (unsigned long)NRMS, rmss);

  return( anRms);
} /* end of medianRms() */
     
#define SMALL 1.0E-20

char * medianAveRmsMinMax( long n, double a[], 
			   double * oMedian, double * oAve, double * oRms, 
			   double * oMin, double * oMax)
/* utility to compute a statisical summary of an input double array() */
{ double sumf = a[0], sumff = a[0]*a[0], rms = 0.0, 
    aMin = a[0], aMax = a[0];
  long i;

  if (n < 2)                                /* if not enough data */
    return("NOT enought data for statistics");

  for (i=1; i < n; i++) {                   /* for all points */
    sumf  += a[i];                          /* do sums */
    sumff += a[i]*a[i];
    if (a[i] > aMax)
      aMax = a[i];
    else if (a[i] < aMin)
      aMin = a[i];
  } /* end of for all points */
  
  rms = (sumff - (sumf*sumf/(double)n))/((double)n - 1.); 

  if (rms > SMALL)                          /* avoid negative square root */
    rms = sqrt(rms);
  else                                      /* else null return */
    rms = 0.0;

  *oMedian = medianSelect((unsigned long)n/2, (unsigned long)n, a);
  *oAve    = sumf/(double)n;
  *oRms    = rms;
  *oMin    = aMin;
  *oMax    = aMax;
  return(NULL);
} /* end of medianAveRmsMinMax() */
