/* File angularDistance.c, version 1.3, released  97/06/27 at 16:39:54 
   retrieved by SCCS 14/04/23 at 15:51:21     

%% function to calculate the angular distance between to angular coords

:: GBES-C realtime/Offline
 
History:
  970626 GIL fix comments
  960719 GIL handle case of round off for arcCos (1.+EPSILON)
  940921 GIL initial version
 
DESCRIPTION:
Take any two pairs of angular coordinates and calculate the exact
angular distance between them.  (inputs can be az,el pairs, ra,dec pairs
or glat,glon pairs, but can not mix az,el and ra,dec etc).
*/

#include "math.h"
#include "MATHCNST.H"   /* Mathematical constants. */

double angularDistance( double raA, double decA, double raB, double decB) 
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* calculate the angular distance between two points                         */
/* INPUT raA, decA are the location of point A (radians)                     */
/* INPUT raB, decB are the location of point B (radians)                     */
/* OUTPUT angular distance between them (radians) is returned                */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ double dRa = raA - raB, cosDistance, distance;
  double cosA = cos( PIOVR2 - decA), cosB = cos( PIOVR2 - decB);
  double sinA = sin( PIOVR2 - decA), sinB = sin( PIOVR2 - decB);

  cosDistance = (cosA*cosB) + ( sinA*sinB*cos( dRa));


  if (cosDistance < -1.)               /* handle precision problems */
    distance = PI;
  else if ( cosDistance > 1.)
    distance = 0.;
  else 
    distance = acos( cosDistance);     /* normal calculation */

  if (distance < 0.)                   /* if negative distance */
    distance = -distance;              /* convert to positive */
  return(distance);
} /* end of angularDistance */
