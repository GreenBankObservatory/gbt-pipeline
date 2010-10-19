/*  @(#)nutate.c  version 1.2  created 95/11/24 08:16:16
    %% funtion to calc nutation in longitude & obliquity for given time 
    LANGUAGE: C
    ENVIRONMENT: Any
*/

/* includes */
#include "math.h"
#include "MATHCNST.H"
#include "vlb.h"

/*******************************************************************************
*/
void nutate
    (
    double t_now,	/* time with respect to J2000, Julian Centuries */
    double *delt_psi,	/* returned nutation in longitude at t_now */
    double *delt_eps	/* returned nutation in obliquity at t_now */
    )
/*
 * Delta-psi and delta-epsilon are calculated using the full series expansion.
 *
 * Definition of t_now:
 *    ([Julian Day Number of target epoch] - 2451545.0) / 36525.0
 *    where the JD number includes the fractional day since 12h TDB.
 *
 * TESTING: Version 1.0 tested 16 Jan 86, by D. King:
 * Compiled on VAX (50+ bits of precision for type double).
 * Ran for calendar year 1985, for 0 hours of each day.  The output values 
 *  of delta-psi and delta-epsilon were converted to arc-seconds and rounded 
 *  to three decimal places.
 * Manually compared output with "The Astronomical Almanac, 1985."
 * NO ERRORS were detected.
 *
 * Compiled on VME/10 using Alcyon C (24 bits of precision for doubles).
 * Ran for calendar year 1985, as above.  Used file compare utility to look 
 * for differences from VAX output.  Found 25 ERRORS of plus or minus 1 in the 
 * least significant digit(0".001); 16 errors were in delta-psi and 9 in 
 * delta-epsilon.
 *
 * Ran both VAX and VME/10 for calendar years 1995, 2000, 2005, and 2025, and 
 * file-compared to look for discrepancies.  Errors never exceeded 0".001, 
 * and in only two cases (both in year 2025) were delta-psi and delta-epsilon 
 * both in error.
 * Assuming that the VAX output was completely accurate, the errors in the 
 * 24-bit Alcyon output are given by the following table.
 *
 *               YEAR   Total   Errors    Errors
 *                      Errors  in Psi    in Eps
 *               - - - - - - - - - - - - - - - -
 *               1985     25      16         9
 *               1995      8       6         2
 *               2000      1       1         0
 *               2005     11       9         2
 *               2025     50      35        15
 *
 * The errors are assumed to arise mostly in the calculation of the three 
 * fundamental arguments (l, F, and D) which have about 1300 revolutions 
 * per century.  It is thus not surprising that the number of errors 
 * increases with the distance from year 2000.  Hopefully, we will have a 
 * compiler with more than 24 bits of precision by the time we reach 2025.
 */
{
/*
 *  COEFFICIENTS FOR CONSTRUCTING THE FUNDAMENTAL ARGUMENTS (l, l', F, D,
 *  and Omega).  For example:
 *      l = farg_coef[0][0]  +  (farg_rev[0] + farg_coef[0][1]) * T
 *          +  farg_coef[0][2] * T * T  +  farg_coef[0][3] * T * T * T
 *  (Note that the number of integral revolutions per Julian century
 *  has been separated out into its own array, for computational
 *  convenience.)
 *
 *  SOURCE:  USNO Circular #163 (1981dec10), page A3
 */
 
    static double farg_coef[5][4] =
	{
        {  485866.733,   715922.633,   31.310,   0.064 },  /*  l     */
        { 1287099.804,  1292581.224,   -0.577,  -0.012 },  /*  l'    */
        {  335778.877,   295263.137,  -13.257,   0.011 },  /*  F     */
        { 1072261.307,  1105601.328,   -6.891,   0.019 },  /*  D     */
        {  450160.280,  -482890.539,    7.455,   0.008 },  /*  Omega */
	};

    static double farg_revs[5] = { 1325.0,  99.0,  1342.0,  1236.0,  -5.0 };
 
/*
 *  NUTATION SERIES COEFFICIENTS
 *    SOURCE:  USNO Circular # 163 (1981dec10), pages A4 - A6.
 */
 
#define NTERMS     106       /* number of terms in the nutation series */
#define LAST_T_TERM 39       /* last term with nonzero value for either
                                d_lngtd or d_obliq */
 
 
    static double lngtd[NTERMS] =
    { /*            0     1     2     3     4     5     6     7     8     9
             */
      /*   0 */     -171996,       2062,         46,         11,         -3,
      /*   5 */          -3,         -2,          1,     -13187,       1426,
      /*  10 */  -517,  217,  129,   48,  -22,   17,  -15,  -16,  -12,   -6,
      /*  20 */    -5,    4,    4,   -4,    1,    1,   -1,    1,    1,   -1,
      /*  30 */ -2274,  712, -386, -301, -158,  123,   63,   63,  -58,  -59,
      /*  40 */   -51,  -38,   29,   29,  -31,   26,   21,   16,  -13,  -10,
      /*  50 */    -7,    7,   -7,   -8,    6,    6,   -6,   -7,    6,   -5,
      /*  60 */     5,   -5,   -4,    4,   -4,   -3,    3,   -3,   -3,   -2,
      /*  70 */    -3,   -3,    2,   -2,    2,   -2,    2,    2,    1,   -1,
      /*  80 */     1,   -2,   -1,    1,   -1,   -1,    1,    1,    1,   -1,
      /*  90 */    -1,    1,    1,   -1,    1,    1,   -1,   -1,   -1,   -1,
      /* 100 */    -1,   -1,   -1,    1,   -1,    1
     };
 
    static double d_lngtd[LAST_T_TERM] =
    { /*            0     1     2     3     4     5     6     7     8     9
             */
      /*   0 */ -174.2, 0.2,    0,    0,    0,    0,    0,    0, -1.6, -3.4,
      /*  10 */   1.2, -0.5,  0.1,    0,    0, -0.1,    0,  0.1,    0,    0,
      /*  20 */     0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
      /*  30 */  -0.2,    1, -0.4,    0,    0,    0,    0,  0.1, -0.1
    };
 
    static double obliq[NTERMS] =
    { /*            0     1     2     3     4     5     6     7     8     9
             */
      /*   0 */       92025,       -895,        -24,          0,          1,
      /*   5 */           0,          1,          0,       5736,         54,
      /*  10 */   224,  -95,  -70,    1,    0,    0,    9,    7,    6,    3,
      /*  20 */     3,   -2,   -2,    0,    0,    0,    0,    0,    0,    0,
      /*  30 */   977,   -7,  200,  129,   -1,  -53,   -2,  -33,   32,   26,
      /*  40 */    27,   16,   -1,  -12,   13,   -1,  -10,   -8,    7,    5,
      /*  50 */     0,   -3,    3,    3,    0,   -3,    3,    3,   -3,    3,
      /*  60 */     0,    3,    0,    0,    0,    0,    0,    1,    1,    1,
      /*  70 */     1,    1,   -1,    1,   -1,    1,    0,   -1,   -1,    0,
      /*  80 */    -1,    1,    0,   -1,    1,    1,    0,    0,   -1,    0,
      /*  90 */     0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
      /* 100 */     0,    0,    0,    0,    0,    0
    };
 
    static double d_obliq[LAST_T_TERM] =
    { /*            0     1     2     3     4     5     6     7     8     9
             */
      /*   0 */   8.9,  0.5,    0,    0,    0,    0,    0,    0, -3.1, -0.1,
      /*  10 */  -0.6,  0.3,    0,    0,    0,    0,    0,    0,    0,    0,
      /*  20 */     0,    0,    0,    0,    0,    0,    0,    0,    0,    0,
      /*  30 */  -0.5,    0,    0, -0.1,    0,    0,    0,    0,    0
    };
 
/*
 *  MULTIPLES OF FUNDAMENTAL ARGUMENTS
 *       argument(term) = sum_over_i(farg_mult(i, term) * fund_arg(i))
 *    SOURCE:  USNO Circular # 163 (1981dec10), pages A4 - A6.
 */
 
    static int farg_mult[5][NTERMS] =
    {
      /*          0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
         l_args       */
      /*  00 */ { 0, 0,-2, 2,-2, 1, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0,-2,
      /*  20 */   0, 2, 0, 1, 2, 0, 0, 0,-1, 0, 0, 1, 0, 1, 1,-1, 0, 1,-1,-1,
      /*  40 */   1, 0, 2, 1, 2, 0,-1,-1, 1,-1, 1, 0, 0, 1, 1, 2, 0, 0, 1, 0,
      /*  60 */   1, 2, 0, 1, 0, 1, 1, 1,-1,-2, 3, 0, 1,-1, 2, 1, 3, 0,-1, 1,
      /*  80 */  -2,-1, 2, 1, 1,-2,-1, 1, 2, 2, 1, 0, 3, 1, 0,-1, 0, 0, 0, 1,
      /* 100 */   0, 1, 1, 2, 0, 0 },
      /*          0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
         lprime_args  */
      /*  00 */ { 0, 0, 0, 0, 0,-1,-2, 0, 0, 1, 1,-1, 0, 0, 0, 2, 1, 2,-1, 0,
      /*  20 */  -1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      /*  40 */   0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1,-1, 0, 0, 0, 0, 0, 0, 0,
      /*  60 */  -1, 0, 1, 0, 0, 1, 0,-1,-1, 0, 0,-1, 1, 0, 0, 0, 0, 0, 0, 0,
      /*  80 */   0, 0, 0, 1, 0, 0, 0,-1, 0, 0, 0, 0, 0, 0, 1,-1, 0, 0, 1, 0,
      /* 100 */  -1, 1, 0, 0, 0, 1 },
      /*          0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
         F_args       */
      /*  00 */ { 0, 0, 2,-2, 2, 0, 2,-2, 2, 0, 2, 2, 2, 0, 2, 0, 0, 2, 0, 0,
      /*  20 */   2, 0, 2, 0, 0,-2,-2, 0, 0, 2, 2, 0, 2, 2, 0, 2, 0, 0, 0, 2,
      /*  40 */   2, 2, 0, 2, 2, 2, 2, 0, 0, 2, 0, 2, 2, 2, 0, 2, 0, 2, 2, 0,
      /*  60 */   0, 2, 0,-2, 0, 0, 2, 2, 2, 0, 2, 2, 2, 2, 0, 0, 0, 2, 0, 0,
      /*  80 */   2, 2, 0, 2, 2, 2, 4, 0, 2, 2, 0, 4, 2, 2, 2, 0,-2, 2, 0,-2,
      /* 100 */   2, 0,-2, 0, 2, 0 },
      /*          0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
         D_args       */
      /*  00 */ { 0, 0, 0, 0, 0,-1,-2, 0,-2, 0,-2,-2,-2,-2,-2, 0, 0,-2, 0, 2,
      /*  20 */  -2,-2,-2,-1,-2, 2, 2, 0, 1,-2, 0, 0, 0, 0,-2, 0, 2, 0, 0, 2,
      /*  40 */   0, 2, 0,-2, 0, 0, 0, 2,-2, 2,-2, 0, 0, 2, 2,-2, 2, 2,-2,-2,
      /*  60 */   0, 0,-2, 0, 1, 0, 0, 0, 2, 0, 0, 2, 0,-2, 0, 0, 0, 1, 0,-4,
      /*  80 */   2, 4,-4,-2, 2, 4, 0,-2,-2, 2, 2,-2,-2,-2, 0, 2, 0,-1, 2,-2,
      /* 100 */   0,-2, 2, 2, 4, 1 },
      /*          0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
         Omega_args   */
      /*  00 */ { 1, 2, 1, 0, 2, 0, 1, 1, 2, 0, 2, 2, 1, 0, 0, 0, 1, 2, 1, 1,
      /*  20 */   1, 1, 1, 0, 0, 1, 0, 2, 1, 0, 2, 0, 1, 2, 0, 2, 0, 1, 1, 2,
      /*  40 */   1, 2, 0, 2, 2, 0, 1, 1, 1, 1, 0, 2, 2, 2, 0, 2, 1, 1, 1, 1,
      /*  60 */   0, 1, 0, 0, 0, 0, 0, 2, 2, 1, 2, 2, 2, 1, 1, 2, 0, 2, 2, 0,
      /*  80 */   2, 2, 0, 2, 1, 2, 2, 0, 1, 2, 1, 2, 2, 0, 1, 1, 1, 2, 0, 0,
      /* 100 */   1, 1, 0, 0, 2, 0 },
      /*          0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
             */
    };

    double fund_arg[5];      /* l, l_prime, F, D, Omega */
    double t_power[4];
    double psi;              /*  holds partial sum of delta_psi */
    double eps;              /*  holds partial sum of delta_epsilon */
    double argument;         /*  argument of nutation series term */
    int i, j;                /*  loop indices */

    /* calculate the fundamental arguments for time t_now, reduced to
    the interval 0 <= arg < TWOPI */
    t_power[0] = 1.0;
    t_power[1] = t_now;
    t_power[2] = t_now * t_now;
    t_power[3] = t_power[2] * t_now;
 
    for (i = 0; i < 5; i++)
	{
        double x = 0.0, y;

        for (j = 0; j < 4; j++)
            x += farg_coef[i][j] * t_power[j];
	y = farg_revs[i] * t_now;
	y = y - (long)y;      /* get y fractional part w/ same sign */
        x = x * RAD_ASEC + y * TWOPI;
	while (x < 0)         /* make 0 <= x < TWOPI */
	    x += TWOPI;
	while (x >= TWOPI)
	    x -= TWOPI;
	fund_arg[i] = x;
	}
 
    /* calculate the nutation series
    Since all time_dependent terms are zero after term 39 (subscript
    38, in C-language conventions), the summation is broken into
    two parts, to speed the computations. */
    psi = 0.0;
    eps = 0.0;
    for (i = 0; i < LAST_T_TERM; i++)
	{
	/* calculate the actual argument for the current term */
        argument = 0.0;
        for (j = 0; j < 5; j++)
            argument += farg_mult[j][i] * fund_arg[j];

        /* sum the series */
        psi += (lngtd[i] + d_lngtd[i] * t_now) * sin (argument);
        eps += (obliq[i] + d_obliq[i] * t_now) * cos (argument);
	}
    for ( ; i < NTERMS; i++)
	{
        argument = 0.0;
        for (j = 0; j < 5; j++)
            argument += farg_mult[j][i] * fund_arg[j];
        psi += lngtd[i] * sin (argument);
        eps += obliq[i] * cos (argument);
	}
 
    /* psi and eps are in units of 0.0001 arc-second
    convert to radians and put them into the caller's variables */
    *delt_psi = psi * 0.0001 * RAD_ASEC;
    *delt_eps = eps * 0.0001 * RAD_ASEC;
}
