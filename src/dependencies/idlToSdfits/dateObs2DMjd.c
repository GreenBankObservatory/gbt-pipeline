/* File dateObs2DMjd.c, version 1.10, released  12/04/09 at 12:03:41 
   retrieved by SCCS 14/04/23 at 15:51:02     

%% Generate a summary and  AIPS SDFITS data for a series of scans from the GBT
:: TEST C program
 
HISTORY:
  111110 GIL read one more digit of time in the ascii string 
  041228 GIL add complimentary function dMjd2DateObs()
  030605 GIL print utc only if less than 0
  020207 GIL strip out trailing 'Z' in some files
  011019 GIL add fileName2Dmjd() 
  010412 GIL remove unused variable
  010412 GIL print only if data out of range
  010411 GIL initial version from readTCal.c
 
DESCRIPTION:
Convert a DATE-OBS keyword string into a double precision
Modified Julian Day.
*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "math.h"
#include "MATHCNST.H"
#include "STDDEFS.H"

/* externals */
extern char * stripWhite( char *);
extern char * cvrtuc( char *);
extern long dayMonthYear2mjd( int day, int month, int year);
extern char *str2rad( char *, double *);
extern STATUS mjd2date(		/* convert MJD to date */
    long mjd,		/* input Modified Julian Date */
    int *pYear,		/* pointer to returned year (1-10000) */
    int *pMonth,	/* pointer to returned month (1-12) */
    int *pDay		/* pointer to returned day (1-31) */
    );
extern char *rad2strg(
    double angle,       /* input angle in radians */
    char *pFormat,      /* input string specifing format of output string */
    char *pOutStr,      /* returned string ('\0' terminated) */
    BOOL roundFlag      /* TRUE- output string is rounded, FALSE-truncated */
    );

char * mjdUtc2DateObs( long mjd, double utc, char * dateObs)
/* convert mjd and utc (radians) to standard fits date time string */
{ int day = 0, month = 0, year = 0;
  char timeString[31] = "";

  /* mjd */
  mjd2date( mjd, &year, &month, &day);

  /* utc with : between hours and minutes and with two digits in seconds*/
  rad2strg( utc, "h:0.2", timeString, TRUE);

  /* convert to DATE_OBS= '2000-10-23T00:00:00' */
  sprintf( dateObs, "%4d-%02d-%02dT%s", year, month, day, timeString);
  if (mjd == 0) 
    fprintf( stderr, "%ld %lf -> %d-%02d-%02d -> %s\n",
	   mjd, utc, year, month, day, dateObs);
  return(NULL);
} /* end of mjdUtc2DMjd() */

char * dMjdDateObs( double dMjd, char * dateObs)
/* convert double precision modified julian days to fits date time string */
{ long mjd = dMjd;
  double utc = 0;
  
  utc = (dMjd - mjd) * TWOPI;
  return( mjdUtc2DateObs( mjd, utc, dateObs));
} /* end of mjdUtc2DateObs() */

char * dateObs2DMjd( char * dateObs, double * dMjd)
{ int i = 0, day = 0, month = 0, year = 0;
  double utc = 0;
  long mjd = 0;
  char dateString[31] = "", timeString[31] = "";
  static long printCount = 0;

  *dMjd = 0;                            /* init output */

  if (dateObs)
    strncpy ( dateString, dateObs, 30);
  else
    return( "NULL date string");

  dateString[30] = EOS;                    /* maximum time string len */

  /* convert DATE_OBS= '2000-10-23T00:00:00' to '2000 10 23' */
  for (i = 0; i < strlen(dateString); i++)  
    if (dateString[i] == '-')
      dateString[i] = ' ';
    else if (dateString[i] == '_')
      dateString[i] = ' ';
    else if (dateString[i] == '\'')
      dateString[i] = ' ';
    else if (dateString[i] == 'T') {
      dateString[i] = EOS;
      strcpy( timeString, &dateString[i+1]);
    }

  stripWhite( dateString);

  if (strlen (dateString) < 3)
    return(NULL);

  sscanf( dateString, "%d %d %d", &year, &month, &day);
  mjd = dayMonthYear2mjd( day, month, year);

  for (i = 0; i < strlen(timeString); i++) {
    if (timeString[i] == '\'')
      timeString[i] = ' ';
    else if (isalpha(timeString[i])) {
      timeString[i] = EOS;
      break;
    }
  }

  /* find 12:34:56.78 and  convert to 12h34m56.78 */
  for (i = 0; i < strlen(timeString); i++)  
    if (timeString[i] == ':') {
      timeString[i] = 'h';
      timeString[i+3] = 'm';
      timeString[i+9] = EOS;
      break;
    }      

  for (i = 0; i < strlen(timeString); i++)  
    if (timeString[i] == '\'') 
      timeString[i] = EOS;

  stripWhite( timeString);

  str2rad( timeString, &utc);

  *dMjd = mjd + (utc/TWOPI);

  /* if out of range time and not many messages printed */
  if ((utc < 0 || utc > TWOPI) && printCount < 2) {
    fprintf( stderr, "dateObs2DMjd: %s -> %s %s => %8.2f\n", 
	     dateObs, dateString, timeString, *dMjd);
    printCount++;
  }
  return(NULL);
} /* end of dateObs2DMjd() */

char * fileName2DMjd( char * fileName, double * dMjd)
{ int i = 0, day = 0, month = 0, year = 0, j = 0, n = 0;
  double utc = 0;
  long mjd = 0;
  char dateString[50] = "", timeString[50] = "";

  if (fileName) {
    /* convert /home/gbtdata/HIOH/GO/2001_09_20_09:55:30A.fits */
    /* => 2001_09_20_09:55:30A.fits */
    for (i = 0; i < strlen( fileName); i++) {
      if (fileName[i] == '/')
	j = 0;
      else {
	dateString[j] = fileName[i];
	j++;
      }
    }
  }
  else
    return( "NULL date string");

  dateString[j] = EOS;
  n = strlen(dateString);

  /*convert 2001_09_20_09:55:30A.fits => 2001_09_20_09:55:30A => */
  for (i = 0; i < n; i++) {
    if (dateString[i] == '.') {
      dateString[i] = EOS;
      break;
    }
  }
  
  n = strlen(dateString);
  /*convert 2001_09_20_09:55:30A => 2001_09_20_09:55:30 */
  if (n > 1) {
    if (isalpha( dateString[n-1]))
      dateString[n-1] = EOS;
  }

  stripWhite( dateString);

  n = strlen(dateString);
  /* convert 2001_09_20_09:55:30A => 2001 09 20 09:55:30 */
  for (i = 0; i < n; i++)  
    if (dateString[i] == '_' || dateString[i] == '-')
      dateString[i] = ' ';

  stripWhite( dateString);

  sscanf( dateString, "%d %d %d %s", &year, &month, &day, timeString);
  mjd = dayMonthYear2mjd( day, month, year);

  stripWhite( timeString);

  /* find 12:34:56.78 and  convert to 12h34m56.78 */
  for (i = 0; i < strlen(timeString); i++)  
    if (timeString[i] == ':') {
      timeString[i] = 'h';
      timeString[i+3] = 'm';
      timeString[i+8] = EOS;
      break;
    }      

  for (i = 0; i < strlen(timeString); i++)  
    if (timeString[i] == '\'') 
      timeString[i] = EOS;

  stripWhite( timeString);

  str2rad( timeString, &utc);

  *dMjd = mjd + (utc/TWOPI);

  if (utc <= 0 || utc > TWOPI)
    fprintf( stderr, "fileName2DMjd: %s %s => %8.2f\n", 
	     dateString, timeString, *dMjd);
  return(NULL);
} /* end of fileName2DMjd() */

