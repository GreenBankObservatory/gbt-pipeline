/*  @(#)nutrotn.c  version 1.1  created 90/04/02 14:35:30
                fetched from SCCS 95/11/13 10:23:48
%% function to rotate the coordinate system to account for nutation
LANGUAGE: C
ENVIRONMENT: Any
:: pointing nutation position
*/

/* externals */
void rotate3 ();
double sin ();
double cos ();

#define APPROXIMATE  1       /*  Use the APPROXIMATE MATRIX          */
 
/*++****************************************************************************
*/
void nutrotn (epsilon, dpsi, deps, mean_posn, true_posn)
double epsilon;      /* mean obliquity in radians */
double dpsi;         /* nutation in longitude in radians */
double deps;         /* nutation in obliquity in radians */
double mean_posn[3]; /* (input) direction cosines of mean position of date */
double true_posn[3]; /* (output) direction cosines of true (nutated) position */
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
    double temp;
 
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
    rotate3 (true_posn, nutmatrix, mean_posn);
}
