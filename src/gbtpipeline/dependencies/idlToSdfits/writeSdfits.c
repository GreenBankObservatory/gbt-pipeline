/* File writeSdfits.c, version 1.36, released  12/04/09 at 16:15:36 
   retrieved by SCCS 14/04/23 at 15:50:50     

%% write an AIPS single dish fits file from a idl structure
:: TEST C program
 
HISTORY:
  111027 GIL force nPol = nIf if required
  101014 GIL reduce printout, use pid as part of temporary file name
  100908 GIL fix image sizes
  100728 GIL write a few more keywords for AIPS imaging downstream
  091230 GIL check that all integrations have the same milliMjd, if written
  080225 GIL add Alternate Ref Pix and value, to allow velocities in AIPS
  070705 GIL deal with HELiocentric
  070618 GIL fix CRVAL = -1 for LL or RR
  070604 GIL fix order to be stokes then channels
  070601 GIL more diagnostic data
  060308 GIL different numbers of polarizations
  060307 GIL deal with only one polarization
  060119 GIL print more info about scan with missing data
  051025 GIL fix case of not much data, keep skip Count > 0
  051020 GIL use idToScanIntegration() 
  050908 GIL print more info if discarding polarizations
  050906 GIL disable FREQ-LSR etc, do not write GALACTIC info
  050902 GIL try to fix GALACTIC coordinates in random parameters
  050901 GIL write units
  050830 GIL version that uses gbtGo.h to set some output parameters
  050815 GIL version that works with idlToSdfits.c
  050503 GIL write some AIPS info to set the data sort order
  050502 GIL write two temporary files, not keep one large temporary array
  050502 GIL get host name for use in check for going beyond end of data array
  050428 GIL check for going beyond end of data array
  050407 GIL change printout
  050404 GIL reduce printout
  050104 GIL flag data if tSys is negative
  050103 GIL comment fixes
  050101 GIL fix writing of the random parameters
  041229 GIL update antenna sample field
  041228 GIL write coordinates, scan/integration numbers and time + date
  041227 GIL fix header writing
  041222 GIL rudimentary version
  041221 GIL use idl structures, not patterns
  041220 GIL inital version that compiles
  041217 GIL inital version for IDL
  021211 GIL inital version based on gbtObsSummary.c
 
DESCRIPTION:
Write an AIPS single dish fits file from a GBT observation and a
group of idl structures
*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include "math.h"
#include "dirent.h"
#include "fitsio.h"
#include "MATHCNST.H"
#include "STDDEFS.H"
#include "gbtIdl.h"
#include "gbtAntenna.h"
#include "gbtDcr.h"
#include "gbtGo.h"
#include "gbtTCal.h"
#include "gbtScanInfo.h"
#include "gbtSpectrometer.h"

/* externals */
STATUS mjd2date (long mjd, int * pYear, int * pMonth, int * pDay);   
char * rad2str( double, char *, char *);
char * mjd2str( long, char *);
char * str2mjd( char *, long *);
char * stripWhite( char *);
char * cvrtuc( char *);
void medianFilter ( int count, int medWid2, double inarr[], double outarr[]);
extern double median4 ( double a, double b, double c, double d);
char * dateObsKey( long mjd, double utc, char * dateString);
char * parseDates( int argc, char * argv[], long * pIndex, long * minMjd, 
		   double * minUtc, long * maxjd, double * maxUtc);
extern char * parseDatesHelp();
extern char * str2rad( char *, double *);
extern char * dateObs2DMjd( char * dateObs, double * dMjd);
extern long today2mjd();
extern void shellSort(long n, double a[]);
extern void radec2azel( double ra, double dec,    /* take ra, dec (radians) */
            double lst, double lat,               /* need lst time, latitude */
	    double * azimuth, double *elevation); /* calc az, el */
extern void azel2radec( double az, double el,         /* take az,el (radians)*/
            double lst, double lat,                   /* need lst time, lat  */
	    double * raOut, double * decOut);         /* calc ra, dec */
extern double gastm(long mjd);
extern int date2J2000 (long mjd, double utc, double ranow, double decnow, 
		       double * ra2000, double * dec2000);
extern int now2J2000 (long mjd, double utc, double ranow, double decnow, 
		       double * ra2000, double * dec2000);
void radec2azel( double ra, double dec,          /* take ra, dec (radians) */
            double lst, double lat,              /* need lst time, latitude */
	    double * azimuth, double *elevation);/* calc az, el */
extern void obsposn (long mjd, double utc, double ra2000, double dec2000, 
	      double * ranow, double * decnow);
extern int ffpbyt(fitsfile *fptr,   
		  /* I - FITS file pointer                    */
           long nbytes,      /* I - number of bytes to write             */
           void *buffer,     /* I - buffer containing the bytes to write */
           int *status);     /* IO - error status                        */
extern char *  raDec2gLatLon( double ra, double dec, 
			      double * gLat, double * gLon);
extern char *  gLatLon2RaDec( double gLat, double gLon,
			      double * ra, double * dec);
extern int mjd2AIPS( int inMJD, char * dateStr, char * mapStr);
extern char * getIdl( long scanNumber, long maxN, GBTIDL * outIdls[], 
		      long * nOut);
extern struct ANTENNA gbtAntenna;
extern struct GOPARAMETERS go;
extern void printerror( int status);
extern char * idToScanIntegration( long id, long * scan, long * integration);

/* internals */
/* This should match the SOFTVERSION in mainIdlToSdfits.c */
#define SOFTVERSION    "8.6"
#define MAXNAMELENGTH  512
#define MAXFITSLINE     80
#define MAXPOLS          4

#define J2000    0
#define B1950    1
#define AZEL     2
#define GALACTIC 3
/* Weight for data is inversely proportional to time*T_sys^2.  To make weight*/
/* values near unity, set the reference system temperature (arbitrary) value */
#define REFTSYS  25.             /* set reference Tsys to 25 K for weight */

#define MAXMEDIAN (2*4096)
#define MAGIC      -99999.

#define NRANDOM      6
/* the dataArray must be as large as twice the largest single spectrum */
#define FITSDATA  10000000
static float dataArray[FITSDATA];
extern struct GBTPOSITION gbtPos;
long gbtGoInit = FALSE;

char * getHost( char * hostName)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* getHost() returns the ASCII string name of the host running the program   */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ FILE * hostPipe = NULL;
  long pid = getpid();
  char hostStr[60]= "", pidStr[30]="";

  hostPipe = popen("printenv HOST","r"); /* get GMT time from cpu */
  fgets(hostStr, 50, hostPipe);             /* read in string */
  pclose( hostPipe);
  hostStr[49] = '\0';                       /* terminate string */
  stripWhite(hostStr);
  sprintf( pidStr, "%ld", pid);
  stripWhite(pidStr);
  strcpy( hostName, hostStr);
  strcat( hostName, ".");
  strcat( hostName, pidStr);
  return(NULL);
} /* end of getHost() */

char * gbtInit( struct GOPARAMETERS * pGo, struct GBTPOSITION * pGbtPos,
		long *pGoInit)
{ long i = 0;
  if (*pGoInit == FALSE) { 
    bzero( pGo, sizeof( struct GOPARAMETERS));
  }
  *pGoInit = TRUE;

  for (i = 0; i < FITSDATA; i++)   /* zero scratch */
    dataArray[i] = 0.;
  return(NULL);
} /* end of gbtInit() */

double wrapLimit( double value, double maxV)
/* wrapLimit() returns limited input value to between 0 and a maximum value */
/* OMISSIONS: Only handles values between -maxV and 2*maxV case */
{ double outV = value;

  if (outV > maxV)
    outV -= maxV;
  else if (outV < 0.)
    outV += maxV;
  return( outV);
} /* end of wrapLimit() */

char * initIdlSdfits( fitsfile *fptr,
		      long coordType, long nPol, long nScans, GBTIDL * pIdl)
{ int status = 0, naxis = NRANDOM, extend = TRUE, 
    bitpix = FLOAT_IMG;
  long  pcount = 4, gcount = 0, naxes[NRANDOM] = {0, 3, 2, 1, 1, 1}, nChan = 0,
    mjd = 0, scanNumber = 0, integration = 0, iCenterFreq = 0,
    cellsize = 5, imsize1 = 150, imsize2 = 150;
  char comment[MAXNAMELENGTH] = "GBT location and pointing data",
    origin[] = "NRAO, Green Bank", receiver[MAXNAMELENGTH] = "", 
    history[MAXNAMELENGTH] = "", strCenterFreq[MAXNAMELENGTH] = "",
    dateStr[MAXNAMELENGTH] = "", mapStr[MAXNAMELENGTH] = "";
  double bzero = 0, bscale = 1, az = 0, el = 0,  diameterCm = 1E4, 
    lambdaCm = 1, bmajDeg = 0.01, 
    dAz = 0, dEl = 0, dRefraction = 0, bandWidth = 0, dMjd = 0, cRVal3 = 1,
    cDVal3 = -1., altRefPix = 0.;

  /* write the required keywords for the primary array image.     */
  status=0;
  nChan = pIdl->data_points;
  gcount = nScans;
  naxes[2] = nPol;
  naxes[3] = nChan;

  /* write fits group header */
  if ( fits_write_grphdr(fptr, TRUE, bitpix, naxis, naxes, pcount,
			 gcount, extend, &status) ) {
    printerror( status);
    fprintf( stderr, "Error Writing to Temporary FITS file\n");
    return("Error writing to Temporary FITS file");
  }

  fits_update_key(fptr, TDOUBLE, "BZERO", &bzero, "Zero Level", &status);
  fits_update_key(fptr, TDOUBLE, "BSCALE", &bscale, "Scale value", &status);

  fits_write_key_dbl( fptr, "SITELAT", 
			    gbtPos.siteLat, -15, comment, &status);
  fits_write_key_dbl( fptr, "SITELONG", 
			    gbtPos.siteLon, -15, comment, &status);
  fits_write_key_dbl( fptr, "SITEELEV", 
			    gbtPos.siteElev, -15, comment, &status);
  fits_write_key_dbl( fptr, "LPC_AZ1", 
			    gbtPos.lpcAz1, -15, comment, &status);
  fits_write_key_dbl( fptr, "LPC_AZ2", 
		            gbtPos.lpcAz2, -15, comment, &status);
  fits_write_key_dbl( fptr, "LPC_EL", 
			    gbtPos.lpcEl, -15, comment, &status);
  fits_write_key_str( fptr, "ORIGIN", origin,
		     "WV 24944  304-456-2011", &status);
  fits_write_key_str( fptr, "TELESCOP", go.telescope,
		     "Robert C. Byrd", &status);
  fits_write_key_str( fptr, "BUNIT", pIdl->calibrate,
		     "JY/BEAM or K/BEAM", &status);
  fits_write_key_str( fptr, "CTYPE2", "COMPLEX", 
		     "Signal, Baseline, Weight", &status);
  fits_write_key_dbl( fptr, "CRVAL2", 1.0, -15, "", &status);
  fits_write_key_dbl( fptr, "CDELT2", 1.0, -15, "", &status);
  fits_write_key_dbl( fptr, "CRPIX2", 1.0, -15, "", &status);
  fits_write_key_dbl( fptr, "CROTA2", 0.0, -15, "", &status);
  fits_write_key_str( fptr, "CTYPE3", "STOKES", 
		     "X, Y or R, L/", &status);

  if (strstr( pIdl->pol_id, "RR" ) || strstr( pIdl->pol_id, "LL" ))
    cRVal3 = -1;
  else if (strstr( pIdl->pol_id, "RL" ))
    cRVal3 = -3;
  else if (strstr( pIdl->pol_id, "LR" ))
    cRVal3 = -4;
  else if (strstr( pIdl->pol_id, "YY" ) || strstr( pIdl->pol_id, "XX" ))
    cRVal3 = -5;
  else if (strstr( pIdl->pol_id, "XY" ))
    cRVal3 = -7;
  else if (strstr( pIdl->pol_id, "YX" ))
    cRVal3 = -8;
  else if (strstr( pIdl->pol_id, "V" ))
    cRVal3 = 4;
  else if (strstr( pIdl->pol_id, "U" ))
    cRVal3 = 3;
  else if (strstr( pIdl->pol_id, "Q" ))
    cRVal3 = 2;
  else if (strstr( pIdl->pol_id, "X" ))
    cRVal3 = -5;
  else if (strstr( pIdl->pol_id, "Y" ))
    cRVal3 = -6;
  else
    cRVal3 = 1;

  /*    fprintf( stderr, "Stokes %s: %7.0lf\n", pIdl->pol_id, cRVal3); */
  fits_write_key_dbl( fptr, "CRVAL3", cRVal3, -15, "", &status);
  fits_write_key_dbl( fptr, "CDELT3", cDVal3, -15, "", &status);
  fits_write_key_dbl( fptr, "CRPIX3", 1.0, -15, "", &status);
  fits_write_key_dbl( fptr, "CROTA3", 0.0, -15, "", &status);
  /* VELREF  =                    1 /1 LSR, 2 HEL, 3 OBS, +256 Radio  */
  if (strstr( pIdl->vel_def, "LSR")) {
    /*    fits_write_key_str( fptr, "CTYPE4", "FREQ-LSR", 
	  "frequency in LSR frame", &status); */
    fits_write_key_str( fptr, "CTYPE4", "FREQ", 
			"frequency in LSR frame", &status);
    if (strstr( pIdl->vel_def, "RAD"))
      fits_write_key_lng( fptr, "VELREF", 257, 
			   "1 LSR, 2 HEL, 3 OBS, +256 Radio", &status);
    else
      fits_write_key_lng( fptr, "VELREF", 1, 
			   "1 LSR, 2 HEL, 3 OBS, +256 Radio", &status);
  }
  else if (strstr(pIdl->vel_def, "BAR") ||
	   strstr(pIdl->vel_def, "HEL")) {
    /*    fits_write_key_str( fptr, "CTYPE4", "FREQ-HEL",  
	  "frequency in BARYCENTRIC", &status); */
    fits_write_key_str( fptr, "CTYPE4", "FREQ", 
			"frequency in BARYCENTRIC", &status);
    status = 0;
    if (strstr( pIdl->vel_def, "RAD") != 0)
      fits_write_key_lng( fptr, "VELREF", 258, 
			   "1 LSR, 2 HEL, 3 OBS, +256 Radio", &status);
    else
      fits_write_key_lng( fptr, "VELREF", 2, 
			   "1 LSR, 2 HEL, 3 OBS, +256 Radio", &status);
  }
  else {
    /*    fits_write_key_str( fptr, "CTYPE4", "FREQ-OBS", 
	  "frequency in Topocentric", &status); */
    fits_write_key_str( fptr, "CTYPE4", "FREQ", 
			"frequency in Topocentric", &status);
      fits_write_key_lng( fptr, "VELREF", 3, 
			   "1 LSR, 2 HEL, 3 OBS, +256 Radio", &status);
  }
  bandWidth = (nChan-1.) * pIdl->delta_x;
  fits_write_key_dbl( fptr, "RESTFREQ", pIdl->rest_freq, 
			-15, "", &status);

  iCenterFreq = (pIdl->sky_freq + ((nChan/2.) - pIdl->ref_ch)*pIdl->delta_x)
    / 1000000.;
  sprintf( strCenterFreq, "%ld", iCenterFreq);


  /* if the rest frequency is defined, then define zero velocity pixel */
  if (pIdl->rest_freq > 0. && pIdl->delta_x != 0.) {
    fits_write_key_dbl( fptr, "ALTRVAL", (double)0.,
			-15, "", &status);
    altRefPix = pIdl->ref_ch + ((pIdl->rest_freq - pIdl->sky_freq)/pIdl->delta_x);
    fits_write_key_dbl( fptr, "ALTRPIX", altRefPix,
			-15, "", &status);
  } /* if a rest frequency */

  fits_write_key_dbl( fptr, "BANDWIDT",  bandWidth,
			-15, "", &status);
  if (nChan > 0) {            /* if any IF data available */
    fits_write_key_dbl( fptr, "CRVAL4", pIdl->sky_freq, 
			-15, "", &status);
    fits_write_key_dbl( fptr, "CDELT4", pIdl->delta_x,
			-15, "", &status);
    fits_write_key_dbl( fptr, "CRPIX4", pIdl->ref_ch, -15, "", &status);
  }
  else {                    /* else use default from first obs */
    fits_write_key_dbl( fptr, "CRVAL4", 7.9E8, -15, "", &status);
    fits_write_key_dbl( fptr, "CDELT4", 1.0E6, -15, "", &status);
    fits_write_key_dbl( fptr, "CRPIX4", 1.0, -15, "", &status);
  }
  fits_write_key_dbl( fptr, "CROTA4", 0.0, -15, "", &status);
  fits_write_key_dbl( fptr, "CDELT5", 1.0, -15, "", &status);
  fits_write_key_dbl( fptr, "CRPIX5", 1.0, -15, "", &status);
  fits_write_key_dbl( fptr, "CROTA5", 0.0, -15, "", &status);

  coordType = J2000;

  if (coordType == GALACTIC) {
    fits_write_key_str( fptr, "CTYPE5", "GLON",
			"Galactic Longitude", &status);
    fits_write_key_str( fptr, "CTYPE6", "GLAT",
			"Galactic Latitude", &status);
  }
  else {
    fits_write_key_str( fptr, "CTYPE5", "RA",
		     "Right Ascension", &status);
    fits_write_key_str( fptr, "CTYPE6", "DEC",
			"Declination", &status);
  }

  /*  fits_write_key_dbl( fptr, "CDELT6", 1.0, -15, "", &status); */
  /*  fits_write_key_dbl( fptr, "CRPIX6", 1.0, -15, "", &status); */
  fits_write_key_dbl( fptr, "CROTA6", 0.0, -15, "", &status);
  /*  fits_write_key_dbl( fptr, "CDELT6", 1.0, -15, "", &status); */
  /*  fits_write_key_dbl( fptr, "CRPIX6", 1.0, -15, "", &status); */
  fits_write_key_dbl( fptr, "CROTA6", 0.0, -15, "", &status);

  if (go.equinox < 1900.)
    go.equinox = 2000.;

  fits_write_key_dbl( fptr, "EPOCH", go.equinox, -15, 
		     "RA Dec reference epoch", &status);
  if (coordType == GALACTIC) 
    fits_write_key_str( fptr, "PTYPE1", "GLON", 
			"Galactic Longitude in Degrees", &status);
  else
    fits_write_key_str( fptr, "PTYPE1", "RA", 
			"RA in Degrees", &status);

  fits_write_key_dbl( fptr, "PSCAL1", 1.0/DEGREE, -15, 
		     "Unit conversion factor", &status);
  fits_write_key_dbl( fptr, "PZERO1", 0.0, -15, 
		     "Unit conversion factor", &status);
  if (coordType == GALACTIC) 
    fits_write_key_str( fptr, "PTYPE2", "GLAT", 
			"Galactic Latitude in Degrees", &status);
  else
    fits_write_key_str( fptr, "PTYPE2", "DEC", 
			"Declination in Degrees", &status);

  fits_write_key_dbl( fptr, "PSCAL2", 1.0/DEGREE, -15, 
		     "Unit conversion factor", &status);
  fits_write_key_dbl( fptr, "PZERO2", 0.0, -15, 
		     "Unit zero value", &status);
  fits_write_key_str( fptr, "PTYPE3", "BEAM", 
		     "point number*256 + Scan", &status);
  fits_write_key_dbl( fptr, "PSCAL3", 1.0, -15, 
		     "Unit conversion factor", &status);
  fits_write_key_dbl( fptr, "PZERO3", 0.0, -15, 
		     "Unit zero value", &status);
  fits_write_key_str( fptr, "PTYPE4", "DATE", 
		     "Date+time in Julian date (days)", &status);
  fits_write_key_dbl( fptr, "PSCAL4", 1.0, -15, 
		     "Unit conversion factor", &status);

  dateObs2DMjd( pIdl->date, &dMjd);  /* get modified julian day of obs */
  mjd = dMjd;                        /* truncate to integer */
  fits_write_key_dbl( fptr, "PZERO4", (double)mjd+2.4000005E6, -15, 
     "Unit zero value", &status); 
  fits_write_key_str( fptr, "OBJECT", go.object,
		     "DistantCreation", &status);
  fits_write_key_str( fptr, "IMCLASS", strCenterFreq, 
		     "Class is Center Freq (MHz)", &status);
  fits_write_key_str( fptr, "IMNAME", go.object,
		     "WV 24944  304-456-2011", &status);
  fits_write_key_str( fptr, "SORTORD", "TB", 
		     "Data time sorted for efficiency", &status);

  /* mjd2AIPS( (int)go.dateObs, dateStr, mapStr); */
  mjd2AIPS( mjd, dateStr, mapStr);
  fits_write_key_str( fptr, "DATE-OBS", dateStr,
		     "UTC Date of observation", &status);
  idToScanIntegration( pIdl->scan_num, &scanNumber, &integration);
  fits_write_key_lng( fptr, "SCAN", scanNumber,
		     "GBT M&C Scan Number", &status);
  fits_write_key_str( fptr, "OBSERVER", go.observer,
		     "Student of the Universe", &status);
  fits_write_key_str( fptr, "PROJID", go.projectId,
		     "Study of the Universe", &status);
  sscanf( pIdl->history, "%s %s", receiver, history);
  fits_write_key_str( fptr, "INSTRUME", receiver,
		     "Front End", &status);

  fits_write_key_dbl( fptr, "REFRACT", dRefraction/DEGREE, -15,
		     "Refraction model (deg)", &status);
  fits_write_key_dbl( fptr, "DAZMODEL", dAz/DEGREE, -15,
		     "Azimuth   offset (deg) at reference pos.", &status);
  fits_write_key_dbl( fptr, "DELMODEL", dEl/DEGREE, -15,
		     "Elevation offset (deg) at reference pos.", &status);

  if (coordType == J2000 || coordType == B1950) {
    if (coordType == B1950)
      fits_write_key_str( fptr, "COORDTYP", "B1950",
			  "Coordiante Type", &status);
    else
      fits_write_key_str( fptr, "COORDTYP", "J2000",
			  "Coordiante Type", &status);
    fits_write_key_dbl( fptr, "CRVAL5", go.ra2000/DEGREE, -15,
		      "Right Ascension of Center", &status);
    fits_write_key_dbl( fptr, "CRVAL6", go.dec2000/DEGREE, -15,	
		      "Declination of Center", &status);
  }
  else if (coordType == AZEL) {
    fits_write_key_str( fptr, "COORDTYP", "AZEL-OFF",
		     "Coordiante Type", &status);
    fits_write_key_dbl( fptr, "CRVAL5", (double)0.0, -15,
		      "Azimuth offset relative to Source", &status);
    fits_write_key_dbl( fptr, "CRVAL6", (double)0.0, -15,	
		      "Elevation offset relative to Source", &status);
    fprintf( stderr, "Writing Az,El offset positions for ");
    fprintf( stderr, "Az,El = %7.3f,%7.3f\n",
	     (double)az/DEGREE, (double)el/DEGREE);
  }
  else if (coordType == GALACTIC) {
    fits_write_key_str( fptr, "COORDTYP", "GALACTIC",
		     "Coordiante Type", &status);
    fits_write_key_dbl( fptr, "CRVAL5", go.gLon/DEGREE, -15,
		      "Galactic Longitude of Center", &status);
    fits_write_key_dbl( fptr, "CRVAL6", go.gLat/DEGREE, -15,	
		      "Galactic Latitude of center", &status); 
   fprintf( stderr, "Writing Galactic positions\n");
  }

  fits_write_history( fptr, 
     "SORTORD = 'TB      ' / Data time sorted                    ",
		      &status);     
  fits_write_history( fptr, 
     "AIPS   SORT ORDER = 'TB'                                   ",
		      &status);     
  fits_write_history( fptr, 
     "UVSRT  SORT = 'TB'   / New sort order                      ",
		      &status);     
  /* write some AIPS imaging keywords */
  if (pIdl->sky_freq > 0.) 
    lambdaCm = 100. * C_LIGHT / pIdl->sky_freq;
  if (diameterCm > 0.) {
    bmajDeg = 1.2 * lambdaCm / (DEGREE * diameterCm);
    cellsize = ceil(3600.*bmajDeg/6.);
  }
  fits_write_key_dbl( fptr, "BMAJ", bmajDeg, -15, 
		      "Angular Resolution (FWHM Degrees)", &status);
  fits_write_key_dbl( fptr, "BMIN", bmajDeg, -15, 
		      "Angular Resolution (FWHM Degrees)", &status);
  fits_write_key_dbl( fptr, "BPA", 0., -15, 
		      "Orientatio (Degrees)", &status);
  fits_write_key_lng( fptr, "CELLSIZE", cellsize,
		     "Desired Image Cellsize (arcsec)", &status);
  fits_write_key_dbl( fptr, "CDELT5", cellsize/3600., -15,
		     "Desired Image Cellsize (degree)", &status);
  fits_write_key_dbl( fptr, "CDELT6", cellsize/3600., -15, 
		     "Desired Image Cellsize (degree)", &status);
  /* the angular size of the image in radians is provided in a */
  /* global structure gbtPos.  iersPMX is the RA range in Radians */
  /* iersPMY is the Dec Range in Radians */
  /* cellsize is the the pixel size in degrees */
  /* estimate a good half-image size, multiply by 2 later*/
  imsize1 = (gbtPos.iersPMX * 1.1 / (2.*cellsize*ARCSEC));
  imsize2 = (gbtPos.iersPMY * 1.1 / (2.*cellsize*ARCSEC));
  /* must be an even number, round up add a few arcminute boarder */
  imsize1 = 2*(imsize1 + ceil(45./cellsize));
  imsize2 = 2*(imsize2 + ceil(45./cellsize));
  /* must increase image size by beam offset */
  if (imsize1 < 32)
    imsize1 = 32;
  if (imsize2 < 32)
    imsize2 = 32;
  fits_write_key_lng( fptr, "CRPIX5", imsize1,
		     "Desired Image X Size (pixels)", &status);
  fits_write_key_lng( fptr, "CRPIX6", imsize2,
		     "Desired Image Y Size (pixels)", &status);
  fits_write_history( fptr, pIdl->history, &status);     
  sprintf( comment, "idlToSdfits v%s      / idlToSdfits version number", 
	   SOFTVERSION);
  fits_write_history( fptr, comment, &status);     

  return(NULL);
} /* end of initIdlSdfits() */

char * endianFlip( unsigned char fourBytes[])
/* endianFlip() performs the big-endian little-endian byte order flip        */
/* Does both both forward and reverse flips; calling twice has no net effect */
/* Must be called with a 4 byte (32 bit) word                                */
{ unsigned char tempByte = fourBytes[0];

  fourBytes[0] = fourBytes[3];
  fourBytes[3] = tempByte;
  tempByte     = fourBytes[1];
  fourBytes[1] = fourBytes[2];
  fourBytes[2] = tempByte;

  return(NULL);
} /* end of endianFlip */

char * writeSdfits( char * fitsName, long nScans, long scanList[],
		    long coordType, long nIf)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* Create an AIPS SDFITS format data file.  This function uses the fitsio    */
/* package to generate the file keywords, then does a binary transfer of the */
/* fits format sample data.  Returns NULL on OK, else error message          */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ char tempFileName[MAXNAMELENGTH] = "./temp.SDFITS", *errMsg = NULL,
    hostName[MAXNAMELENGTH] = "", tempDataName[MAXNAMELENGTH] = "";
  int status = 0;
  long  maxN = MAXPOLS, nIdl = 0, n = 0, i = 0, j = 0, nBytes = 0, k = 0, 
    debugPrint = 5, maxDebugPrint = 5, mjd = 0, iScan = 0, nPol = 0, 
    nRead = 0, nChan = 0, dN = 0, nOut = 0, nBlocks = 0, skipCount = 2000,
    nTotal = 0, iS = 0, scanNumber = 0, integration = 0, polCount[MAXPOLS],
    iPol = 0, lastNIdl = 0, dN1 = 0, dN2 = 0, nData = 0, iScan0 = 0,
    nTSys[MAXPOLS];
  /* initialize FITS image parameters */
  double utc = 0, ra2000 = go.ra2000*DEGREE, dec2000 = go.dec2000*DEGREE, 
    az = 0, el = 0, dMjd = 0, dMjdRef = 0., weights[MAXPOLS],
    tSys[MAXPOLS], tInt[MAXPOLS];
  unsigned char fitsBlock[2*2880];
  fitsfile *fptr =  NULL;     /* FITS file, defined in fitsio.h*/
  FILE  *tempFile = NULL, *fitsFile =  NULL,
    *dataFile = NULL;    /* FITS file, do binary dump */
  GBTIDL * idls[MAXPOLS], * pIdl = NULL;

  if (nScans <= 0) {
    fprintf( stderr, "writeSdfits: No Scans to write!\n");
    return("No data to write!");
  }

  getHost( hostName);
  sprintf( tempFileName,"./write.%s.Header", hostName);
  remove( tempFileName);      /* must delete to start with fresh temp. file */

  sprintf( tempDataName, "./write.%s.Data", hostName);
  remove( tempDataName);      /* must delete to start with fresh temp. file */

  /* create new FITS file for writing keywords */
  if (fits_create_file( &fptr, tempFileName, &status)) {
    fprintf( stderr, "Error Creating FITS file: %s\n", tempFileName);
    return( "writeSdfits: error creating fits file");
  }

  /* create new temporary data file for writing keywords */
  if (( dataFile = fopen( tempDataName, "w")) == NULL) {
    fprintf( stderr, "Error Creating temporary FITS data file: %s\n", 
	     tempDataName);
    return( "writeSdfits: error creating fits data file");
  }

  status = 0;         /* initialize status before calling fitsio routines */

  /* init the count of each of the different number of polarizations */
  for (iPol = 0; iPol < MAXPOLS; iPol++) {
    polCount[iPol] = 0;
    nTSys[iPol] = 0;
    tSys[iPol] = 0;
    tInt[iPol] = 0;
  }

  /* for scans in list, read number of polarizations */
  for (iS = 0; iS < nScans; iS++) {
    iScan = scanList[iS];
    getIdl( iScan, maxN, idls, &nIdl);
    if (nIdl > 0 && nIdl <= MAXPOLS) 
      polCount[nIdl-1] = polCount[nIdl-1] + 1;
    else {
      if (nIdl <= 0)
	fprintf( stderr, "Scan %ld: No polarizations; %ld\n",
	       iScan, nIdl);
      else
	fprintf( stderr, "Scan %ld: Invalid number of polarizations; %ld\n",
	       iScan, nIdl);
    }
  } /* end for all scan/integrations in the list */      

  /* now find the maximum number of polarizations */
  for (iPol = MAXPOLS-1; iPol >= 0; iPol --) {
    if (polCount[iPol] > 0) {
      nPol = iPol+1;
      break;
    }
  }

  if (nPol < 1) {
    fprintf( stderr, "No scans have data, exiting\n");
    return("No Scans have data");
  }
    
  if (nIf >= 1 && nIf <= nPol) {
    if (nIf != nPol)
      fprintf( stderr, "Enforcing Number of Polarizations: %ld (%ld)\n",
	       nIf,nPol);
    nPol = nIf;
  } /* end if enforcing a number of polarizations */

  for (iPol = 0; iPol < nPol; iPol++) {
    if (polCount[iPol] > 0) 
      if (debugPrint < maxDebugPrint)
	fprintf( stderr, 
	       "%ld Scan-Integrations have %ld polarization measurement(s)\n",
	       polCount[iPol], iPol+1);
  }

  for (iS = 0; iS < nScans; iS++) {
    iScan = scanList[iS];
    getIdl( iScan, maxN, idls, &nIdl);
    for (iPol = 0; iPol < nIdl; iPol++) {
      nTSys[iPol] = nTSys[iPol] + 1;
      tSys[iPol] = tSys[iPol] + idls[iPol]->tsys;
      tInt[iPol] = tInt[iPol] + idls[iPol]->tintg;
    } /* end for all polarizations in this int. */
  } /* end for all integrations */

  for (iPol = 0; iPol < nIdl; iPol++) {
    if (nTSys[iPol] > 0) {
      tSys[iPol] = tSys[iPol]/nTSys[iPol];
      tInt[iPol] = tInt[iPol]/nTSys[iPol];
    }
    if ( tSys[iPol] > 0.)/* weight relative to TSYS * 1 s */
      weights[iPol] = tInt[iPol]*(REFTSYS/tSys[iPol]) * (REFTSYS/tSys[iPol]); 
    else 
      weights[iPol] = -1.;                         /* else just flag data */
    if (debugPrint < maxDebugPrint)
      fprintf( stderr, "Data Weights: %ld, %10.3lf\n", iPol, weights[iPol]);
  }

  n = 0;
  /* for all scans/integrations */
  for (iS = 0; iS < nScans; iS++) {
    iScan = scanList[iS];
    getIdl( iScan, maxN, idls, &nIdl);
      
    if (nIdl < 1)       /* if no idl structures, then we're out of data */
      break;

    if (iS == 0)
      lastNIdl = nIdl;
    
    pIdl = idls[0];     /* get pointer to data structure */
    if (pIdl == NULL) {
      fprintf( stderr, 
	       "Null Idl structure pointer, no data for integration\n");
      continue;
    }

    idToScanIntegration( pIdl->scan_num, &scanNumber, &integration);
    if (iS == 0)        /* label scans relative to the first one */
      iScan0 = pIdl->scan_num - 1;
    if (iScan0 < 128)   /* but if a small scan number keep scan number */
      iScan0 = 0;
    if (nIdl != nPol) { /* if polarizations for this scan not usual number */
      pIdl = idls[0];
      fprintf( stderr, 
	  "!writeSdfits: nIdl=%ld not %ld; Kept Pol %s Scan %ld Int. %ld\n",
	  nIdl, nPol, idls[0]->pol_id, pIdl->scan_num, pIdl->iIntegration);
    } /* end if not standard number of polarizations */

    dateObs2DMjd( pIdl->date, &dMjd);
    mjd = dMjd;
    utc = (dMjd - mjd)*TWOPI;

    if (iScan < 0)
      fprintf ( stderr, "Scanlist[%4ld] = %ld with %ld (%s)\n", 
	      i, iScan, nIdl, pIdl->date);
    el = pIdl->el;                 /* az,el in degrees for printing */
    az = pIdl->az;
    nChan = pIdl->data_points;

    if (nOut == 0) { /* on first point, initialize the file header */
      errMsg = initIdlSdfits( fptr, coordType, nPol, nScans, pIdl);
      dMjdRef = mjd;
      fits_close_file(fptr, &status); 
    }
  
    /* if outputting az el offsets relative to the source position */
    if (coordType == AZEL) {
      dataArray[n + 0] = pIdl->az;
      dataArray[n + 1] = pIdl->el;
    } /* end if outputing az,el */
    else { /* else outputing J2000 RA, dec, or galactic */
      ra2000  = pIdl->ra;
      dec2000 = pIdl->dec;
      /* insert ra, dec, scan # and time into random group parameter */
      dataArray[n + 0] = ra2000*DEGREE;
      dataArray[n + 1] = dec2000*DEGREE;
    } /* end else an ra/dec coordinate */

    /* Scan ## == AIPS antenna 1 & Integration == baseline value */    
    dataArray[n + 2] = (((pIdl->scan_num-iScan0)%255)*256)+
      ((1+pIdl->iIntegration)%255); 
    dataArray[n + 3] = dMjd-dMjdRef; /* date is relative to first MJD     */

    if (debugPrint < maxDebugPrint) 
      fprintf( stderr, "1-4: %7.3f %7.3f %7.3f %7.3f\n", 
	       dataArray[n], dataArray[n+1], dataArray[n+2], 
	       dataArray[n+3]);
    n += 4;                                 /* skip past 4 random parameters */
    nOut += 4;
  
    nData = n;
    for (j = 0; j < 3*nPol; j++) {          /* zero in case of flagged */
      for (k = 0; k < nChan; k++) {         /* for all channels */
	dataArray[nData] = 0;
	nData++;
      }
    } /* end for all polarizations in all scans */

    /*data order:reA-1, imA-1, weA-1, reB-1, imB-1, weB-1, reA-2, imA-2, we-2*/
  
    for (j = 0; j < nIdl; j++) {          /* for all polarizations */
      if (idls[j] != NULL) {              /* if data pointer valid */
        if (nIdl == nPol)                 /* if expected number of pols */
	  dN = j*3;

	if (nPol == 2) {                  /* if exactly two polarizations */
	  if ( idls[j]->pol_id[0] == 'X' || idls[j]->pol_id[0] == 'R' ||
	       idls[j]->pol_id[0] == 'I') 
	    dN = 0;
	  else 
	    dN = 3;
	}
	else {
	  if (strstr( idls[j]->pol_id, "XX") ||
	      strstr( idls[j]->pol_id, "RR")) 
	    dN = 0;
	  else if (strstr( idls[j]->pol_id, "YY") ||
		   strstr( idls[j]->pol_id, "LL")) 
	    dN = 3;
	  else if (strstr( idls[j]->pol_id, "XY") ||
		   strstr( idls[j]->pol_id, "RL")) 
	    dN = 6;
	  else 
	    dN = 9;
	}
	if (dN > ((nPol-1)*3))    /* do not go beyond end of data */
	  dN = ((nPol-1)*3);

	/*  fprintf( stderr, 
	 "scan:%4ld int:%4ld n:%9ld; nOut:%9ld dN:%9ld nPol:%3ld j:%3ld\n",   
	 iScan, integration, n, nOut, dN, nPol, j); */

	for (k = 0; k < nChan; k++) {           /* for all channels */
	  /* now insert data, Tsys, cal counts and weight for each pol. */
	  dataArray[n+(k*3*nPol)+dN] = idls[j]->data[k];    /* real */
	  dataArray[n+(k*3*nPol)+dN+1] = 0.;       /*  baseline imaginary */
	  dataArray[n+(k*3*nPol)+dN+2] = weights[j];   /* weight */
	} /* end if data in array */
      } /* end if not a flagged spectrum */

    } /* end for all polarizations */

    if (debugPrint < maxDebugPrint) {
      dN1 = 0;  dN2 = 3;
      fprintf( stderr, "%7.3f %7.3f %7.3f %7.3f %7.3f %7.3f\n", 
	       dataArray[n+dN1],dataArray[n+dN1+1], dataArray[n+dN1+2],
	       dataArray[n+dN2],dataArray[n+dN2+1], dataArray[n+dN2+2]);
      dN1 = 3*nChan;  dN2 = (3*nChan) + 3;
      fprintf( stderr, "%7.3f %7.3f %7.3f %7.3f %7.3f %7.3f\n", 
	       dataArray[n+dN1],dataArray[n+dN1+1], dataArray[n+dN1+2],
	       dataArray[n+dN2],dataArray[n+dN2+1], dataArray[n+dN2+2]);
      debugPrint ++;
    } /* end if debugging */

    nOut = nOut + (nPol*3*nChan);    /* nOut always increases */
    n = n + (nPol*3*nChan);          /* n increases then decreases at write*/
  
    if (n >= FITSDATA) {
      k = FITSDATA;
      fprintf( stderr, "Max output data size exceeded: %ld\n", k);
      break;
    }
    if (debugPrint < maxDebugPrint) {
      fprintf( stderr, "\n");
      debugPrint++;
    }
      
    nBlocks = (n/720);
    nTotal += nBlocks;
    /* if gathered more than 1 block of data */
    if (nBlocks > 0) {
      for (i = 0; i < (nBlocks*720); i = i + 720) 
        fwrite( (void *)&dataArray[i], 2880, 1, dataFile);

      n = n - (nBlocks*720);    /* now compute data left un-written */

      /* now move the rest of the data array to the front of the buffer */
      for (j = 0; j < n; j++) 
        dataArray[j] = dataArray[j+(nBlocks*720)];
     
    } /* if enough data collected to write a block */
  } /* end for all integrations */
  
  /* pad data to zero last block of fits 2880 byte buffer */
  for (i = 0; i < 720; i++)
    dataArray[n+i] = 0;

  nBlocks = n/720;

  if (nBlocks * 720 != n)
    nBlocks++;

  nTotal += nBlocks;
  /* now write the rest of the block */
  for (i = 0; i < (nBlocks*720); i = i + 720) 
    fwrite( (void *)&dataArray[i], 2880, 1, dataFile);

  fclose( dataFile);

  if ((tempFile = fopen( tempFileName, "r")) == NULL) {
    fprintf( stderr, "Error opening the temporary FITS FILE: %s\n", 
	     tempFileName);
    return("Error openning temp file name");
  }

  if ((dataFile = fopen( tempDataName, "r")) == NULL) {
    fprintf( stderr, "Error re-opening the temporary Data FILE: %s\n", 
	     tempDataName);
    return("Error openning temp file name");
  }

  if ((fitsFile = fopen( fitsName, "w")) == NULL) {
    fprintf( stderr, "Error opening output fits file: %s\n", fitsName);
    return("Error opening fits file");
  }

  nBytes = 0;
  /* copy fits header until end of keywords */
  for (i = 0; i < 20; i++) {
    nRead = fread ( (void *)&fitsBlock[0], 2880, 1, tempFile);
    if (nRead <= 0) 
      break;
    if (fitsBlock[0] == 0)   /* if end of keywords, stop */
      break;
    nBytes += (fwrite ( (void *)&fitsBlock[0], 2880, 1, fitsFile)*2880);
  }
  fclose( tempFile);    
  remove( tempFileName);

  /* limit printout to 15 lines total */
  skipCount = (2*(nTotal / 7)) + 1;
  nBlocks = 0;
  /* now copy data to file, NOTE this has some portability issues!! */
  /* Will only work properly on PCs !!!! */
  nRead = 1;
  do {
    nRead = fread ( (void *)&fitsBlock[0], 2880, 1, dataFile);
    if (nRead <= 0)
      break;
    if (nBlocks % skipCount == 0) {
      if (debugPrint < maxDebugPrint) 
      fprintf( stderr, "Writing data word %10ld: %8.4f\n", 
	       nBlocks*720, *(float *)&fitsBlock[0]);
    }
    /* must flip the float words one word at a time */
    for (j = 0; j < 720; j++) 
      endianFlip( &fitsBlock[j*4]);
    nBytes = nBytes + (fwrite( (void *)&fitsBlock[0], 2880, 1, fitsFile)*2880);
    nBlocks++;
  } while (nRead > 0);
  fclose( fitsFile);    
  fclose( dataFile);    
  remove( tempDataName);

  return(NULL);
} /* end of writeSdfits() */

