/* File transformObliquity.c, version 1.1, released  01/10/18 at 10:11:20 
   retrieved by SCCS 14/04/23 at 15:51:19     

%% function to calculate velocites relative to a direction

:: GBES-C position point J2000 epoch apparent
 
History:
  011018 GIL initial c version
  ?????? RJM initial version
              
DESCRIPTION:
transformObliquity transforms ra, dec into coordiantes 
with north pole at the normal to the orbit of the earth around the
sun.
*/
#include "stdio.h"	/* add io definitions */
#include "math.h"	/* add mathmatics definitions */
#include "MATHCNST.H"	/* define TWOPI */
#include "STDDEFS.H"	/* define TWOPI */


char * transformObliquity( double ra, double dec, double obliquity,
			   double * eclipticLong, double * eclipticLat)
/* transformObliquity() converts from apparent ra,dec with current obliquity */
/* to ecliptic coordinates.  All Arguments and outputs in radians */
{
  *eclipticLong = 
    atan2( sin(ra)*cos(obliquity)+tan(dec)*sin(obliquity),cos(ra) );
  *eclipticLat  =
    asin( sin(dec)*cos(obliquity)-cos(dec)*sin(obliquity)*sin(ra) ) ;

  return(NULL);
} /* end of transformObliquity() */
