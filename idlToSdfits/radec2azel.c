/* File radec2azel.c, version 1.4, released  06/01/20 at 17:19:14 
   retrieved by SCCS 09/12/30 at 16:45:21     

%% functions to convert from ra dec (of date) to az, el (of antenna) and vs.

:: GBES-C point antenna
 
History:
  060120 GIL - fix diffinition of hourangle in azel2radec
  940224 GIL - initial version based on section of code in point.c

DESCRIPTION:
Functions to convert from ra dec (of date) to az, el and visa versa.
These functions implimented to be repeatedly called and cash
some temporary values.
*/
#include <math.h>
#include "MATHCNST.H"

/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
void radec2azel( double ra, double dec,          /* take ra, dec (radians) */
            double lst, double lat,              /* need lst time, latitude */
	    double * azimuth, double *elevation) /* calc az, el */
/* all input and output angles and times are in radians */
{ static double cosdec = 1., sindec = 0., lastdec = 0;
  static double coslat = 1., sinlat = 0., lastlat = 0;
  double cosz, sinz, hourAngle, cosaz, sinaz, az, el;

  if (dec != lastdec) {                     /* if a new dec, calc cos, sin */
    cosdec = cos(dec);
    sindec = sin(dec);
    lastdec = dec;                          /* know when to calc again */
  }

  if (lat != lastlat) {                     /* if a new lat, calc cos, sin */
    coslat = cos(lat);
    sinlat = sin(lat);
    lastlat = lat;                          /* know when to calc again */
  }

  hourAngle = lst - ra;

  /* The following code was stolen from VLBA's pointdrv.c */

  /* calc source elevation */
  cosz = sinlat * sindec	            /* cosine(zenith angle) */
       + coslat * cosdec * cos(hourAngle);
  sinz = sqrt (1.0 - (cosz * cosz));        /* sine(zenith angle) */
  el = (sinz != 0.0) ? atan2(cosz, sinz) : PIOVR2;

  /* calc source azimuth range = -PI(south) to 0(north) to +PI(south) */

  if (coslat != 0.0 && sinz != 0.0) {
    cosaz = (sindec - sinlat * cosz) / (coslat * sinz);
    sinaz = -cosdec * sin(hourAngle) / sinz;
    if (cosaz)
      az = atan2 (sinaz, cosaz);
    else
      if (sinaz > 0.0)
	az = PIOVR2;
      else 
	az = PI + PIOVR2;
    }
  else az =0;

  *azimuth = az;                            /* transfer to output */
  *elevation = el;   
} /* end of radec2azel() */

/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
void azel2radec( double azimuth, double elevation,    /* take az,el (radians)*/
            double lst, double lat,                   /* need lst time, lat  */
	    double * raOut, double * decOut)          /* calc ra, dec */
/* all input and output angles and times are in radians */
/* azimuth ranges from 0 (north) to pi/2 (west) to pi (south) to 2pi (north) */
/* elevation ranges from pi/2 (up) to 0 (horizion) to -pi/2 (down) */
{ static double cosaz = 1., sinaz = 0., lastaz = 0;
  static double cosel = 1., sinel = 0., lastel = 0;
  static double coslat = 1., sinlat = 0., lastlat = 0;
  double cosh, sinh, hourAngle, ra, dec, sindec;

  if (elevation != lastel) {                /* if a new el, calc cos, sin */
    if (elevation > PIOVR2) {               /* if over the top */
      azimuth = azimuth - PI;               /* compute for other side */
      elevation = PI - elevation;
    }
    cosel = cos(elevation);
    sinel = sin(elevation);
    lastel = elevation;                     /* know when to calc again */
  }

  if (azimuth != lastaz) {                  /* if a new az, calc cos, sin */
    cosaz = cos(azimuth);   
    sinaz = sin(azimuth);
    lastaz = azimuth;                       /* know when to calc again */
  }

  if (lat != lastlat) {                     /* if a new lat, calc cos, sin */
    coslat = cos(lat);
    sinlat = sin(lat);
    lastlat = lat;                          /* know when to calc again */
  }

  /* calc source declination */
  sindec = (sinlat * sinel) + ( coslat * cosel * cosaz );
  dec    = asin( sindec);

  sinh = cosel * sinaz * coslat;            /* sin and cos functions */
  cosh = sinel - (sinlat * sindec);         /* of hour angle */

  /* the actual sin and cos functions of hour angle should be divided by */
  /* cosdec * coslat; however, these cancel in the atan2 calculation */

  /* hour angle range = -PI(north) to 0 (south) to +PI(north) */
  /* atan2() returns angles in range -PI to PI */
  hourAngle = atan2( sinh, cosh);

  ra = lst - hourAngle;                     /* right ascension */
  
  /* dec range is -PIOVR2 to PIOVR2; asin() range is 0 to PI */
  if (dec > PIOVR2) {
    dec = dec - PI;
    ra = ra + PI;
  }
  /* ra range 0 to twopi */
  if (ra < 0)
    ra = ra + TWOPI; 
  
  ra = fmod( ra, TWOPI);                    /* ra must be between 0 and 2pi */

  *raOut = ra;
  *decOut = dec;
} /* end of azel2radec() */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
