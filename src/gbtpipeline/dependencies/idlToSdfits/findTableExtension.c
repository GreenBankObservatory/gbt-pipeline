/* File findTableExtension.c, version 1.4, released  07/12/17 at 14:33:39 
   retrieved by SCCS 14/04/23 at 15:50:55     

%% Function to read a FITS file and return the size and shape of 1 extension

:: offline GBT utility
 
History:
  070704 GIL allow reading multiple tables
  030625 GIL change global variable name
  030606 GIL fix comparision with table name
  030605 GIL inital version based on tableToTxt.c

DESCRIPTION:
findTableExtension() searches an entire FITS file for a Table with
specified TABLE EXTENSION name.
*/

#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#include <math.h>
#include "MATHCNST.H"   /* Mathematical constants. */
#include "KEYWORD.H"    /* FITS keyword constants and structure. */

/* externals */
#ifndef TRUE
#define TRUE 1
#endif
#ifndef FALSE
#define FALSE 0
#endif
#ifndef EOS
#define EOS 0
#endif

struct keyword getFITSKey( long maxKeys, char * keyString,
		struct keyword * keys[]);
extern char *rad2str (double, char *, char *); /* convert radians to string */
extern char *mjd2str (long, char *);	       /* convert MJD to date string */
extern long today2mjd ();    	               /* return todays MJD */
extern char *cvrtuc  (char *);	               /* convert to Upper case */
extern char *stripWhite (char *);	       /* remove white space */

extern long FITSTableR( char * FITSDir, char * FITSFileName, long maxKeys, 
		long * nHeader, struct keyword * headerCards[],
	        long * nTable, struct keyword * tableCards[], 
		long * nRows, long * bytesPerRow, char * data);

extern int findCard( char * keyword, char fitsBuffer[]);
extern FILE * openFITS( char * FITSFileName, long maxKeys, long * nHeader, 
			struct keyword * headerCards[]);
extern struct keyword getFITSKey( long maxKeys, char * keyString,
				  struct keyword * keys[]);
extern long getFITSCards( FILE * FITSFile, long maxKeys, 
			  struct keyword * keys[]);

/* internals */
#define MAXARRAY 2880
#define MAXCARDS 2000

struct keyword * tableCards[MAXCARDS];      /* pointers to table header*/
struct keyword * headerCards[MAXCARDS];     /* pointers to file header */
struct keyword keyArray[2*MAXCARDS];        /* actual data array */
long nInitialized = 0;                      /* must be initialized once */

char * findTableExtension( char * fullFileName, char * extensionName, 
			   long * nRows, long * nBytesPerRow)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* tableToTxt() appends output a measured FITS to filename.  Returns the     */
/* number of bytes read from the file; negative on error; zero on end of file*/
/* INPUT FITSDir   directory containing FITS file                            */
/*  FITSFileName   file name in directory                                    */
/* OUTPUTS                                                                   */
/*  nEntries       total number of Delta-T values in all tables              */
/*  nFlag          total number of flagged Delta-T values in all tables      */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i = 0, tableCount = 0, nHeader = 0, nBytes = 0, n = 0,
    debug = FALSE, nTables = 0, nDataReads, dataReadSize = 2880; 
  char tableName[100] = "";
  static FILE * inFITSFile = NULL;
  struct keyword aKey;
  unsigned char fitsDataArray[2*MAXARRAY];

  *nRows = *nBytesPerRow = 0;

  if (nInitialized < MAXCARDS) {            /* if temp array not initialized */
    for (i = 0; i < MAXCARDS; i++) {        /* initialize all cards */
      headerCards[i] = &keyArray[i];
      tableCards[i] =  &keyArray[i+MAXCARDS];
    } /* end for all cards */
    nInitialized = MAXCARDS;                /* mark array initialized */
  } /* end if time to initialize FITS cards */

  /* openFITS takes care of closeing on next open, DO NOT CLOSE FILE! */
  if (inFITSFile == NULL)
    inFITSFile = openFITS( fullFileName, MAXCARDS, &nHeader, headerCards);
  else { /* else must skip past the last table */
    /* next parse critical table entries */
    aKey = getFITSKey( nTables, "NAXIS2", tableCards);
    if (aKey.type == FITSINTEGER)
      *nRows = aKey.dbl;

    aKey = getFITSKey( nTables, "NAXIS1", tableCards);
    if (aKey.type == FITSINTEGER)
      *nBytesPerRow = aKey.dbl;

    /* determine how many data reads are required to finish up the table */
    nDataReads = (*nRows * *nBytesPerRow) / dataReadSize;
    /* if not exactly the right size, read one more FITS block */
    if ((*nRows * *nBytesPerRow) != (nDataReads % dataReadSize)) 
      nDataReads ++;

    if (debug) { /* if diagnosing problems */
      fprintf( stderr, "Table has %ld Rows, with %ld Bytes (%ld reads)\n", 
	       *nRows, *nBytesPerRow, nDataReads);
      fprintf( stderr, "Table %s has %ld header keywords\n", 
	      tableName, nTables);
    } /* end if printing debugging info */

    /* if here, then this is not the required table, must read past data */
    for (i = 0; i < nDataReads; i ++) {
      fread( fitsDataArray, dataReadSize, 1, inFITSFile); 
      nBytes += dataReadSize;
    } /* end for all points */
  }

  if (inFITSFile == NULL)            /* if file open failed, exit */
    return("FITS File Open Failed");

  /* keep debugging prints quiet unless needed */
  if (debug) 
    fprintf( stderr, "File: %s\n", fullFileName);

  do { 

    /*read all table cards and get number of table cards found */
    nTables = getFITSCards( inFITSFile, MAXCARDS, tableCards);

    /* exit on end of file, or lost in the file */
    if (nTables < 1 && nTables > 1999)
      break;

    /* next parse critical table entries */
    aKey = getFITSKey( nTables, "NAXIS2", tableCards);
    if (aKey.type == FITSINTEGER)
      *nRows = aKey.dbl;

    aKey = getFITSKey( nTables, "NAXIS1", tableCards);
    if (aKey.type == FITSINTEGER)
      *nBytesPerRow = aKey.dbl;

    /* determine how many data reads are required to finish up the table */
    nDataReads = (*nRows * *nBytesPerRow) / dataReadSize;
    /* if not exactly the right size, read one more FITS block */
    if ((*nRows * *nBytesPerRow) != (nDataReads % dataReadSize)) 
      nDataReads ++;

    if (debug) { /* if diagnosing problems */
      fprintf( stderr, "Table has %ld Rows, with %ld Bytes (%ld reads)\n", 
	       *nRows, *nBytesPerRow, nDataReads);
      fprintf( stderr, "Table %s has %ld header keywords\n", 
	      tableName, nTables);
    } /* end if printing debugging info */

    /* next get extension name and check if this is the ONE! */
    aKey = getFITSKey( nTables, "EXTNAME", tableCards);
    if (aKey.type == FITSSTRING) {
      strncpy( tableName, aKey.str, 16);
      tableName[16] = EOS;
      stripWhite( tableName);
      if (strncmp( tableName, extensionName, strlen( extensionName)) == 0) {
        if (debug)
          fprintf( stderr, "Table %s found\n", extensionName); 
        inFITSFile = openFITS( "", MAXCARDS, &n, headerCards);
	return(NULL);
      }
    } /* end if a string */

    /* if here, then this is not the required table, must read past data */
    for (i = 0; i < nDataReads; i ++) {
      fread( fitsDataArray, dataReadSize, 1, inFITSFile); 
      nBytes += dataReadSize;
    } /* end for all points */

    tableCount++;
  } while (tableCount < 30);   /* end before reading too many tables */

  if (debug)
    fprintf( stderr, "Table %s not found\n", extensionName); 
   
  /* close with the open command */
  inFITSFile = openFITS( "", MAXCARDS, &nHeader, headerCards);

  return("Table Not Found");
} /* end of findTableExtension() */

