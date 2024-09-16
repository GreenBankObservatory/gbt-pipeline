/* File readScanInfo.c, version 1.5, released  05/10/20 at 09:17:55 
   retrieved by SCCS 14/04/23 at 15:50:55     

%% read GBT FITS file primary header into an output structure
:: FITS utility function
 
HISTORY:
  050902 GIL reduce error messages in case of no BACKEND or DATE-OBS
  040416 GIL add function to open the file and return scanInfo structure
  020725 GIL return fitsVersion and mcVersion, add utility function
  020308 GIL use INSTRUME for BACKEND
  020215 GIL initial version from readDcr.c
 
DESCRIPTION:
read a GBT fits file primary header and return scan description
OMISSIONS:
*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "math.h"
#include "dirent.h"
#include "fitsio.h"
#include "MATHCNST.H"
#include "STDDEFS.H"
#include "gbtScanInfo.h"

/* externals */
extern char * stripPathName( char * fullFileName);

/* convert MJD to date */
STATUS mjd2date (long mjd, int * pYear, int * pMonth, int * pDay);   
char * rad2str( double, char *, char *);
char * mjd2str( long, char *);
char * stripWhite( char *);
char * cvrtuc( char *);
char * dateObsKey( long mjd, double utc, char * dateString);
char * str2rad( char *, double *);
extern char * dateObs2DMjd( char * dateObs, double * dMjd);

/* internals */
#define MAXNAMELENGTH  512
#define MAXLINE        256

char * fitsReadScan( fitsfile *pFitsFile, long * scan) 
/* fitsReadScan() reads the SCAN keyword from an open FITS file */
{ int status = 0;
  char tempString[100] = "", comment[100] = "", * errMsg = NULL;

  if (pFitsFile == NULL)
    return( "invalid fits file pointer");

  /* read the string keywords */
  if ( fits_read_key_lng( pFitsFile, "SCAN", scan, comment, &status)) {
    status = 0;
    if (fits_read_key_str( pFitsFile, "SCAN",    /* read scan as string */
			  tempString, comment, &status)) {
      status = 0;
      *scan = 0;
    }
    else {
    /* read the string long, if not a long, then status != 0 */
      tempString[FLEN_VALUE-1] = EOS;
      stripWhite( tempString);
      sscanf( tempString, "%ld", scan);
    } 
  } /* end if error on read */

  if (status)
    errMsg = "fitsReadScan: Error, Scan keyword not found";
  return(errMsg);
} /* end of fitsReadScan() */

char * fitsReadScanObject( fitsfile *pFitsFile, long * scan, char * object) 
/* fitsReadScan() reads the SCAN keyword from an open FITS file */
{ int status = 0;
  char value[100] = "", comment[100] = "", * errMsg = NULL;

  if (pFitsFile == NULL)
    return( "invalid fits file pointer");

  *scan = 999;                        /* default values */
  *object = EOS;

  /* read the string keywords */
  fits_read_key_lng( pFitsFile, "SCAN", scan, comment, &status);

  if (status)
    errMsg = "fitsReadScan: Error, Scan keyword not found";
  status = 0;

  fits_read_key_str( pFitsFile, "OBJECT", value, comment, &status);
  if (status == 0)             /* if no error reading the object value */
    strcpy( object, value);

  return(errMsg);
} /* end of fitsReadScanObject() */

char * readScanInfo( fitsfile *pFitsFile,  /* FITS file, defined in fitsio.h*/
		     long printFitsInput, 
		     struct SCANINFO * pScanInfo)
/* readScanInfo() reads the standard parameters from a GBT FITS file */
{ 
  int nkeys = 0, keypos = 0, hdutype = 0, status = 0, jj = 0;
  char value[MAXLINE] = "", card[MAXLINE] = "", comment[MAXLINE] = "",
    * errMsg = NULL;
  long mjd = 0;

  if ( pFitsFile == NULL) {
    fprintf ( stderr, "readScanInfo: Invalid FITS file pointer\n");
    return ("FITS file pointer error");
  }

  /* move th the first fits header data unit */
  if (fits_movabs_hdu(pFitsFile, 1, &hdutype, &status)) {
    fprintf ( stderr, "readScanInfo: Error moving to the first HDU\n");
    return ("FITS HDU not present");
  } /* end if end of hdus */

  /* get no. of keywords */
  fits_get_hdrpos(pFitsFile, &nkeys, &keypos, &status);
  status = 0;
  if (printFitsInput) {
    for (jj = 1; jj <= nkeys; jj++)  {
      fits_read_record(pFitsFile, jj, card, &status);
      printf("%s\n", card); /* print the keyword card */
    }
    printf("END\n");
    status = 0;
  } /* end if printing input header files */

  fits_read_key_str( pFitsFile, "DATE-OBS", value, comment, &status);
  if (status) {                         /* if error, try again */
    status = 0;
    fits_read_key_lng( pFitsFile, "UTDATE", &mjd, comment, &status);
    if (status) {                         /* if error, report it */
      status = 0;
      pScanInfo->dMjd = 0;
    }
    else
      pScanInfo->dMjd = mjd;
  }
  else
    dateObs2DMjd( value, &(pScanInfo->dMjd));
			   
  fits_read_key_str( pFitsFile, "FITSVER", value, comment, &status);
  if (status) {                         /* if error, ignore it */
    status = 0;
    strcpy( pScanInfo->fitsVersion, "");
  }
  else
    strcpy( pScanInfo->fitsVersion, value);

  fits_read_key_str( pFitsFile, "GBTMCVER", value, comment, &status);
  if (status) {                         /* if error, ignore it */
    status = 0;
    strcpy( pScanInfo->mcVersion, "");
  }
  else {
    strcpy( pScanInfo->mcVersion, value);
  } 

  fits_read_key_str( pFitsFile, "BANK", value, comment, &status);
  if (status) {                         /* if error, ignore it */
    status = 0;
    strcpy( pScanInfo->bank, "");
  }
  else {
    strcpy( pScanInfo->bank, value);
  } 

  errMsg = fitsReadScan( pFitsFile, &(pScanInfo->scanNumber));
  if (errMsg) 
    fprintf ( stderr, "readScanInfo: Error Reading Scan number; %s",
	      errMsg);

  /* read the object name */
  if ( fits_read_key_str( pFitsFile, "OBJECT", value, comment, &status)) {
    status = 0;
    strcpy( pScanInfo->object, "");
  }
  else
    strcpy( pScanInfo->object, value);

  /* as time has gone by the INSTRUME -> MANAGER -> BACKEND */
  if ( fits_read_key_str( pFitsFile, "BACKEND", 
			  value, comment, &status)) {
    status = 0;
    if ( fits_read_key_str( pFitsFile, "MANAGER", 
			  value, comment, &status)) {
      status = 0;
      if ( fits_read_key_str( pFitsFile, "INSTRUME", 
			  value, comment, &status)) {
	strcpy( pScanInfo->manager, "");
      }
      else
	strncpy( pScanInfo->manager, value, MAXKEYLEN);
    }
    else
      strncpy( pScanInfo->manager, value, MAXKEYLEN);
  }
  else
    strncpy( pScanInfo->manager, value, MAXKEYLEN);

  pScanInfo->manager[MAXKEYLEN-1] = EOS;

  pScanInfo->simulate = FALSE;                /* assume real data */

  return(errMsg);
} /* end of readScanInfo() */

char * getScanInfo( char * fileName,    /* FITS file name*/
		     long printFitsInput, 
		     struct SCANINFO * pScanInfo)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* getScanInfo() returns the scan info structure for a GBT FITS FILE         */
/* INPUT  fileName      string describing the file location (NULL terminated)*/
/* INPUT  printKeywords if TRUE the file header keywords are printed (stderr)*/
/* OUTPUT scanInfo      output data in scan INfo structure                   */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ fitsfile *fptr = NULL;    /* pointer to the FITS file, defined in fitsio.h */
  int status = 0;
  char * errMsg = NULL;

  /* now try to open the file */
  if ( fits_open_file(&fptr, fileName, READONLY, &status) ) {
    fprintf( stderr, "Failed to open fits File: %s\n", fileName);
    return( "Failed to open FILE");
  }

  /* get all spectrometer scan parameters */
  errMsg = readScanInfo( fptr, printFitsInput, pScanInfo);

  fits_close_file(fptr, &status);

  return( NULL);
} /* end of getScanInfo() */
