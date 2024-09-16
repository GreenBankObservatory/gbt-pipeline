/* File adjust3Level.c, version 1.2, released  01/12/28 at 14:12:21 
   retrieved by SCCS 14/04/23 at 15:51:06     

%% function to calculate velocites relative to a direction

:: GBES-C position point J2000 epoch apparent
 
History:
  011218 GIL remove printf
  011031 GIL initial version
              
DESCRIPTION:
adjust3Level() calculates a scale factor based on the
auto-correlation value from the 3 level spectrometer data.
*/
#include "stdio.h"	/* add io definitions */
#include "math.h"	/* add mathmatics definitions */
#include "MATHCNST.H"	/* define TWOPI */
#include "STDDEFS.H"	/* define TWOPI */

/* externals */
extern double pow3lev(double zho);
extern double linearFit(double x[], double y[], int ndata, double *a,
			double *b, double *siga, double *sigb);

/* internals */
#define TRUEFACTOR 0
#define ZEROFACTOR 1
#define VANVFACTOR 2
#define SIZEFACTOR 3

char * adjust3Level ( double zeroLag, double * gainFactor)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* adjust3Level() uses values from Langston and Lacasse 01 March 8 to adjust */
/* the power level correction for 3 level spectrometer sampling.             */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long nAdjustments = 32, i = 0, j = 0, ndata = 0;
  static long printCount = 0; 
  double xs[4], ys[4], a = 0, b = 0, siga = 0, sigb = 0,
    levelAdjustments[] = {
    0.1259 ,      0.0615 ,     0.1071 ,
    0.1585 ,      0.0929 ,     0.1326 ,
    0.1995 ,      0.1482 ,     0.1791 ,
    0.2512 ,      0.1945 ,     0.2225 ,
    0.3162 ,      0.2530 ,     0.2866 ,
    0.3981 ,      0.3058 ,     0.3571 ,
    0.5012 ,      0.3816 ,     0.4892 ,
    0.6310 ,      0.4351 ,     0.6148 ,
    0.7943 ,      0.4986 ,     0.8179 ,
    1.0000 ,      0.5459 ,     1.0266 ,
    1.2589 ,      0.6066 ,     1.4119 ,
    1.5849 ,      0.6458 ,     1.7730 ,
    1.9953 ,      0.6882 ,     2.3251 ,
    2.5119 ,      0.7212 ,     2.9396 ,
    3.1623 ,      0.7616 ,     4.0664 ,
    3.9811 ,      0.7868 ,     5.1173 ,
    5.0119 ,      0.8098 ,     6.4648 ,
    6.3096 ,      0.8299 ,     8.1056 ,
    7.9433 ,      0.8550 ,    11.2015 ,
    10.0000 ,      0.8703 ,    14.0381 ,
    12.5893 ,      0.8861 ,    18.2496 ,
    15.8489 ,      0.8971 ,    22.3682 ,
    19.9526 ,      0.9128 ,    31.1796 ,
    25.1189 ,      0.9217 ,    38.6594 ,
    31.6228 ,      0.9316 ,    50.8272 ,
    39.8107 ,      0.9381 ,    61.9082 ,
    50.1187 ,      0.9463 ,    82.3070 ,
    63.0957 ,      0.9508 ,    98.0642 ,
    79.4328 ,      0.9553 ,   118.8207 ,
    100.0000 ,      0.9582 ,   136.0584 ,
    125.8925 ,      0.9614 ,   159.1787 ,
    158.4893 ,      0.9628 ,   171.9671};

  for (i = 0; i < nAdjustments; i++) {
    if (levelAdjustments[(i*SIZEFACTOR)+ZEROFACTOR] > zeroLag) 
      break;
  }

  if (i <= 2)
    *gainFactor = levelAdjustments[TRUEFACTOR]/levelAdjustments[VANVFACTOR];
  else if (i >= nAdjustments-3) 
    *gainFactor = 
      levelAdjustments[TRUEFACTOR+((nAdjustments-1)*SIZEFACTOR)]/
      levelAdjustments[VANVFACTOR+((nAdjustments-1)*SIZEFACTOR)];
  else { /* else interpolate */
    for (j=i-2; j < i + 3 && j < nAdjustments; j++) {
      xs[ndata] = pow3lev(levelAdjustments[(j*SIZEFACTOR)+ZEROFACTOR]);
      ys[ndata] = levelAdjustments[TRUEFACTOR+(j*SIZEFACTOR)]/
	levelAdjustments[VANVFACTOR+(j*SIZEFACTOR)];    
      ndata++;
    }
    linearFit( xs, ys, ndata, &a, &b, &siga, &sigb);
    /* now interpolate */
    *gainFactor = a + (b*pow3lev(zeroLag));
  } /* end else between value, interpolate */
 
  if (printCount < 1) {                   /* just print once */
    fprintf ( stderr, 
	    "adjust3Level: %7.3f => %7.3f (a = %7.3f, b = %7.3f)\n", 
	    zeroLag, *gainFactor, a, b);
    printCount++;
  }
  return(NULL);
} /* end of adjust3Level */


