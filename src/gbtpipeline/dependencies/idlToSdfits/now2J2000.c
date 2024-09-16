/* File now2J2000.c, version 1.3, released  03/10/09 at 09:59:27 
   retrieved by SCCS 14/04/23 at 15:51:21     

%% function to precess (etc.) J2000 co-ords to given epoch

:: GBES-C position point J2000 epoch apparent
 
History:
  021206 GIL - fix type for positionInvese()
  010320 GIL - new function now2J2000 that directly calculates J2000
  010319 GIL - fix prototype of nPrint
  000414 GIL - do not print if near the north pole, large changes are expected
  980828 GIL - fix initializion
  970908 GIL - initialize i for case of dec at north pole
  941021 GIL - limit to positive ra
  940818 GIL - fix false solutions, modulo 2PI
  940426 GIL - based on obsposn.c, which calculates radec of date from J2000
              
DESCRIPTION:
now2J2000 transforms an input ra, dec of date to J2000 ra and dec.
This function is implimented as an iterative calculation based on 
obsposn which calculates the inverse function.

Tests indicate that the accuracy of this function is better than 1 arc second.
*/
#include "stdio.h"	/* add io definitions */
#include "math.h"	/* add io definitions */
#include "MATHCNST.H"	/* define TWOPI */

/* externals */
void obsposn (long mjd, double utc, double ra2000, double dec2000, 
	      double * ranow, double * decnow);
extern double angularDistance( double raA, double decA, 
			       double raB, double decB);

extern char * rad2str( double, char *, char *);
extern char * mjd2str( long, char *);
extern void matinvert (double inA[3][3], double outB[3][3]); 
/* externals */
extern void rotate3 (double *, double matrix[3][3], double *);
extern void dircos (double, double, double *);
extern void aberrat (double, double, double *, double *);
extern void nutate (double, double *, double *);
extern void rectpol (double dir_vector[], double * ra, double * dec);
extern double obliq (double);

/* internals */

void precess2Now (
double t_now,        /* target time with respect to J2000 in Julian centuries */
double pos_mean[3],  /* (input) position vector:  direction cosines
			of MEAN position at target epoch */

double pos_J2000[3]) /* (output) position vector:  direction cosines
			of position at standard epoch J2000 */
/*
* Definition of t_now:
*    ([Julian Day Number of target epoch] - 2451545.0) / 36525.0
*    where the JD number includes the fractional day since 12h TDB.
*
* SOURCES:
*    United States Naval Observatory:  Circular # 163 (1981 Dec 10), page A2.
*    National Radio Astronomy Observatory:  VLA Computer Memorandum # 105
*         (1973 Aug 9), page 3.
* TESTED:  86jan07, D. King.  Seems to do reasonable things to input positions;
*          but should be tested against published J2000 positions of
*          stars listed in the "Astronomical Almanac."
*  86feb04, D. King:
*  The matrices produced by this algorithm were pre-multiplied by
*  the nutation matrices produced by the "exact" algorithm in "NUTROTN."
*  The results were compared with those in "The Astronomical Almanac" for
*  1985 January 0 thru February 15, plus a few more randomly chosen dates
*  in 1985.
*
*  For the VAX (50+ bits of precision) four errors of plus or minus 1e-8
*  were seen in off-diagonal elements.  These errors are presumed to be due to
*  differences in computational precision and round-off from the Almanac.
*  For more information, see the Test Status for 86feb04 in "nutrotn.c".
-*/
{
    double zeta_A = 0;   /*  }                                          */
    double zed_A  = 0;   /*  }-  Equatorial precession parameters       */
    double theta_A= 0;   /*  }                                          */
    double sin_zeta = 0;
    double cos_zeta = 0;
    double sin_zed  = 0;
    double cos_zed  = 0;
    double sin_theta= 0;
    double cos_theta= 0;
    double temp = 0;
    double tnow_sq = t_now * t_now;
    double tnow_cu = tnow_sq * t_now;
    double rot_mat[3][3], inv_mat[3][3];
 
    /*
    **  Calculate the rotation angles between the J2000 reference system
    **  and the mean equinox and equator at time t_now, in arc-sec.
    **    SOURCE:  USNO circ. # 163 (1981dec10), page A2
     */
    temp    = 2306.2181 * t_now;
    zeta_A  = temp               +  0.30188 * tnow_sq  +  0.017998 * tnow_cu;
    zed_A   = temp               +  1.09468 * tnow_sq  +  0.018203 * tnow_cu;
    theta_A = 2004.3109 * t_now  -  0.42665 * tnow_sq  -  0.041833 * tnow_cu;
 
    /*
    **  Convert to radians and take sines and cosines
     */
    zeta_A  *= RAD_ASEC;
    zed_A   *= RAD_ASEC;
    theta_A *= RAD_ASEC;
 
    sin_zeta = sin (zeta_A);
    cos_zeta = cos (zeta_A);
 
    sin_zed = sin (zed_A);
    cos_zed = cos (zed_A);
 
    sin_theta = sin (theta_A);
    cos_theta = cos (theta_A);
 
    /*
    **  Construct the rotation matrix
    **    SOURCE:  VLA Computer Memo #105 (1973aug09), pages 3-4
    **      (Notes:  Indices run 0-2, not 1-3, due to C language conventions.
    **               This is actually the transpose of the reference matrix.)
     */
    temp = cos_theta * cos_zed;
    rot_mat[0][0] =  temp * cos_zeta  -  sin_zeta * sin_zed;
    rot_mat[0][1] = -temp * sin_zeta  -  cos_zeta * sin_zed;
    rot_mat[0][2] = -sin_theta * cos_zed;
 
    temp = cos_theta * sin_zed;
    rot_mat[1][0] =  temp * cos_zeta  +  sin_zeta * cos_zed;
    rot_mat[1][1] = -temp * sin_zeta  +  cos_zeta * cos_zed;
    rot_mat[1][2] = -sin_theta * sin_zed;
 
    rot_mat[2][0] =  cos_zeta * sin_theta;
    rot_mat[2][1] = -sin_zeta * sin_theta;
    rot_mat[2][2] =  cos_theta;

    matinvert ( rot_mat, inv_mat);  
    /*
    **  Rotate the co-ordinates from J2000 to mean at t-now.
     */
    rotate3 (pos_J2000, inv_mat, pos_mean);
} /* end of precess2Now */

#define APPROXIMATE  1       /*  Use the APPROXIMATE MATRIX          */
 
/*++****************************************************************************
*/
char * nutrotnInverse (
double epsilon,      /* mean obliquity in radians */
double dpsi,         /* nutation in longitude in radians */
double deps,         /* nutation in obliquity in radians */
double true_posn[3], /* (input) direction cosines of mean position of date */
double mean_posn[3]) /* (output) direction cosines of true (nutated) position */
/*
* Note that "true position" does not include the "E-terms of aberration,"
* in accordance with J2000 conventions.
*
* Both approximate and exact algorithms for the nutation matrix are
* provided.  The approximate method works better with the 24-bit precision
* of Alcyon C, and is acceptable on the VAX (see Test Status, below).
*
* This version (1.0) uses the approximate method.  To use the exact
* method, parameter APPROXIMATE must be undefined.
*
* TEST STATUS:  86feb04, D. King:
* The matrices produced by these algorithms were post-multiplied by the 
* precession matrices produced by the algorithm used in "PRCESJ2."  The 
* results were compared with those in "The Astronomical Almanac" for 1985 
* January 0 thru February 15, plus a few more randomly chosen dates in 1985.
*
* For the VAX (50+ bits of precision) four errors of plus or minus 1e-8 were 
* seen in off-diagonal elements, when the exact algorithm for the nutation 
* matrix was used.  These errors are presumed to be due to differences in 
* computational precision and round-off from the Almanac.  When the approximate 
* algorithm was used on the VAX, most dates had one or two errors of 1e-8, 
* including a few in the diagonal elements.  The approximate method thus seems 
* adequate if a nutation matrix precision of 1e-8 is adequate.
*
* For the VME/10 using Alcyon C (24 bits of precision),  errors of up to 15e-8 
* were seen in the diagonal elements, when the approximate algorithm for the 
* nutation matrix was used.  Off-diagonal elements showed about one error per 
* matrix, usually of only 1e-8, and never more than 5e-8.  Since 24 bits can 
* express a number of order 1.0 to only about 6e-8, these results seem 
* reasonable.
*
* When the exact algoritm was used with Alcyon C, results were worse.  Errors 
* in the diagonal elements were larger, up to 23e-8.  In addition, elements 
* 2,3 and 3,2 were always in error -- usually more than 5e-8, and sometimes in 
* excess of 20e-8.  The reason for the poorer performance of the exact 
* algorithm is unknown.  It was not possible to get similar results on the 
* VAX by declaring the appropriate variables to be 'float', (although accuracy 
* of the final digit of all elements was degraded).  (Perhaps the Alcyon sine 
* and cosine routines are not good enough.)
-*/
{
    double nutmatrix[3][3];   /*  rotation matrix for nutation */
    double nutInverse[3][3];  /*  inverse rotation matrix for nutation */
    double temp = 0;
 
    /*
    **    Construct the rotation matrix
    **      Note that subscripts run 0-2, rather than 1-3, because of
    **      the usual C language conventions.
    */
 
#ifdef APPROXIMATE
    /*  ----APPROXIMATE MATRIX----
     **  SOURCE:  Taff, L. G.  1981.  "Computational Spherical Astronomy"
     **           John Wiley & Sons, page 81.
     */
    double cos_eps = cos (epsilon);
    double sin_eps = sin (epsilon);
    double deps_sq = deps * deps;
    double dmu;
    double dNU;                 /* upper case NU to distinguish from mu */
 
    dmu = dpsi * cos_eps;
    dNU = dpsi * sin_eps;
 
    nutmatrix [0][0] = 1.0 - 0.5 * dpsi * dpsi;
    nutmatrix [1][1] = 1.0 - 0.5 * (deps_sq - dmu * dmu);
    nutmatrix [2][2] = 1.0 - 0.5 * (deps_sq + dNU * dNU);
 
    nutmatrix [0][1] = -dmu;
    nutmatrix [1][0] =  dmu - deps * dNU;
 
    nutmatrix [0][2] = -dNU;
    nutmatrix [2][0] =  dNU - deps * dmu;
 
    temp = -0.5 * dmu * dNU;
    nutmatrix [1][2] = temp - deps;
    nutmatrix [2][1] = temp + deps;
 
#else
    /*  ----EXACT MATRIX----
     **  SOURCE:  Emerson, B. 1973.  Royal Obs Bul 178, pg 299-300.
     */
    double eps0;               /* MEAN obliquity */
    double cos_eps;
    double sin_eps;
    double cos_eps0;
    double sin_eps0;
    double cos_dpsi;
    double sin_dpsi;

    sin_eps0 = sin (eps0);
    cos_eps0 = cos (eps0);

    epsilon = eps0 + deps;     /* 'epsilon' is now TRUE obliquity */
    cos_eps = cos (epsilon);
    sin_eps = sin (epsilon);
 
    sin_dpsi = sin (dpsi);
    cos_dpsi = cos (dpsi); 

    nutmatrix [0][0] = cos_dpsi;

    nutmatrix [0][1] = -sin_dpsi * cos_eps0;
    nutmatrix [1][0] =  sin_dpsi * cos_eps;

    nutmatrix [0][2] = -sin_dpsi * sin_eps0;
    nutmatrix [2][0] =  sin_dpsi * sin_eps;

    temp = cos_dpsi * cos_eps0;
    nutmatrix [1][1] = temp * cos_eps + sin_eps0 * sin_eps;
    nutmatrix [2][1] = temp * sin_eps - sin_eps0 * cos_eps;

    temp = cos_dpsi * sin_eps0;
    nutmatrix [1][2] = temp * cos_eps - cos_eps0 * sin_eps;
    nutmatrix [2][2] = temp * sin_eps + cos_eps0 * cos_eps;
#endif
    /*
    **  Rotate the mean co-ordinates to get the true position.
    */
    matinvert( nutmatrix, nutInverse);
    rotate3 (mean_posn, nutInverse, true_posn);
    return(NULL);
} /* end of nutrotnInverse () */


char * aberratInverse(
double tnow,             /* time relative to J2000, in Julian centuries */
double epsilon,          /* mean obliquity of the ecliptic at t_now */
double apparentPosn[3],  /* (input) dir-cosines of aberrated position */
double meanPosn[3])      /* (output) dir-cosines of position to be aberrated */
{ long i = 0;
  double tempPosn[3] = {0, 0, 0}, normFactor = 0;

  aberrat (tnow, epsilon, apparentPosn, tempPosn);

  /* assuming aberration is small, the aberrating backwards is just opposite */
  for (i = 0; i < 3; i++) {
    meanPosn[i] = apparentPosn[i] - (tempPosn[i] - apparentPosn[i]);
    normFactor += (meanPosn[i] * meanPosn[i]);
  }
  if (normFactor <= 0) {
    fprintf( stderr, "in aberateInverse: error normalizing: %10.3e\n",
	     normFactor);
    return("Error Normalizing");
  }

  normFactor = sqrt (normFactor);

  for (i = 0; i < 3; i++)
    meanPosn[i] /= normFactor;
  return(NULL);
} /* end of aberateInverse() */

/*++***************************************************************************
*/
char * positionInverse (
double raNow,     /* J2000 right ascension */
double decNow,    /* J2000 declination */
double t_now,        /* current time wrt J2000 in Julian centuries */
double posJ2000[3])   /* (output) direction cosines of
			current corrected position */
/*
* RETURNS equation of equinoxes (delta _psi * cos (mean_obliquity)),
*              in seconds of time
*
* This routine does NOT include calculations for proper motion or parallax.
-*/
{
    double posMean[3];       /* dir-cosines of mean position of date */
    double posAberrated[3];  /* d-c of mean pos of date, corrected for
                                aberration and relativistic deflection */
    double posApparent[3];   /* d-c of apparent (geocentric) position */
    double mean_obliq = 0;   /* mean obliquity of date */
    double delta_psi = 0;    /* nutation in longitude */
    double delta_eps = 0;    /* nutation in obliquity */
 
    /* convert input ra, dec to direction cosines */
    dircos (raNow, decNow, posApparent);

    /* correct for aberration and general relativistic deflection */
    mean_obliq = obliq (t_now);

    /* un-correct for nutation */
    nutate (t_now, &delta_psi, &delta_eps);
    nutrotnInverse (mean_obliq, delta_psi, delta_eps, posApparent, 
		    posAberrated);

    aberratInverse (t_now, mean_obliq, posAberrated, posMean);

    /* precess from J2000 to t_now */
    precess2Now (t_now, posMean, posJ2000);

    return (NULL);
} /* end of positionInverse() */

char * now2J2000 (long mjd, double utc, double raNow, double decNow, 
	      double * raJ2000, double * decJ2000)
{    /***  calc epoch wrt J2000 in Julian centuries  ***/
    double mjd2000 = 51544.5;	             /* mjd of J2000 (2000 Jan 1.5) */
    double tNow = 0;
    double posJ2000[3] = {0, 0, 0};	/* posn-vector of apparent co-ords */


    tNow = (((double)mjd - mjd2000) + (utc / TWOPI))/(double)JUL_CENT;

    /***  get current apparent position into posvectr  ***/
    positionInverse (raNow, decNow, tNow, posJ2000);

    /***  convert posvectr to polar co-ords  ***/
    rectpol (posJ2000, raJ2000, decJ2000);
    return(NULL);
} /* end of obsposn() */






