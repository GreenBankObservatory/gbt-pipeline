/* File findScanInfo.c, version 1.3, released  03/08/19 at 11:22:19 
   retrieved by SCCS 14/04/23 at 15:51:07     

%% Function to read a FITS file and returns the file header info 

:: offline GBT utility
 
History:
  030715 GIL if no INSTRUME, check for BACKEND
  030626 GIL initial version based on findTableExtension.c

DESCRIPTION:
findScanInfo() does the same operations as readScanInfo, but does
not use the FITS io functions, to protect agains problems due
to damaged files.
*/

#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#include <math.h>
#include "MATHCNST.H"   /* Mathematical constants. */
#include "KEYWORD.H"    /* FITS keyword constants and structure. */
#include "gbtScanInfo.h"

#ifndef EOS
#define EOS 0
#endif

struct keyword getFITSKey( long maxKeys, char * keyString,
		struct keyword * keys[]);
extern struct keyword getFITSKey( long maxKeys, char * keyString,
				  struct keyword * keys[]);
extern long getFITSCards( FILE * FITSFile, long maxKeys, 
			  struct keyword * keys[]);
extern char * dateObs2DMjd( char * dateObs, double * dMjd);

/* internals */
#define MAXCARDS 100

char * findScanInfo( char * fullFileName, long printFitsInput, 
		     struct SCANINFO * pScanInfo)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* findScanInfo() appends output a measured FITS to filename.  Returns the   */
/* structure containing GBT parameters                                       */
/* INPUT           fullFileName   full path to the data file                 */
/*  FITSFileName   file name in directory                                    */
/* OUTPUTS                                                                   */
/*  nEntries       total number of Delta-T values in all tables              */
/*  nFlag          total number of flagged Delta-T values in all tables      */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i = 0; 
  FILE * fitsFile = NULL;
  static struct keyword * headerCards[MAXCARDS]; /* pointers to file header */
  static long nInitialized = 0, nHeader = 0;     /* must be initialized once */
  struct keyword aKey;

  if (nInitialized < MAXCARDS) {            /* if temp array not initialized */
    for (i = 0; i < MAXCARDS; i++)          /* initialize all cards */
      headerCards[i] =  (struct keyword *)malloc( sizeof( struct keyword));
    nInitialized = MAXCARDS;                /* mark array initialized */
  } /* end if time to initialize FITS cards */

  /* keep debugging prints quiet unless needed */
  if (printFitsInput) 
    fprintf( stderr, "File: %s\n", fullFileName);

  if ((fitsFile = fopen( fullFileName,"r")) == NULL)    /* file exists? */
    return ("Error Opening fits File");

  nHeader = getFITSCards( fitsFile, MAXCARDS, headerCards);

  fclose( fitsFile);

  if (nHeader < 1) 
    return( "No cards in file header!");

  aKey = getFITSKey( nHeader, "DATE-OBS", headerCards);
  if (aKey.type == FITSSTRING) 
    dateObs2DMjd( aKey.str, &(pScanInfo->dMjd));
  else {
    aKey = getFITSKey( nHeader, "UTDATE", headerCards);
    if (aKey.type == FITSINTEGER) 
      pScanInfo->dMjd = aKey.dbl;
    else
      pScanInfo->dMjd = 0;
  } /* end else looking for UTDATE */
			   
  aKey = getFITSKey( nHeader, "FITSVER", headerCards);
  if (aKey.type == FITSSTRING) 
    strcpy( pScanInfo->fitsVersion, aKey.str);
  else
    strcpy( pScanInfo->fitsVersion, "");

  aKey = getFITSKey( nHeader, "GBTMCVER", headerCards);
  if (aKey.type == FITSSTRING) 
    strcpy( pScanInfo->mcVersion, aKey.str);
  else
    strcpy( pScanInfo->mcVersion, "");

  aKey = getFITSKey( nHeader, "SCAN", headerCards);
  if (aKey.type == FITSINTEGER) 
    pScanInfo->scanNumber = aKey.dbl;
  else
    pScanInfo->scanNumber = 0;

  aKey = getFITSKey( nHeader, "OBJECT", headerCards);
  if (aKey.type == FITSSTRING) 
    strcpy( pScanInfo->object, aKey.str);
  else
    strcpy( pScanInfo->object, "");

  aKey = getFITSKey( nHeader, "INSTRUME", headerCards);
  if (aKey.type == FITSSTRING) 
    strcpy( pScanInfo->manager, aKey.str);
  else if (aKey.type == FITSUNKNOWN) {
    /* if no INSTRUMENT, then look for BACKEND keyword (DCR) */
    aKey = getFITSKey( nHeader, "BACKEND", headerCards);
    if (aKey.type == FITSSTRING) 
      strcpy( pScanInfo->manager, aKey.str);
    else
      strcpy( pScanInfo->manager, "");
  }

  aKey = getFITSKey( nHeader, "SIMULATE", headerCards);
  if (aKey.type == FITSINTEGER) 
    pScanInfo->simulate = aKey.dbl;
  else 
    pScanInfo->simulate = 0;                /* assume real data */

  return(NULL);
} /* end of findScanInfo() */

char * getScanNumber( char * fullFileName, long * scanNumber, char * object,
		      char * manager)
/* getScanNumber() returns selected parameters from an observation         */
/* since the last file is repeatedly checked, the values are cashed        */
{ char * errMsg = NULL;
  static char lastFileName[LENKEYSTR] = "";
  static struct SCANINFO scanInfo;

  /* if a new file name */
  if (strcmp( lastFileName, fullFileName)) { 
    errMsg = findScanInfo( fullFileName, 0, &scanInfo);
    strcpy( lastFileName, fullFileName);
  } /* end if a new file */
  
  *scanNumber = scanInfo.scanNumber;
  strcpy( object,  scanInfo.object);
  strcpy( manager, scanInfo.manager);

  return(errMsg);
} /* end of getScanNumber */
