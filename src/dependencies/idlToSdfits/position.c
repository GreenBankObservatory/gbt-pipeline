/* File position.c, version 1.1, released  00/08/17 at 13:42:01 
   retrieved by SCCS 14/04/23 at 15:51:16     

%% function to calc current geocentric apparent position from J2000 position

:: pointing position apparent J2000 geocentric equinox equation
 
HISTORY:
  980320  GIL added function prototyping based on VLBA code
              @(#)position.c  version 1.1  created 90/04/02 14:32:08
              fetched from SCCS 95/11/13 10:24:24

DESCRIPTION:
function to calc current geocentric apparent position from J2000 position
*/

#include <math.h>
#include "MATHCNST.H"

/* externals */
void dircos ();
void prcesj2 ();
void aberrat ();
void nutate ();
void nutrotn ();
double obliq ();

/*++****************************************************************************
*/
double position (
double ra_j2000,     /* J2000 right ascension */
double dec_j2000,    /* J2000 declination */
double t_now,        /* current time wrt J2000 in Julian centuries */
double pos_now[3])   /* (output) direction cosines of
			current corrected position */
/*
* RETURNS equation of equinoxes (delta _psi * cos (mean_obliquity)),
*              in seconds of time
*
* This routine does NOT include calculations for proper motion or parallax.
-*/
{
    double pos_j2000[3];     /* direction cosines of J2000 position */
    double pos_mean[3];      /* dir-cosines of mean position of date */
    double pos_aber[3];      /* d-c of mean pos of date, corrected for
                                aberration and relativistic deflection */
    double pos_app[3];       /* d-c of apparent (geocentric) position */
    double pos_topo[3];      /* dir-cosines of topocentric position */
    double mean_obliq;       /* mean obliquity of date */
    double delta_psi;        /* nutation in longitude */
    double delta_eps;        /* nutation in obliquity */
    double eqn_eqnx;         /* equation of equinoxes */
    int i;                   /* loop index */
 
    /* convert input ra, dec to direction cosines */
    dircos (ra_j2000, dec_j2000, pos_j2000);

    /* precess from J2000 to t_now */
    prcesj2 (t_now, pos_j2000, pos_mean);

    /* correct for aberration and general relativistic deflection */
    mean_obliq = obliq (t_now);
    aberrat (t_now, mean_obliq, pos_mean, pos_aber);

    /* correct for nutation */
    nutate (t_now, &delta_psi, &delta_eps);
    nutrotn (mean_obliq, delta_psi, delta_eps, pos_aber, pos_app);

    /* topocentric corrections go here
    ** (Currently, there are no topocentric corrections,
    ** so copy the apparent position into the topocentric position.)
    */
    for (i = 0; i < 3; i++)
	pos_topo[i] = pos_app[i];

    /* load the final position into the caller's variable, then return */
    for (i = 0; i < 3; i++)
        pos_now[i] = pos_topo[i];
    eqn_eqnx = delta_psi * cos (mean_obliq) / (RAD_ASEC * 15.0);
    return (eqn_eqnx);
} /* end of position() */
