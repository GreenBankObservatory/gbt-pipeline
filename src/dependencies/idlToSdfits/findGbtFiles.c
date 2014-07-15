/* File findGbtFiles.c, version 1.14, released  05/06/13 at 09:14:47 
   retrieved by SCCS 14/04/23 at 15:50:57     

%% Generate a summary and  AIPS SDFITS data for a series of scans from the GBT
:: TEST C program
 
HISTORY:
  050613 GIL fix stripFitsExtension
  050131 GIL add getBankLetter()
  050128 GIL fix problems with finding B bank
  041013 GIL use findRcvr() for un-matched files
  040829 GIL add makeGbtFiles()
  040805 GIL match spectrometer bank
  030605 GIL do not parse time in scan log if error reading
  020401 GIL case of more than 1 spectrometer file
  020209 GIL match all backends to input file name
  020207 GIL return holography file
  020118 GIL make functions more generic
  020116 GIL fix support for old format
  011218 GIL support new FITS format
  011110 GIL add LO1A support
  011008 GIL modularize
  011005 GIL initial version based on gbtObsSummary.c
 
DESCRIPTION:
Reads a scan log and finds files matching an observation.  Two time stamp
formats are supported, 1) Old Date String, 2) Double dMJD value.
OMISSIONS:
Does not use time to allow stopping search quicker.
The old scan log format has three fields, 
1) double DMJD, 2) long SCAN and 3) FILEPATH

The full backend file names are expected to be provided to these routines
an example backend file is:
/home/gbtdata/AGBT04B_003_01

From this we go two '/'s backwards to get the base path:
/home/gbtdata/AGBT04B_003_01/

From this we generate the ScanLog File
/home/gbtdata/AGBT04B_003_01/ScanLog.fits:

The Other backends, GO info, eetc are below the base path
/home/gbtdata/AGBT04B_003_01/GO ...

*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "math.h"
#include "dirent.h"
#include "fitsio.h"
#include "MATHCNST.H"
#include "STDDEFS.H"

/* externals */

extern char * stripWhite( char *);
extern char * cvrtuc( char *);
/* convert MJD to date */
extern char * dateObs2DMjd( char * dateObs, double * dMjd);
extern int ffpbyt(fitsfile *fptr,   
		  /* I - FITS file pointer                    */
           long nbytes,      /* I - number of bytes to write             */
           void *buffer,     /* I - buffer containing the bytes to write */
           int *status);     /* IO - error status                        */

/* internals */
#define MAXNAMELENGTH  512

static fitsfile *pLogFile = NULL;        /* FITS file, defined in fitsio.h*/
static char lastScanLogFile[MAXNAMELENGTH] = "";
static int nkeys = 0, keypos = 0, hdutype = 0;
static long frow = 1, felem = 1, nelem = 1;
static long debug = FALSE;

char * initScanLog()
/* initScanLog initializes the scan log file properties */
{ int status = 0;

  if ( pLogFile)
    fits_close_file(pLogFile, &status);
  pLogFile = NULL;
  lastScanLogFile[0] = EOS;
  return(NULL);
} /* end of initScanLog() */

char * readScanLog( char * scanLogName, long printFitsInput, long * iSubFile,
		    long * mjd, double * utc, long * scan, 
		    char * subFileName)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* readScanLog() reads the list of files in a GBT observation and returns    */
/* the next file in the series.  Returns NULL on OK, else error/end of file  */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ FILE * pFile = NULL;
  int status = 0, anynull = 0, ii = 0, jj = 0;
  double mjds[2] = {0, 0}, dubblenull = 0.;
  long scans[2] = {0, 0}, longnull = 0, i = 0;
  char strnull[10] = " ", card[100] = "", * fileNames[2] = { NULL, NULL},
    timeType[100] = "", timeString[1000] = "", comment[100] = "", 
    * errMsg = NULL;
  static long doubleTime = TRUE;

  if (strcmp( lastScanLogFile, scanLogName) != 0) {  /* if a new file name */
    initScanLog();
    if (( pFile = fopen ( scanLogName, "r")) == NULL)
      return("ScanLog Not present");
    else
      fclose( pFile);
    if ( fits_open_file(&pLogFile, scanLogName, READONLY, &status) ) {
      /* fits_close_file(pLogFile, &status); */
      fprintf (stderr, "Error opening Scan Log: %s\n", scanLogName);
      return("Error Opening Scan Log");
    }
    strcpy( lastScanLogFile, scanLogName);

    for (ii = 1; ii <= 2; ii++) {

      fits_movabs_hdu(pLogFile, ii, &hdutype, &status);

      /* get no. of keywords */
      if (fits_get_hdrpos(pLogFile, &nkeys, &keypos, &status) )
	break;

      for (jj = 1; jj <= nkeys; jj++)  {

	if ( fits_read_record(pLogFile, jj, card, &status) )
	  break;

	if (printFitsInput) 
	  printf("%s\n", card); /* print the keyword card */
      }
    } /* end for all HDUS */
    frow = 1;

    fits_read_keyword( pLogFile, "TTYPE1", timeType, comment, &status);
    if (status) {
      fprintf ( stderr, "Error reading scan Log Time type\n");
      errMsg = "Error reading Scan Log Time Type\n";
      fits_close_file( pLogFile, &status);
      return( errMsg);            /* got the expected EOF error; reset = 0  */
    }
    cvrtuc (timeType);
    for (i = 0; i < strlen(timeType); i++) {
      if (timeType[i] == '"' || timeType[i] == '\'')
	timeType[i] = ' ';
    }
    stripWhite( timeType);
    if (strcmp( timeType, "DMJD") == 0)
      doubleTime = TRUE;
    else
      doubleTime = FALSE;
    if (doubleTime) 
      fprintf( stderr, "readScanLog: Old format ScanLog Time\n");
  } /* end if time to open the file */

  *iSubFile = frow;

  if (doubleTime) {      
    /* now read to read the file */
    fits_read_col(pLogFile, TDOUBLE, 1, frow, felem, nelem, &dubblenull, mjds,
		  &anynull, &status);
    if (status == END_OF_FILE) { /* status values are defined in fitsioc.h */
      fits_close_file(pLogFile, &status);
      pLogFile = NULL;
      strcpy( lastScanLogFile, "");
      return("End of File");    /* got the expected EOF error; reset = 0  */
    }
  }
  else { 
    strcpy( timeString, "                                          ");
    fileNames[0] = timeString;   /* fits_read_col takes and array of pointers*/
    /* else looking for time in string form: 2001-12-10T19:52:35  */   
    fits_read_col(pLogFile, TSTRING, 1, frow, felem, nelem, &dubblenull, 
		  fileNames, &anynull, &status);
    if (status) {
      status = 0;
      mjds[0] = 0;
      errMsg = "Error Reading the ScanLog Time";
    }
    else {
      /* protect against "SCAN FINISHED" string */
      if (strncmp( timeString, "SCAN ", 5) != 0)
	dateObs2DMjd( timeString, mjds); 
      else
	mjds[0] = 0;
    }
  } /* end else string, not double precision time */

  /* break up double precision date into date and time */
  *mjd = mjds[0];
  *utc = mjds[0] - *mjd;
  *utc = TWOPI * *utc;  

  /* next read scan number */
  fits_read_col(pLogFile, TLONG, 2, frow, felem, nelem, &longnull, scans,
		&anynull, &status);
  *scan = scans[0];

  /* read file name or comment string */
  fileNames[0] = subFileName;
  fits_read_col(pLogFile, TSTRING, 3, frow, felem, nelem, strnull, 
		fileNames, &anynull, &status);
  subFileName[192] = EOS;
  stripWhite (subFileName);
  frow++;                       /* increment index for next call */
  return(errMsg);
} /* end of readScanLog() */

char * stripFitsExtension( char * fullFileName)
/* stripFitsExtension() removes the '.fits' from the file name end */
{ long n = strlen(fullFileName);

  if (n < 4) 
    return("String Too Short");

  stripWhite( fullFileName);

  if ((fullFileName[n-5] == '.') && 
      (fullFileName[n-4] == 'f'  || fullFileName[n-4] == 'F') &&
      (fullFileName[n-3] == 'i'  || fullFileName[n-3] == 'I') &&
      (fullFileName[n-2] == 't'  || fullFileName[n-2] == 'T') &&
      (fullFileName[n-1] == 's'  || fullFileName[n-1] == 'S'))
    fullFileName[n-5] = EOS;
  return(NULL);
} /* end of stripFitsExtension() */

char * getBankLetter( char * obsFileName, char * bank) 
/* getBankLetter() finds the bank character for an observing file name */
/* The obsFileName is the full file name of the backend data file */
/* The bank characters is assumed to be the character preceeding '.fits' in the file name */
{ char tempName[MAXNAMELENGTH] = ".", * fitsPointer = NULL;

  *bank = ' ';                         /* default is no bank */

  if (obsFileName == NULL) 
    return("Null input file name");

  strncpy( tempName, obsFileName, MAXNAMELENGTH-1);
  tempName[MAXNAMELENGTH-1] = EOS;
  stripWhite( tempName);

  fitsPointer = strstr( tempName, ".fits");
  if (fitsPointer == NULL)
    return(NULL);

  fitsPointer --;                     /* look at character before .fits */

  if (*fitsPointer == 'a' || *fitsPointer == 'A')
    *bank = 'A';
  else if (*fitsPointer == 'b' || *fitsPointer == 'B')
    *bank = 'B';
  else if (*fitsPointer == 'c' || *fitsPointer == 'C')
    *bank = 'C';
  else if (*fitsPointer == 'd' || *fitsPointer == 'D')
    *bank = 'D';

  return(NULL);
} /* end of getBankLetter */

char * stripExtension( char * fullFileName)
/* stripExtension() removes the '.xxx' from the file name end */
{ long i = 0, n = strlen(fullFileName);

  for (i = n-1; i >= 0; i--) {
    if (fullFileName[i] == '.') {
      fullFileName[i] = EOS;
      break;
    }
  }
  return(NULL);
} /* end of stripExtension() */


char * stripPathName( char * fileName)
/* stripPathName() removes the path from the file name */
{ long j = 0, i = 0; 

  /* ../Antenna/2001_03_26_12:34:45A.fits => 2001_03_26:12:34:45A.fits */
  for (i = 0; i < strlen( fileName); i++) {
    if ( fileName[i] == '/')
      j = 0;
    else {
      fileName[j] = fileName[i];
      j++;
    }
  }
  fileName[j] = EOS;
  stripWhite( fileName);
  return(NULL);
} /* end of stripPathName() */

char * stripBankName( char * fullFileName)
/* stripBankName() removes the A,B,C or D character the file name */
{ /* ../SP/2001_03_26_12:34:45A.fits => ../SP/2001_03_26:12:34:45A */
  stripExtension( fullFileName);

  /* ../SP/2001_03_26_12:34:45A ../SP/2001_03_26:12:34:45 */
  if ((fullFileName[strlen(fullFileName)-1] == 'A') ||
      (fullFileName[strlen(fullFileName)-1] == 'B') ||
      (fullFileName[strlen(fullFileName)-1] == 'C') ||
      (fullFileName[strlen(fullFileName)-1] == 'D') ||
      (fullFileName[strlen(fullFileName)-1] == 'a') ||
      (fullFileName[strlen(fullFileName)-1] == 'b') ||
      (fullFileName[strlen(fullFileName)-1] == 'c') ||
      (fullFileName[strlen(fullFileName)-1] == 'd'))
    fullFileName[strlen(fullFileName)-1] = EOS;

  return(NULL);
} /* end of stripBankName() */

char * makeGbtName( char * fullFileName, char * manager, char * managerName)
/* makeManagerName() creates a file name from a backend file name */
{ long i = 0, lastSlash = 0, slashCount = 0; 
  char fitsFileName[200] = "";

  /* /home/gbtdata/Test/SP/foo.fits => foo.fits */
  for (i = strlen( fullFileName) - 1; i >= 0; i--)
    if ( fullFileName[i] == '/') {
      lastSlash = i+1;                  /* save for stripping the backend */
      break;
    }

  strcpy( fitsFileName, &fullFileName[lastSlash]);
  /* 2001_03_26_12:34:45A.fits => 2001_03_26_12:34:45A */
  stripFitsExtension( fitsFileName);
  /* 2001_03_26_12:34:45A => 2001_03_26_12:34:45 */
  stripBankName( fitsFileName);

  strcpy( managerName, fullFileName);

  /* /home/gbt/Test/SP/2001_03_26_12:34:45.fits => /home/gbt/Test */
  for (i = strlen( managerName)-1; i >= 0; i--) { /* copy up to slash */
    if ( fullFileName[i] == '/') {
      slashCount ++;
      if (slashCount == 2) {
        managerName[i+1] = EOS;
	break;
      }
    }
  }

  /* managerName has full path, add backend, IF etc */
  strcat( managerName, manager);    /* now generate GO, IF, etc  file name */
  strcat( managerName, "/");
  strcat( managerName, fitsFileName);  /* now add the fits file */
  strcat( managerName, ".fits");
  return(NULL);
} /* end of makeGbtName() */

char * makeGoName( char * fullFileName, char * goName)
/* makeGoName() creates GO file name from a backend file name */
{ char * errMsg = NULL;

  errMsg = makeGbtName( fullFileName, "GO", goName);
  return(errMsg);
} /* end of makeGoName() */

char * getPathName( char * fullFileName, char * pathName)
/* getPathName() extracts the path from the file name and removes .fits  */
{ long lastSlash = 0, i = 0; 

  strcpy ( pathName, fullFileName);

  stripWhite( pathName);
  /* ../Antenna/2001_03_26_12:34:45.fits => ../Antenna/ */
  for (i = strlen( pathName) - 1; i >= 0; i--)
    if ( pathName[i] == '/') {
      lastSlash = i;
      break;
    }

  pathName[lastSlash+1] = EOS;

  if (lastSlash <= 0)
    return("Error extracting path name");

  return(NULL);
} /* end of getPathName() */

char * setFullPath( char * pathName, char * fileName)
/* setFullPath() adds the path to file name assuming that the file name is*/
/* from ScanLog.fits files. ie                                               */
/* pathName = /home/gbtdata/TPF1                                             */
/* fileName = ./TPF1/Antenna/2004_08_05_12:37:05.fits */
/* The output file starts with the path name and adds                        */
/*  /Antenna/2004_08_05_12:37:05.fits, removing the /TPF1  one copy          */
{ char tempName[MAXNAMELENGTH] = "";
  long i = 0, slashCount = 0, firstSlash = 0;

  if (debug)
    fprintf( stderr, " %s %s\n", pathName, fileName); 

  strcpy( tempName, fileName);
  /* start with path name, then add file name */
  strcpy( fileName, pathName);

  /* ./TPF1/Antenna/2004_08_05_12:37:05.fits => 
      /Antenna/2004_08_05_12:37:05.fits  */
  for (i = 0; i < strlen( tempName); i++)
    if (tempName[i] == '/') {
      slashCount++;
      if (slashCount == 2) {
	firstSlash = i;
	break;
      } 
    }

  if (slashCount != 2)
    return("Error creating full path Name");

  /* if no trailing / add it */
  if (  fileName[strlen(fileName)-1] != '/') 
    strcat( fileName, "/");

  strcat( fileName, &tempName[firstSlash+1]);

  if (debug)
    fprintf( stderr, "-> %s\n", fileName); 

  return(NULL);
} /* end of setFullPath() */

char * getBasePathName( char * obsFileName, char * basePathName)
/* basePathNameName() takes a fully specified fits file name and */
/* extracts name up to the last / */
{ char * errMsg = NULL;

/* /home/gbtdata/TPF1/Antenna/2004_08_05_12:37:05.fits ==> */  
/* /home/gbtdata/TPF1/Antenna/ */  
  errMsg = getPathName( obsFileName, basePathName);

  if (errMsg) {
    fprintf( stderr, "Error extracting base path name from %s\n", obsFileName);
    return("Error creating ScanLog name");
  }

  /* if a trailing / remove it */
  /* /home/gbtdata/TPF1/Antenna/ ==> /home/gbtdata/TPF1/Antenna */  
  if (  basePathName[strlen(basePathName)-1] == '/') 
    basePathName[strlen(basePathName)-1] = EOS;

  /* /home/gbtdata/TPF1_04AUG05/Antenna ==> */  
  /* /home/gbtdata/TPF1_04AUG05/ */  
  errMsg = getPathName( basePathName, basePathName);

  /* if no trailing / add it */
  if (  basePathName[strlen(basePathName)-1] != '/') 
    strcat( basePathName, "/");

  return(errMsg);
} /* end of getBasePathName() */

char * createScanLogName( char * obsFileName, char * scanLogName)
/* createScanLogName() removes the path from the file name and removes .fits */
{ char * errMsg = NULL;

  errMsg = getBasePathName( obsFileName, scanLogName);

  if (errMsg) {
    fprintf( stderr, "Error creating scanlog name from %s\n", obsFileName);
    return("Error creating ScanLog name");
  }

  strcat( scanLogName, "ScanLog.fits");

  return(errMsg);
} /* end of createScanLogName() */

char * findRcvrName(  char * obsFileName, char * rcvrName) 
/* find receiver name for an obs file, else return last reciever name */
{ char scanLogName[MAXNAMELENGTH] = "", * errMsg = NULL,
    subFileName[MAXNAMELENGTH] = "", backendName[MAXNAMELENGTH] = "",
    pathName[MAXNAMELENGTH] = "";
  long printFitsInput = FALSE, iSubFile = 0, mjd = 0, scan = 0, 
    backendMatch = FALSE;
  double utc = 0;

  errMsg = createScanLogName( obsFileName, scanLogName);
  errMsg = getBasePathName( obsFileName, pathName);
  strcpy( backendName, obsFileName);
  errMsg = stripPathName( backendName);
  stripExtension( backendName);
  stripBankName( backendName);

 /* One Scan Log entry below: */
 /*2004-08-05T12:37:05    4 ./TPF1_04AUG05/Antenna/2004_08_05_12:37:05.fits*/
  while (errMsg == NULL) {
    errMsg = readScanLog( scanLogName, printFitsInput, &iSubFile, 
			    &mjd, &utc, &scan, subFileName);
    if (errMsg) {
      fprintf( stderr, "findGbtFiles: Error reading scan log: %s\n", errMsg);
      break;
    }
    if (mjd == 0)                           /* if end of Scan Log File */
      break;

    /* if special lines */
    if (strncmp( subFileName, "SCAN STARTI", 80) == 0) {
    }
    else if (strncmp( subFileName, "SCAN FINISH", 8) == 0) {
       if (backendMatch)
	  break;
    }
    /* if this file is the glish file */
    else if (strstr( subFileName, "/Rcvr"))
      strcpy( rcvrName, subFileName);
    else if (strstr( backendName, subFileName))
      backendMatch = TRUE;
  } /* end for all input files */

  errMsg = initScanLog();
  if (*rcvrName != EOS) 
    setFullPath( pathName, rcvrName);
  return(NULL);
} /* en dof findRcvrName() */

char * makeGbtFiles ( char * obsFileName, char * goName, char * antennaName, 
		      char * rcvrName, char * loName, char * ifName, 
		      char * spectrometerName, char * spName,
		      char * dcrName, char * bcpmName, char * holographyName)
/* makeGbtFiles() generates all the file names for a obs File Name */
{ char * errMsg = NULL, bank = ' ';
  FILE * pFile = NULL;

  /* make Go file names etc  */
  makeGbtName( obsFileName, "GO", goName);
  makeGbtName( obsFileName, "Antenna", antennaName);
  makeGbtName( obsFileName, "LO1A", loName);
  makeGbtName( obsFileName, "IF", ifName);
  makeGbtName( obsFileName, "SpectralProcessor", spName);
  makeGbtName( obsFileName, "DCR", dcrName);
  makeGbtName( obsFileName, "BCPM", bcpmName);
  makeGbtName( obsFileName, "Holography", holographyName);

  getBankLetter( obsFileName, &bank);

  findRcvrName( obsFileName, rcvrName);
  /*  fprintf( stderr, "ObsFile: %s -> Rcvr: %s\n", obsFileName,
      rcvrName); */

  /* now check that the files actually exist */
  if (( pFile = fopen ( goName, "r")) == NULL)
    strcpy( goName, "");
  else
    fclose( pFile);
  if (( pFile = fopen ( antennaName, "r")) == NULL)
    strcpy( antennaName, "");
  else
    fclose( pFile);
  if (( pFile = fopen ( ifName, "r")) == NULL)
    strcpy( ifName, "");
  else
    fclose( pFile);
  if (( pFile = fopen ( rcvrName, "r")) == NULL)
    strcpy( rcvrName, "");
  else
    fclose( pFile);

  /* special case of spectrometer file, because of banks A,B,C or D */
  if (strstr( obsFileName, "Spectrometer") != NULL) { 
    strcpy( spectrometerName, obsFileName);
  }

  if (( pFile = fopen ( spectrometerName, "r")) == NULL)
    strcpy( spectrometerName, "");
  else
    fclose( pFile);

  if (( pFile = fopen ( spName, "r")) == NULL)
    strcpy( spName, "");
  else
    fclose( pFile);
  if (( pFile = fopen ( dcrName, "r")) == NULL)
    strcpy( dcrName, "");
  else
    fclose( pFile);
  if (( pFile = fopen ( bcpmName, "r")) == NULL)
    strcpy( bcpmName, "");
  else
    fclose( pFile);
  if (( pFile = fopen ( holographyName, "r")) == NULL)
    strcpy( bcpmName, "");
  else
    fclose( pFile);

  return( errMsg);
} /* end of makeGbtFiles() */

char * findGbtFiles ( char * obsFileName, char * goName, char * antennaName, 
		      char * rcvrName, char * loName, char * ifName, 
		      char * spectrometerName, char * spName,
		      char * dcrName, char * bcpmName, char * holographyName)
/* findGbtFiles() returns the known file names for a single backend file */
{ char scanLogName[MAXNAMELENGTH] = "", * errMsg = NULL,
    subFileName[MAXNAMELENGTH] = "", backendName[MAXNAMELENGTH] = "",
    pathName[MAXNAMELENGTH] = "", bank = ' ';
  long printFitsInput = FALSE, iSubFile = 0, mjd = 0, scan = 0;
  double utc = 0;

  errMsg = createScanLogName( obsFileName, scanLogName);
  errMsg = getBasePathName( obsFileName, pathName);
  getBankLetter( obsFileName, &bank);
  strcpy( backendName, obsFileName);
  errMsg = stripPathName( backendName);
  stripExtension( backendName);
  stripBankName( backendName);
  *goName = *antennaName = *loName = EOS;
  *rcvrName = *ifName = EOS;
  *spName = *dcrName = *spectrometerName = EOS;
  *bcpmName = *holographyName = EOS;

  if (debug)
    fprintf( stderr, "findGbtFiles: %s -> %s, %c\n", obsFileName, 
	     backendName, bank);

 /* One Scan Log entry below: */
 /*2004-08-05T12:37:05    4 ./TPF1_04AUG05/Antenna/2004_08_05_12:37:05.fits*/
  while (errMsg == NULL) {
    errMsg = readScanLog( scanLogName, printFitsInput, &iSubFile, 
			    &mjd, &utc, &scan, subFileName);
    if (errMsg) {
      fprintf( stderr, "findGbtFiles: Error reading scan log: %s\n", errMsg);
      break;
    }
    if (mjd == 0)                           /* if end of Scan Log File */
      break;

    /* if special lines */
    if (strncmp( subFileName, "SCAN STARTI", 80) == 0) {
    }
    else if (strncmp( subFileName, "SCAN FINISH", 8) == 0) {
      if (strlen(spName) > 0)                    /* if a backend found */
	if (strstr( spName, backendName) != 0)
	  break;

      if (strlen(spectrometerName) > 0) {        /* if a backend found */
	if (strstr( spectrometerName, backendName) != 0) {
          if (debug)
	    fprintf( stderr, "matched %s == %s\n", spectrometerName,backendName);
	  break;
	}
      }

      if (strlen(holographyName) > 0)            /* if a backend found */
	if (strstr( holographyName, backendName) != 0)
	  break;
      if (strlen(dcrName) > 0)                   /* if a backend found */
	if (strstr( dcrName, backendName) != 0)
	  break;
      if (strlen(bcpmName) > 0)                  /* if a backend found */
	if (strstr( bcpmName, backendName) != 0)
	  break;
      /* else not a match, init and prepare to look again */
      *goName = EOS;
      *antennaName = *loName = EOS;
      *rcvrName = *ifName = EOS;
      *spName = *dcrName = *spectrometerName = EOS;
      *bcpmName = *holographyName = EOS;
    }
    /* if this file is the glish file */
    else if (strstr( subFileName, "/Glish/") ||
	     strstr( subFileName, "/GO/")) {
      strcpy( goName, subFileName);
    } /* end if a new glish file */
    else if (strstr( subFileName, "/Antenna/")) 
      strcpy( antennaName, subFileName);
    else if (strstr( subFileName, "/Rcvr"))
      strcpy( rcvrName, subFileName);
    else if (strstr( subFileName, "/IF/"))
      strcpy( ifName, subFileName);
    else if (strstr( subFileName, "/LO1A/"))
      strcpy( loName, subFileName);
    else if (strstr( subFileName, "/LO1-LO1A-phaseState/")) {
      if (strlen (loName) < 1)
	strcpy( loName, subFileName);
    }
    else if (strstr( subFileName, "/DCR/"))
      strcpy( dcrName, subFileName);
    else if (strstr( subFileName, "/Spectrometer/")) {
      strcpy( spectrometerName, subFileName);  /* found an file */
    }
    else if (strstr( subFileName, "/SpectralProcessor/"))
      strcpy( spName, subFileName);
    else if (strstr( subFileName, "/BCPM/"))
      strcpy( bcpmName, subFileName);
    else if (strstr( subFileName, "/Holography/"))
      strcpy( holographyName, subFileName);
  } /* end for all input files */

  errMsg = initScanLog();

  if (*bcpmName == EOS && *dcrName == EOS &&
      *spName   == EOS && *spectrometerName == EOS &&
      *holographyName == EOS) {
    fprintf( stderr, "File Not in Log: %s\n", obsFileName);
    return("File Not Found");
  }

  if (debug) 
    fprintf( stderr, "matched acs=%s\n", spectrometerName);
  
  if (*loName != EOS) 
    setFullPath( pathName, loName);

  /* if go Name not found, create it from the back end name */
  if (*goName == EOS) {
    if (*bcpmName != EOS)
      makeGoName( bcpmName, goName);
    else if (*dcrName != EOS)
      makeGoName( dcrName, goName);
    else if (*spName != EOS)
      makeGoName( spName, goName);
    else if (*spectrometerName != EOS)
      makeGoName( spectrometerName, goName);
    else if (*holographyName != EOS)
      makeGoName( holographyName, goName);
    if (*goName != EOS) 
      setFullPath( pathName, goName);
  }
  setFullPath( pathName, goName);

  /* now convert from relative paths to full path names */
  if (*ifName != EOS) 
    setFullPath( pathName, ifName);
  if (*rcvrName != EOS) 
    setFullPath( pathName, rcvrName);
  if (*antennaName != EOS) 
    setFullPath( pathName, antennaName);
  if (*spName != EOS) 
    setFullPath( pathName, spName);
  if (*spectrometerName != EOS) 
    setFullPath( pathName, spectrometerName);
  if (*dcrName != EOS) 
    setFullPath( pathName, dcrName);
  if (*bcpmName != EOS) 
    setFullPath( pathName, bcpmName);
  if (*holographyName != EOS) 
    setFullPath( pathName, holographyName);
  
  return(NULL);
} /* end of findGbtFiles */

