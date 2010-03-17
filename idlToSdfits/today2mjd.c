/* File today2mjd.c, version 1.8, released  02/11/22 at 15:34:05 
   retrieved by SCCS 07/07/09 at 16:40:45     

%% utility time convertion

:: GBES Offline/realtime survey
 
HISTORY:
  070709  GIL get fraction of a second
  021122  GIL add a few prototypes
  990919  AHM change mapStr format in mjd2AIPS to be Y@K compliant
  970722  AHM fix bug in now2Utc (in popen command a ' was missing)
  970514  GIL today2mjd() returns UTC date
  970220  GIL add all functions from today2MJD() make today2MJD obsolete
  951207  GIL add now2utc() function that return utc (radians)
  950419  GIL function that returnes mjd of today
  950102  GIL allow sky subtraction
DESCRIPTION:
mjd2AIPS creates two date strings in the format required by AIPS when reading
a FITS file.  This function compiles in the unix and VXWORKS environment.
today2mjd() returns a long for the mjd of today.
*/

#include <stdio.h>
#include <fcntl.h>
#include <string.h>
#include "math.h"
#include "MATHCNST.H"

#ifdef GBES
#include "TIMES.H"
extern struct times times;
#endif

/* externals */
char * stripWhite( char *);
char * str2rad( char *, double *);
char * str2mjd( char *, long *);
int mjd2date ( long mjd, int * pYear, int * pMonth, int * pDay);
char * rad2str (double angle, char * pformat, char * pstring);

/* internals */
long dayMonthYear2mjd( int day, int month, int year) 
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* dayMonthYear2mjd() re-formats the day month and year into a string        */
/* suitable for the VLBA routine str2mjd()                                   */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ char todayStr[30];
  char * months[] = { "JAN", "FEB", "MAR", "APR", "MAY", "JUN", 
		      "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"};
  long mjd;

  if (month < 1 || month > 12)                   /* check input */
    return(-1);
  year %= 100;                                   /* year ranges between 0-99 */
  sprintf(todayStr,"%02d%s%02d",year,months[month-1],day); /* convert to str */
  str2mjd( todayStr, &mjd);                      /* finaly use standard func */
  return (mjd);
} /* end of dayMonthYear2mjd() */

long today2mjd() 
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* today2mjd() returns the MJD for today this function works in both unix    */
/* and vxworks environments                                                  */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long mjd;

#ifdef GBES
  mjd = times.mjd;                     /* in vxworks, just copy from struct */
#else
  FILE * datePipe;                     /* in Unix, must use system "date" */
  char todayStr[30];
  int day, month, year;

  datePipe = popen("date -u '+%d %m %y'","r");   /* get date from cpu */
  fgets(todayStr, 10, datePipe);                 
  pclose( datePipe);
  todayStr[8] = '\0';                            /* terminate string */
  sscanf(todayStr,"%d %d %d", &day, &month, &year);   /* get int */
  mjd = dayMonthYear2mjd( day, month, year);
#endif

  return(mjd);
} /* end of today2mjd() */

double now2Utc() 
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* now2Utc() returns the UTC (radians) at the time of execution.             */
/* This function works in both unix and vxworks environments.                */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ double utc;

#ifdef GBES
  utc = times.utc;
#else
  {
  FILE * datePipe;
  char nowStr[100] = "";
  double nsecs = 0;

  datePipe = popen("date -u '+%Hh%Mm%Ss %N'","r"); /* get GMT time from cpu */
  fgets(nowStr, 22, datePipe);                 /* read in string */
  pclose( datePipe);
  nowStr[9] = '\0';                            /* terminate string */
  nowStr[21] = '\0';                           /* terminate string */
  str2rad( nowStr, &utc);                      /* finaly use standard func */
  sscanf( &nowStr[10], "%lf", &nsecs);
  utc = utc + ((nsecs*1.e-9)/SEC_RAD);
  /*  fprintf( stderr, "Now Str: %s %s; +%lf -> %lf\n", nowStr, 
      &nowStr[10], nsecs, utc);  */
  }
#endif

  return(utc);
} /* end of now2Utc() */

int mjd2AIPS( int inMJD, char * dateStr, char * mapStr)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* mjd2AIPS() creates to date strings in the format expected by AIPS.        */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ int year, month, day, year2;
  long todayMJD;

  mjd2date( inMJD, &year, &month, &day);
  year2  = year % 100;
  sprintf(dateStr,"%02d/%02d/%02d", day, month, year2);

  todayMJD = today2mjd();
  mjd2date( todayMJD, &year, &month, &day);
  /* year  = year % 100; */
  sprintf( mapStr,"%04d-%02d-%02d", year, month, day);

  return(0);
} /* end of mjd2AIPS() */

long AIPS2mjd( char * dateStr)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* AIPS2mjd() takes an AIPS data string and returns the MJD for that string  */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ int i = 0, year = 0, month = 0, day = 0;
  long todayMJD = 0, oldFormat=1;
  char dateTemp[30];

  for (i = 0; i < 29 && dateStr[i] != '\0'; i ++)/* copy to scratch string */
    dateTemp[i] = dateStr[i];

  dateTemp[i] = '\0';                            /* terminate string */
  stripWhite( dateTemp);                         /* remove leading/trailing */

  if (dateTemp[0] == '\'' || dateTemp[0] == '"') /* remove leading ' */
    for (i = 1; i < 30 && dateTemp[i] != '\0'; i ++)
      dateTemp[i-1] = dateTemp[i];

  if (strlen( dateTemp) < 8)                     /* has at least 8 chars *?*/
    return(-1);                                  /* not expected string */

  for (i = 0; dateTemp[i] != '\0'; i ++) {       /* replace / and - with blank */
    if (dateTemp[i] == '/')                      /* old format */
      dateTemp[i] = ' ';
    if (dateTemp[i] == '-') {                    /* new format */
      dateTemp[i] = ' ';
      oldFormat=0;
    } /* end if new format */
  } /* end for i */

  if (oldFormat==1) 
    sscanf(dateTemp,"%d %d %d", &day, &month, &year);
  else
    sscanf(dateTemp,"%d %d %d", &year, &month, &day);

  todayMJD = dayMonthYear2mjd( day, month, year);
  return( todayMJD);
} /* end of AIPS2mjd() */
