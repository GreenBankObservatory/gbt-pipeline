/* File gastm.c, version 1.1, released  03/02/26 at 16:56:53 
   retrieved by SCCS 14/04/23 at 15:51:20     

%% utility mathmatical function based on astronomcial constants.

HISTORY
030226 GIL fix errors due to not prototyping

DESCRIPTION:
gastm() returns Greenwich Apparent Sidereal Time at Midnight  for
an input date (long modified julian date).
*/

/* includes */
#include "math.h"
#include "vlb.h"
/* externals */
extern char * str2rad( char *, double *);
extern double obliq( double t_now);
extern void nutate     (
    double t_now,	/* time with respect to J2000, Julian Centuries */
    double *delt_psi,	/* returned nutation in longitude at t_now */
    double *delt_eps);	/* returned nutation in obliquity at t_now */

/*******************************************************************************
*/
double gastm	/* returns Greenwich Apparent Sidereal Time at Midnight */
    (long mjd)	/* on this Modified Julian Date */
/*
 * Handles stuff mostly as integers to avoid the truncations inherent in
 * the limited mantissas of float.
 */
{
    double tu = 0;
    double gast = 0;
    double longi = 0;
    double obliqui = 0;
    double temp = 0;
    long epoch = 0, century = 0, years = 0, days = 0;

    tu = (mjd - 51544.5) / 36525.0;
    epoch = mjd - 15019;                  /* minus Jan 0, 1900 */
    century = epoch / 36525L;
    epoch = epoch - century * 36525L;
    years = epoch / 365;
    epoch = epoch - years * 365;
    days = epoch;

     /* the next expression is the Greenwich Mean Sidereal Time
        at midnight UT1 */
    str2rad ("6h41m50.54841s", &gast);    /* constant - see circ 163 */
    str2rad ("3m04.81287s", &temp);       /* due to julian vs greg cent */
    gast = gast + temp * (century - 1);
    str2rad ("57.29071s", &temp);         /* leap year term */
    gast = gast - temp * years;
    str2rad ("3m56.55537", &temp);        /* 4m per day */
    gast = gast + temp * (days - 0.5);
    str2rad ("0.09310s", &temp);          /* secular term */
    gast = gast + temp * tu * tu;

    nutate (tu, &longi, &obliqui);
    return (gast + longi * cos (obliq (tu)));
}
