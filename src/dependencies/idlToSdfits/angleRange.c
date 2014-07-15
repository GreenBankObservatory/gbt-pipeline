/* File angleRange.c, version 1.3, released  08/05/18 at 15:46:36 
   retrieved by SCCS 14/04/23 at 15:51:23     

%% utility function to limit an input angle (radians) to a specified range
:: TEST C program
 
HISTORY:
  060215 GIL add anglePmPi() function for limiting hour angles
  060120 GIL initial version

DESCRIPTION:
angleRange() limits an input angle to a specified angle range
*/

#include <stdio.h>
#include "STDDEFS.H"
#include "MATHCNST.H"

/* externals */

/* internals */
char * angleLimit( double * inOutAngle)
/* angleRange() returns in-range angle, between 0 and TWOPI */
{
  /* first get angle in range 0 to TWOPI */
  while ( *inOutAngle < 0.) 
    *inOutAngle += TWOPI;

  while ( *inOutAngle > TWOPI) 
    *inOutAngle -= TWOPI;

  return(NULL);
} /* end of angleLimit() */

char * angleRange( double minAngle, double maxAngle, double * inOutAngle)
/* angleRange() takes minimum and maximum angles and returns in-range angle */
/* note some combinations are not possible; ie +PI min, -PI max */
{
  /* first get angle in range 0 to TWOPI */
  while ( *inOutAngle < minAngle) 
    *inOutAngle += TWOPI;

  while ( *inOutAngle > maxAngle) 
    *inOutAngle -= TWOPI;

  /* deal with +/- angles ie 270d -> -90d & 3/2 PI -> -PI/2 */
  return(NULL);
} /* end of angleRange() */

char * anglePmPi( double * inOutAngle)
/* anglePmPi() angle Plus/Minus PI keeps angles (radians) in Range */
/* Example: PI/2 => PI/2; -PI/2 => -PI/2; 5*PI/6 => - PI/6;  8.9 PI => .9 PI;*/
/* Example: 9.1 PI => - 0.9 PI/2; All angles have valid output range */
{

  /* first get angle in range 0 to TWOPI */
  while ( *inOutAngle < -TWOPI) 
    *inOutAngle += TWOPI;

  while ( *inOutAngle > TWOPI)
    *inOutAngle -= TWOPI;

  /* deal with +/- angles ie 270d -> -90d ==> 3/2 PI -> -PI/2 */
  /* now put in specified range */    
  if (*inOutAngle > PI)
    *inOutAngle = *inOutAngle - TWOPI;
  else if (*inOutAngle < -PI)
    *inOutAngle = TWOPI + *inOutAngle;

  /* deal with +/- angles ie 270d -> -90d ==> 3/2 PI -> -PI/2 */
  /* now put in specified range */    

  return(NULL);
} /* end of anglePmPi() */

char * testAnglePmPi()
{  long i = 0;
   double dAngle = PI/3., inAngle = - 9.1 * PI, outAngle = 0.;

   for (i = 0; i < 100 && inAngle < 9.1 * PI; i++) {
     inAngle += dAngle;
     fprintf( stderr, "Angle %8.2lf d => ", inAngle/DEGREE);
     outAngle = inAngle;
     anglePmPi( &outAngle);
     fprintf( stderr, "%8.2lf d\n", outAngle/DEGREE);
   }

   return(NULL);
} /* end of testAnglePmPi() */





