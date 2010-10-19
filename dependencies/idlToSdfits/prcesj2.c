/*  @(#)prcesj2.c  version 1.1  created 90/04/02 14:32:09
                fetched from SCCS 95/11/13 10:24:26
%% function for general precession FROM standard epoch J2000 TO arbitrary date.
%% MV331 functions to read and write to VME Bus memory
LANGUAGE: C
ENVIRONMENT: Any
:: position pointing precess J2000
*/
#include "MATHCNST.H"

/* externals */
void rotate3 ();
double sin ();
double cos ();

/*++****************************************************************************
*/
void prcesj2 (t_now, pos_J2000, pos_mean)
double t_now;        /* target time with respect to J2000 in Julian centuries */
double pos_J2000[3]; /* (input) position vector:  direction cosines
			of position at standard epoch J2000 */
double pos_mean[3];  /* (output) position vector:  direction cosines
			of MEAN position at target epoch */
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
    double zeta_A;       /*  }                                          */
    double zed_A;        /*  }-  Equatorial precession parameters       */
    double theta_A;      /*  }                                          */
    double sin_zeta;
    double cos_zeta;
    double sin_zed;
    double cos_zed;
    double sin_theta;
    double cos_theta;
    double temp;
    double tnow_sq = t_now * t_now;
    double tnow_cu = tnow_sq * t_now;
    double rot_mat[3][3];
 
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
 
    /*
    **  Rotate the co-ordinates from J2000 to mean at t-now.
     */
    rotate3 (pos_mean, rot_mat, pos_J2000);
}
