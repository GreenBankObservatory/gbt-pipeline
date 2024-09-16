/* File gbtAntenna.h, version 1.5, released  02/03/06 at 08:37:00 
   retrieved by SCCS 14/04/23 at 15:50:46     

%% describe the antenna motion overview and individaul measurements 

HISTORY
010516 GIL add support for gregorian focus receivers
010303 GIL SCCS Headers
010228 GIL add GBTPOSITION 
010226 GIL define parts of plot structure sizes

DESCRIPTION:
 gbtAntenna.h contains a description of the GBT Antenna FITS files
*/

struct ANTENNA {
  double dmjd;      /* date and time Modified Julian Days */
  double raJ2000;   /* ra az or long coord (rad) */
  double decJ2000;  /* dec, el or lat coord */
  double mnt_az;    /* raw azimuth value (rad) */
  double mnt_el;    /* raw elevation value */
  double coordA;    /* ra az or long coord (rad) */
  double coordB;    /* dec, el or lat coord */
  double refract;   /* refraction correction (rad) */
  double X;         /* sub-ref or PF X position (mm) */
  double Y;         /* sub-ref or PF Y position (mm) */
  double Z;         /* sub-ref or PF Y position (mm) */
};

#define LENMODELSTR 40

struct GBTPOSITION {
  double siteLat;   /* latitude (rad) NAD 83 */
  double siteLon;   /* longitude (rad) */
  double siteElev;  /* site elevation (m) */
  double lstStart; /* lst time at start of scan (radians) */
  double deltaUtc; /* UT1 - UTC offset for beginning of scan */
  double iersPMX;  /* X Polar motion correction for beginning of scan */
  double iersPMY;  /* Y Polar motion correction beginning of scan */
  double mntOffAz; /* Azimuth servo encoder offset */
  double mntOffEl; /* Elevation servo encoder offset */
  double lpcAz1;   /* First azimuth local zero point correction coeff */
  double lpcAz2;   /* Second azimuth local zero point correction coef */
  double lpcEl;    /* Elevation local zero point correction coefficie */
  char pointmodel[LENMODELSTR];      /* Type az/el pointing correction model */
  double pntAzD00;                   /* Horizontal collimation coefficient */
  double pntAzB01;                   /* Elevation Axis collimation coeff. */
  double pntAzD01;                   /* Azimuth zero */
  double pntAzA11;                   /* Zenith E tilt */
  double pntAzB11;                   /* Zenith N tilt */
  double pntAzC21;                   /* Azimuth track */
  double pntAzD21;                   /* Azimuth track */
  double pntElD00;                   /* Elevation zero */
  double pntElC10;                   /* Zenith E tilt */
  double pntElD10;                   /* Zenith N tilt */
  double pntElB01;                   /* Asymmetric gravity */
  double pntElD01;                   /* Symmetric gravity */
  char   diAbMode[LENMODELSTR];      /* State of diurnal aberration corr. */
  char   polarMnt[LENMODELSTR];      /* State of polar motion correction par.*/
  char   cosVMode[LENMODELSTR];      /* State of cosVMode parameter */
  double ambTemperature;             /* Ambient Temperature C */
  double ambPressure;                /* Ambient Pressure in milliBars */
  double ambHumidity;                /* Ambient Humidity fraction */
  char   subreflector[LENMODELSTR];  /* Optical path configuration */
  char   focusTracking[LENMODELSTR]; /* Focus tracking mode selection */
  char   parallactic[LENMODELSTR];   /* Parallactic angle tracking selection */
};
