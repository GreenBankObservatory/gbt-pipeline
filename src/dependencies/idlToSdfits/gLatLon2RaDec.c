/* File gLatLon2RaDec.c, version 1.10, released  06/02/01 at 08:26:05 
   retrieved by SCCS 14/04/23 at 15:51:23     

%% Function to calculate ra, dec from galactic latitude and longitude

:: GBES-C point geometry antenna peakup slice region
 
History:
  060122 GIL use angleLimit()
  980928 GIL fix cos(POLEDEC)
  980921 GIL use AIPS constants
  980427 GIL fix ra,dec to lat,lon
  980414 AHM fix bug determining RA from l,b - should be(sb*cc) not (sb*sc) 
             in second term of atan2
  980408 GIL keep output ra,dec in range
  980307 GIL update J2000 coefficients
  970212 GIL add comments about J2000 Coordinates
  970202 GIL initial version
 
DESCRIPTION:
Simple function to convert galactic latitude and longitude to J2000 Ra, Dec.
Updated to use AIPS defined values for J2000 positions.
OMISSIONS:
ToRaDec( toGlatLon()) yields the self-consistent result to better
than 0.1" accurracy.  Not sure that absolute accuracy is better than .1"
*/

#include "stdio.h"
#include "string.h"
#include "math.h"
#include "MATHCNST.H"

/* externals */
extern void obsposn (long, double, double, double, double *, double *); 
extern char * angleLimit( double * inOutAngle);
extern char * angleRange( double minAngle, double maxAngle, double * angle);

/* below are the B1950 Galactic North Pole Coordianates 12h49, 27d24' */
#define POLE1950RA  192.2400*DEGREE
#define POLE1950DEC  27.4000*DEGREE
/* below are the J2000 Galactic North Pole Coordianates */
/* #define POLERA  192.85933333*DEGREE */
/* #define POLEDEC  27.12825278*DEGREE */
#define ASCENDINGNODE 33.07 *DEGREE
#define POLERA  192.859375*DEGREE
#define POLEDEC  27.128643*DEGREE
#define LONCELESTIALPOLE 122.932018*DEGREE
#define EPSILON (ARCSEC*.1)


/* AL double sc = sin(POLEDEC), cc = cos(POLEDEC); */
/*static double sc=0.4559846,     cc = 0.8899877; */
static double sc = 0.45598988,    cc = 0.88998496;

char *  gLatLon2RaDec( double gLat, double gLon, double * pRa, double *pDec)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* gLatLonToRaDec() coverts input gLat, gLon (radians) to J2000 Ra, Dec (Rad)*/
/* returns NULL on OK                                                        */
/* CALCULATE RA DEC COORDINATES (1950) (use different constants for J2000)   */
/*          -1                                                               */
/* dec = sin  ( cos(b)cos(27.4)sin(l-33.) + sin(b)sin(27.4) )                */
/*                                                                           */
/*         -1             cos(b) cos(l-33)                                   */
/* ra = tan  ( ----------------------------------------- )                   */
/*             sin(b)cos(27.4) - cos(b)sin(27.4)sin(l-33)                    */
/*   DEC = ASIN (SIN(GLAT)*SIN(DECGP) + COS(GLAT)*COS(DECGP)*                */
/*     *   COS(GLON-LONCP))                                                  */
/*      RA = RAGP + ATAN2 (COS(GLAT)*SIN(LONCP-GLON), SIN(GLAT)*             */
/*     *   COS(DECGP) - COS(GLAT)*SIN(DECGP)*COS(GLON-LONCP))                */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ double sl, cl, sb, cb, sd, l = gLon - LONCELESTIALPOLE, 
    b = gLat, ra, dec;

  sl = sin(l);
  cl = cos(l);
  sb = sin(b);
  cb = cos(b);
  sd = (sb*sc) + (cb*cc*cl);           /*sin(dec)*/
  dec = asin(sd);
 
  if (dec >= TWOPI)                     /*make range 90 to -90*/
    dec -= TWOPI;
  if (dec >= PI)                        /*make range 90 to -90*/
    dec = TWOPI - dec;
  if (dec >= PIOVR2)
    dec = PI - dec;

  if (1. - fabs(sd) < EPSILON)          /* if near the pole */
     ra = 0.;
   else
     ra = (atan2(-sl*cb,(sb*cc)-(cb*sc*cl))) + POLERA;
 
  angleLimit( &ra);
 *pRa  = ra;
 *pDec = dec;

  return(NULL);
} /* end of gLatLon2RaDec() */

char *  raDec2gLatLon( double ra, double dec, double * gLat, double * gLon)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* reDec2gLatLon() converts the ra and dec (J2000) to galactic latitude and  */
/* longitude.  Returns NULL ON OK, else error message                        */
/* CALCULATE GALACTIC COORDINATES                                            */
/*        -1                                                                 */
/* b = sin  ( cos(dec)cos(27.4)cos(ra-192.25) + sin(dec)sin(27.4) )          */
/*                                                                           */
/*        -1    sin(dec) - (sin(b) sin(27.4))                                */
/* l = tan  ( -------------------------------- )                             */
/*             cos(dec)sin(ra-192.25)cos(27.4)                               */
/* AIPS: 15APR98                                                             */
/*        GLAT = ASIN (SIN(DEC)*SIN(DECGP) + COS(DEC)*COS(DECGP)*            */
/*    *      COS(RA-RAGP))                                                   */
/*        GLON = LONCP + ATAN2 (COS(DEC)*SIN(RAGP-RA), SIN(DEC)*             */
/*    *      COS(DECGP) - COS(DEC)*SIN(DECGP)*COS(RA-RAGP))                  */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ double  sr, cr, sd, cd, sb;

  ra -= POLERA;                             /* RA relative to galactic pole */
  sr = sin(ra);
  cr = cos(ra);
  sd = sin(dec);
  cd = cos(dec);
  sb = (cd*cc*cr) + (sd*sc);                /* sin(b)*/
  *gLat = asin(sb);                         /* galactic latitude*/
 
  if (*gLat >= TWOPI)                        /* keep range 90 to -90*/
    *gLat = *gLat - TWOPI;
  if (*gLat > PI)                           /* make range 90 to -90*/
    *gLat = TWOPI - *gLat;
  if (*gLat > PIOVR2)
    *gLat = PI - *gLat;

  if (1. - fabs(sb) < EPSILON)                /* if near the pole */
    *gLon = 0.;                             /* set galactic long */
  else
    *gLon = (atan2(-sr*cd,(sd*cc)-(cd*sc*cr))) + LONCELESTIALPOLE;
 
  angleLimit( gLon);
   
 return(NULL);
} /* end of raDec2gLatLon() */



