/* File velocities.c, version 1.5, released  04/08/25 at 16:59:15 
   retrieved by SCCS 14/04/23 at 15:51:17     

%% function to calculate velocites relative to a direction

:: GBES-C position point J2000 epoch apparent
 
History:
  040825 GIL remove calls to the naif functions
  011030 GIL remove helioToLsr
  011021 GIL use a C function and J2000 coordiantes to calc V_LSR
  011019 GIL simplify
  011018 GIL use mostly C functions
  011011 GIL initial version
              
DESCRIPTION:
velocties transforms date+time and directions ra, dec J2000 to 
velocites of the Earth relative the Sun, ra and dec.
*/
#include "stdio.h"	/* add io definitions */
#include "math.h"	/* add mathmatics definitions */
#include "MATHCNST.H"	/* define TWOPI */
#include "STDDEFS.H"	/* define TWOPI */

/* externals */
extern double position (
double ra_j2000,     /* J2000 right ascension */
double dec_j2000,    /* J2000 declination */
double t_now,        /* current time wrt J2000 in Julian centuries */
double pos_now[3]);   /* (output) direction cosines of
			current corrected position */
void rectpol (
double dir_vector[3],    /* input, xyz co-ordinates */
double *ra,              /* returned ra in radians, where 0 <= ra < TWOPI */
double *dec);             /* returned dec in radians */
char * transformObliquity( double ra, double dec, double obliquity,
			   double * eclipticLong, double * eclipticLat);

/* calls to fortran functions */

/*double vsun_( double * eclipticLong, double * eclipticLat, double * t_now);*/
double vlsr_( double * ranow, double * decnow, double * t_now);
extern double angularDistance( double raA, double decA, 
			       double raB, double decB);
char * helioToLsr( double raJ2000, double decJ2000, double vHelio,
		   double * vLsrOut);

/* internals */
#define MJD_2000 51544.5           /* mjd of J2000 (2000 Jan 1.5) */

char * velocities ( long mjd, double utc, double raJ2000, double decJ2000,
		    double lst, double latitude, 
 		    double * vEarthOut, double * vSunOut, double * vLsrOut)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* velocity() takes the J2000, ra, dec and calculates the components of the  */
/* velocity of the earth relative to LSR velocitie (km/sec)                  */
/* The J2000 coordinates of the object are returned (radians)                */
/* The algorythm is iterative, and the number of interations is returned     */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ double ranow = 0, decnow = 0,
    /***  calc epoch wrt J2000 in Julian centuries  ***/
    t_now = (mjd - MJD_2000 + (utc / TWOPI)) / JUL_CENT,
    julianDate = mjd + JD_J2000 - MJD_2000 + (utc/TWOPI),
    vEarth = 0, vSun = 0, vLsr = 0, dT = 0,
    eclipticLong = 0, eclipticLat = 0, obliq = 0, posvectr[3],
    /* retation Rate of earth at equator, km/sec */
    vEarth0 = TWOPI*E_EQ_RADIUS*1.E-3/(SOLAR_SID*24.*3600.),
    obliquityCoef[4] = {23.452294, -0.0130125, -0.00000164, 0.000000503};
  
  /* get earth spin axis parameter */
  obliq = obliquityCoef[0];                  /* value in degrees */
  dT = (julianDate - 2415020.0) / (double)JUL_CENT;  /* coeff. from 1950 */
  obliq += (obliquityCoef[1]*dT);
  obliq += (obliquityCoef[2]*dT*dT);
  obliq += (obliquityCoef[3]*dT*dT*dT);

  obliq *= DEGREE;                           /* convert to radians */

  /***  get current apparent position into posvectr  ***/
  position (raJ2000, decJ2000, t_now, posvectr);

  /***  convert posvectr to polar co-ords  ***/
  rectpol (posvectr, &ranow, &decnow);

  /* calculate the velocity of the earth in the direction of the source */
  vEarth = vEarth0 * sin(lst-ranow) * cos(latitude) * cos(decnow);

  transformObliquity( ranow, decnow, obliq,
		      &eclipticLong, &eclipticLat);

  ranow  *= HOUR_RAD;                 /* convert to hours */
  decnow *= DEG_RAD;                  /* convert to degrees */
  eclipticLong *= DEG_RAD;            /* convert to degrees */
  eclipticLat  *= DEG_RAD;            /* convert to degrees */

  /* get source location on the ecliptic */

  /*   vSun   = vsun_( &eclipticLong, &eclipticLat, &julianDate) + vEarth; */
  vSun = vEarth;

  helioToLsr( raJ2000, decJ2000, vSun, &vLsr); 

  *vEarthOut = vEarth;
  *vSunOut   = vSun;
  *vLsrOut   = vLsr;

  return(NULL);
} /* end of velocities */

