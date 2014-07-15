/* File rectpol.c, version 1.1, released  98/03/20 at 09:16:25 
   retrieved by SCCS 14/04/23 at 15:51:15     

%% function to convert from rectangular to polar co-ordinates

:: polar
 
HISTORY:
  980320  GIL added function prototyping based on VLBA code
              @(#)rectpol.c  version 1.1  created 90/04/02 14:32:11
              fetched from SCCS 95/11/13 10:26:23

DESCRIPTION:
Function to convert from rectangular to polar co-ordinates
*/
#include <math.h>
#include "MATHCNST.H"

/* internals */
#define TOO_SMALL  1.0e-9    /* should be square root of smallest 
				nonzero value that compiler can handle */

/*++****************************************************************************
*/
void rectpol (
double dir_vector[3],    /* input, xyz co-ordinates */
double *ra,              /* returned ra in radians, where 0 <= ra < TWOPI */
double *dec)             /* returned dec in radians */
/*
* If the z-axis coincides with the polar axis, and the x-axis passes thru
* the vernal equinox, then this routine converts to the equatorial system
* of right ascension and declination (as is implied by the nomenclature
* of the formal parameters).
-*/
{
    double x = dir_vector[0];
    double y = dir_vector[1];
    double z = dir_vector[2];
    double fabsx, fabsy;

    fabsx = (x >= 0) ? x : -x;
    fabsy = (y >= 0) ? y : -y;

    /* take care of the special case of input = a pole */
    if (fabsx < TOO_SMALL  &&  fabsy < TOO_SMALL)
	{
        *ra = 0.0;
        *dec = (z > 0) ? PIOVR2 : -PIOVR2;
        return;
	}
 
    /* calculate the declination */
    *dec = atan2 (z, sqrt (x * x + y * y));
 
    /* take care of special cases of x = 0 or y = 0 */
    if (fabsx < TOO_SMALL)
	{
	*ra = (y > 0) ? PIOVR2 : PIOVR2 + PI;
        return;
	}
    if (fabsy < TOO_SMALL)
	{
	*ra = (x > 0) ? 0.0 : PI;
	return;
	}
 
    /* calculate right ascension, in the range 0 <= ra < TWOPI */
    if ((*ra = atan2 (y, x)) < 0.0)
	*ra += TWOPI;
} /* endo of rectpol() */
