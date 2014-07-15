/*  @(#)aberrat.c  version 1.4  created 92/01/03 14:28:56
                fetched from SCCS 99/07/29 10:06:14
%% function to calc aberration and gravitational deflection
LANGUAGE: C
ENVIRONMENT: Any
:: position pointing aberration gravitation deflection
*/
#include "MATHCNST.H"

/* externals */
double dotpr3 ();
double sqrt ();
double sin ();
double cos ();
#define SOLAR_SEMIDIAM  960.0   /* arcseconds */

/*++****************************************************************************
*/
void aberrat (tnow, epsilon, mean_posn, app_posn)
double tnow;             /* time relative to J2000, in Julian centuries */
double epsilon;          /* mean obliquity of the ecliptic at t_now */
double mean_posn[3];     /* dir-cosines of position to be aberrated */
double app_posn[3];      /* (output) dir-cosines of aberrated position */
/*
* The input position, "mean_posn" is corrected for annual aberration,
* including the E-terms, and for the relativistic gravitational deflection
* of light.
*
* The corrected position is placed into the array pointed to by
*"app_posn".  The input position is unchanged.
---
* This is a complete implementation of the Atkinson aberration algorithm
* (Atkinson, R. d'E. 1972, Astron. J. 77, 512).
*
* Differences from Atkinson:
* 1.  The 1976 IAU system of astronomical constants is used.  The values
*     affected in this function are:  Speed of light; Aberration constant;
*     Astronomical unit.
* 2.  A more accurate conversion factor for radians-to-arcseconds is used.
*     (Atkinson uses 206265 exactly; the correct value is 206264.806247...)
* 3.  Equations A14, A15, A20, and A21 are all summed from 1 to 17.
*     (Atkinson sums A14 from 3 to 17, A15 from 3 to 12, and A20 and A21
*     from 1 to 12).
*
* The gravitational deflection calculations are based on VLA Scientific
* Memorandum #122 (C. M. Wade, 1976).  This memo contains an error:  the
* terms in sin(2D) should be omitted (C. Wade, private communication, 1986.
* See also Murray, MNRAS 195, 639-648, 1981.)
*
* Definition of t_now:
* ([Julian Day Number of target epoch] - 2451545.0) / 36525.0
* where the JD number includes the fractional day since 12h TDB.
*
* TEST STATUS:
*  (version 1.0, tested 3 April 86 by D. King.)
*    VAX (50+ bits of precision)
*       The Bessel day numbers C and D were computed by this routine for
*       calendar years 1978 and 1985.  The results were manually compared with
*       those in the "Astronomical Almanac."  For 1978:  errors in C were:
*       67 of -1 milliarcsec, 105 of +1, and 4 of +2; errors in D were: 68
*       of -1 milliarcsec. 1 of -2, 112 of +1, and 2 of +2.  The errors were
*       systematic -- errors of the same sign were grouped together.
*       For 1985 there were only 32 errors in C, 17 of -1 milliarcsec and
*       15 of +1.  For D there were 155 errors, all of -1 milliarcsec.
*
*       An attempt was made to use this routine to compute the Earth's
*       rectangular velocity components, as listed in the 1985 Almanac.
*       Errors in X-dot ranged periodically thru +-200e-9 A.U. per day;
*       in Y-dot from +700 to +1100, and in Z-dot from about 0 to 300.
*       (100e-9 A.U. per day is about 0.12 milliarcsec of aberration.)
*
*       These periodic and systematic offset errors in the velocity
*       components are presumed to be due to perturbations and barycentric
*       terms which were ignored by Atkinson.
*
*    VME/10 (Alcyon C), 24 bits of precision
*       The Bessel C and D day numbers were computed for calendar years
*        1978 and 1985 and compared (by computer) with the results of the VAX
*        runs.  (Note that the comparison was NOT with the Almanac.)
*        about one third of the day numbers matched exactly, the rest had
*        maximum discrepancies of +- 3 milliarcsec, with rms discrepancy
*        of 1.
*
*   The gravitational deflection portion of this routine has NOT yet been
*   tested, due to lack of comparison data.
*
-*/
{
#include "ABPTRB.H"          /* perturbation constants */
 
    double
        d,                   /* days since 1900 Jan 0.5 */
        y,                   /* Julian years since 1900 Jan 0.5 */
        l,                   /* Sun's mean longitude */
        g,                   /* Sun's mean anomaly */
        e,                   /* moon's mean elongation */
        g1,                  /* moon's mean anomaly */
        u,                   /* moon's mean argument of latitude */
        cos_eps = cos (epsilon),  /* cosine of obliquity */
        sin_eps = sin (epsilon),  /* sine of obliquity */
        cnt,                 /* Sun's equation of the center */
        lpl,                 /* lunar perturbation in longitude */
        lpr,                 /*   "        "        "  logarithm of radius */
        dlpr,                /* daily change in lpr */
        dlpl,                /* daily change in lpl */
        dplt,                /* daily change in (?lunar?)
                                      perturbation in latitude */
        rpl,                 /* an intermediate value in the calculation
                                      of planetary perturbations */
        cos_rpl,             /* cosine of rpl */
        sin_rpl,             /* sine of rpl */
        ppl,                 /* planetary perturbation in longitude */
        ppr,                 /*     "           "        " log radius */
        dppl,                /* daily change in ppl */
        dppr,                /* daily change in ppr */
        lgpl,                /* long-period perturbation in longitude */
        sunl,                /* Sun's true longitude (mean equinox of date) */
        cos_sunl,
        sin_sunl,
        sun_posn[3],         /* Sun's true position (direction cosines) */
        pr_dal,              /* perturbation in radial velocity (?) */
        dpr,                 /* radial velocity */
        dpl,                 /* longitudinal velocity */
        vlt,                 /* latitudinal velocity */
        v1, v2, v3,          /* polar velocity components, in 
				        arcsec of aberration */
        gj,                  /* Jupiter's mean anomaly */
        lj,                  /* Jupiter's true longitude */
        gs,                  /* Saturn's mean anomaly */
        ls,                  /* Saturn's true longitude */
        bc,                  /* Barycenter correction to C */
        bd,                  /* Barycenter correction to D */
        eterm,               /* E-term of aberration */
        e1, e2,              /* components of E-term */
        eccentr,             /* eccentricity of Earth's orbit */
        perih,               /* position angle of perihelion */
        ve[3],               /* rectanglular velocity components, including
                                      E-terms, in radians of aberration */
        cos_sundist,         /* cosine of angle between Sun and object */
        cos_soldiam =        /* cosine of solar semi_diameter */
            cos (SOLAR_SEMIDIAM * RAD_ASEC),
        mu_deflect,          /* gravitational deflection coefficient */
        norm_factr;          /* normalization factor for dir_cosines */
 
    int i;                   /* summation index */
 
    double rad_day = DEGREE / JUL_YEAR;  /* converts degrees per year
                                                 to radians per day */
    double mr = ASTR_UNIT / 1000.0;      /* astronomical unit in Kilometers */
    double ab_factr = 1000.0             /* converts kilometers per day */
	/ (SEC_DAY * ARCSEC * C_LIGHT);  /* (velocity) to arcsec (aberration) */

    /* current time relative to 1900jan0.5 */
    d = (tnow + 1.0) * JUL_CENT;
    y = (tnow + 1.0) * 100.;

    /* orbital elements for Sun and Moon  [Atkinson A1 - A5] */
    l  = 4.8816279 + 0.01720279126 * d + 2.4e-6;
    g  = 6.25658   + 0.0172019698  * d;
    e  = 6.1215    + 0.2127687117  * d;
    g1 = 5.168     + 0.2280271350  * d;
    u  = 0.1964    + 0.2308957232  * d;

    /* Sun's equation of center  [Atkinson A7] */
    cnt = (6910.057 - 4.72e-4 * d) * sin (g) + 72.100 * sin (2.0 * g) +
                   1.054 * sin (3.0 * g);

    /* lunar perturbation and its derivatives  [Atkinson A8 - A12] */
    lpl = 6.454 * sin (e) - 0.424 * sin (e - g1);
    lpr = 1336.0 * cos (e) -  133.0 * cos (e - g1);

    dlpr = - 284.26 * sin (e)             - 1.91 * sin (3.0 * e)
           -  16.31 * sin (e + g1)        - 2.03 * sin (e - g1)
           -   3.28 * sin (3.0 * e - g1)  + 3.22 * sin (e + g)
           -   7.04 * sin (e - g);
 
    dlpl =   1.3732 * cos (e)             + 0.0083 * cos(3.0 * e)
           + 0.0780 * cos (e + g1)        + 0.0065 * cos (e - g1)
           + 0.0160 * cos (3.0 * e - g1)  - 0.0147 * cos (e + g)
           + 0.0336 * cos (e - g);
 
    dplt =   0.1330 * cos (u);

    /*
    **  Planetary perturbations.  Note that all items are summed from
    **  1 to 17, whereas Atkinson sums A20 and A21 from 1 to 12,
    **  A14 from 3 to 17, and A15 from 3 to 12.
    */
    ppl = 0.;
    ppr = 0.;
    dppl = 0.;
    dppr = 0.;
    for (i = 0; i < 17; i++)
	{
        rpl = (angl[i] + rate[i] * y) * DEGREE;            /* A13 */
        cos_rpl = cos (rpl);
        sin_rpl = sin (rpl);
        ppl  += ampl[i] * cos_rpl;                         /* A14 */
        ppr  += radv[i] * sin_rpl;                         /* A15 */
        dppl -= ampl[i] * rate[i] * sin_rpl;               /* A21 */
        dppr += radv[i] * rate[i] * cos_rpl;               /* A20 */
	}
    dppl *= rad_day;
    dppr *= rad_day;

    /* long period perturbation in longitude  [Atkinson A16] */
    lgpl =  6.400 * sin (4.03503 + 9.6525e-6 * d)
          + 1.871 * sin (0.99903 + 7.1806e-5 * d);

    /* longitude of the Sun  [Atkinson A17] */
    sunl = l + (cnt + lpl + ppl + lgpl) * ARCSEC;
    cos_sunl = cos (sunl);
    sin_sunl = sin (sunl);

    /* direction cosines of Sun */
    sun_posn[0] = cos_sunl;
    sun_posn[1] = sin_sunl * cos_eps;
    sun_posn[2] = sin_sunl * sin_eps;

#ifdef DEBUG
/*DEBUG -- fudge solar longitude to get Besselian day numbers
**         C and D with respect to nearest end of year (before 1984)
**         or middle of current Julian year (1984 and later).
**         Use J2000 precession constant for 1984 and later.
**/
    {
    double tau;
    int n;

    if (y < 84.0)
        {
	tau = (d - 0.313) / 365.242194;
	n = tau;
	tau = tau - n;
	if (tau > 0.5)
	    tau = tau - 1.;
	sunl = sunl - 2.437e-4 * tau;
        }
    else
        {
	n = y;
	tau = y - n - 0.5;
	sunl = sunl - 2.438e-4 * tau;
        }
    sin_sunl = sin (sunl);
    cos_sunl = cos (sunl);
    }
/*END-DEBUG*/
#endif

    /*
    **  Actual Velocities
    */
    pr_dal = 5.9256e6 * (lpr * 1.0e-8 + ppr * 1.0e-9);         /* A19 */
    dpr = LOG_E_10 * mr * (dlpr * 1.0e-8 + dppr * 1.0e-9);     /* A22 */
    dpl = pr_dal + mr * (dlpl + dppl) * ARCSEC;                /* A23 */
    vlt = mr * dplt * ARCSEC;                                  /* A24 */

    v1 = ab_factr * dpr;                                       /* A25 */
    v2 = ABERRATE + ab_factr * dpl;                            /* A26 */
    v3 = ab_factr * vlt;                                       /* A27 */

    /*
    **  Barycentric Corrections
    */

    gj = -27.481  + 0.0014501127 * d;                          /* A31 */
    lj = -27.2587 + 0.0014508827 * d  + 0.09684 * sin (gj)
         + 0.00293 * sin (gj + gj);                            /* A32 */
    gs =  -9.508  + 0.0005837134 * d;                          /* A33 */
    ls =  -7.9185 + 0.0005846491 * d + 0.11136 * sin (gs)
         + 0.00388 * sin (gs + gs);                            /* A34 */

    /* The following two statements are the final two (unnumbered)
     ** equations in the appendix of Atkinson's paper */
    bc = 0.008581 * cos (lj) + 0.001896 * cos (ls) + 0.000400;
    bd = 0.008581 * sin (lj) + 0.001896 * sin (ls) + 0.000204;

    /* Eccentricity and perihelion (J2000) [Explan. Suppl. (1968), pg 48] */
    eccentr = 0.01671 - 0.00004 * tnow;
    perih = (102.94 + 1.72 * tnow) * RAD_DEG;

    /* E-term and its components */
    eterm = eccentr * ABERRATE;
    e1    = eterm * sin (perih);
    e2    = eterm * cos (perih);

#ifdef DEBUG
/*DEBUG - exclude e-terms to compare Bessel C and D with ephemeris */
/*DEBUG      (prior to 1984) */
/*DEBUG**/  if (y < 84.0)  { e1 = 0.0;   e2 = 0.0; }
/*END DEBUG */
#endif

      /* AT LAST! Earth's rectangular velocity components, expressed
      **   in radians of aberration.  Atkinson eqs 3 - 5.            */
    ve[0] = -RAD_ASEC * ((v1 * cos_sunl  -  v2 * sin_sunl)  +  e1  -  bd);
      v2  =  RAD_ASEC * ((v1 * sin_sunl  +  v2 * cos_sunl)  -  e2  +  bc);
      v3  *=  RAD_ASEC;
    ve[1] = -(v2 * cos_eps  -  v3 * sin_eps);
    ve[2] = -(v2 * sin_eps  +  v3 * cos_eps);

#ifdef DEBUG
/*debug*/  {double c = ve[1]/RAD_ASEC, d = -ve[0]/RAD_ASEC ;
/*debug*/   printf("aberrat:  C = %7.3f,      D = %7.3f\n", c, d); }
#endif

    /*
    **  GENERAL RELATIVITY CORRECTION
    **    SOURCE:  C. Wade, VLA Scientific Memo # 122, February 1976
    **               (Corrected in accordance with Murray, MNRAS 195,
    **                639-648 (1981) -- no terms in sin(2D).)
    */

    cos_sundist = dotpr3 (sun_posn, mean_posn);

    if (cos_sundist > cos_soldiam)    /*  Is source behind the Sun?? */
        cos_sundist = cos_soldiam;
    mu_deflect = 1.9742e-8 / (1.0 - cos_sundist);

    /*
    **  CONSTRUCT AND NORMALIZE THE APPARENT POSITION-VECTOR
    */
    for (i = 0, norm_factr = 0.0; i < 3; i++)
	{
        app_posn[i] = mean_posn[i] + ve[i] +
                        mu_deflect * (mean_posn[i] * cos_sundist - sun_posn[i]);
        norm_factr += app_posn[i] * app_posn[i];
	}
    norm_factr = sqrt (norm_factr);
    for (i = 0; i < 3; i++)
        app_posn[i] /= norm_factr;
}
