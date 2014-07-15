/*  @(#)obliq.c  version 1.3  created 95/11/24 08:17:36
    %% function to calc MEAN obliquity at an arbitrary time, in radians.
    LANGUAGE: C
    ENVIRONMENT: Any
*/

/* includes */
#include "MATHCNST.H"
#include "vlb.h"

/*******************************************************************************
*/
double obliq
    (
    double t_now       /* time with respect to J2000, in Julian centuries  */
    )
/*
 * RETURNS: mean obliquity at t_now, in radians
 *
 *  SOURCE:  United States Naval Observatory; Circular number 163
 *                   (1981dec10), page A3
 *
 * To obtain the TRUE obliquity:  To the value returned by this function,
 * add delta-epsilon, which is calculated by "nutate".
 *
 * Definition of t_now:
 *   ([Julian Day Number of target epoch] - 2451545.0) / 36525.0
 *   where the JD number includes the fractional day since 12h TDB.
 *
 * TEST STATUS: (Version 1.0, tested 21 Jan 86, by D. King)
 *  VAX (50+ bits of precision):
 *   Output of this routine was combined with the Nutation in Obliquity
 *   from routine NUTATE, and the result compared to the "Astronomical
 *   Almanac" for each day of 1985.  ONE DISCREPANCY, of +0".001, was found 
 *   (for 85aug18).  The VAX result for this date was then printed to 9 
 *   decimals and found to be xxx".187500056.  The discrepancy is thus thought 
 *   to be attributable to differences in machine precision and round-off 
 *   algorithms between the VAX and the machine used by the compilers of the 
 *   Almanac.
 *  Alcyon C for Motorola MC68000 (VME/10) (24 bits of precision):
 *   The true obliquity was calculated, as above, for each day of 1985.
 *      The following results were obtained:
 *                 34 days:  exact match with almanac;
 *                197 days:  VME/10 results were greater than almanac;
 *                135 days:    "       "     "   less      "     "   ;
 *                extreme deviations were plus and minus 0".010;
 *                mean deviation was +0".000795;
 *                RMS deviation was 0".004032.
 * Since 24 bits can express the obliquity (about 84300 arc-seconds) to
 * a precision of only about 0".005, the above results are considered
 * to be quite acceptable.
 */
{
    double obl;
 
    obl = ((0.001813 * t_now - 0.00059) * t_now - 46.8150) * t_now 
	+ 84381.448;
    return (obl * RAD_ASEC);
}
