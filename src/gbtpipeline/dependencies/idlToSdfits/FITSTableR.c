/* File FITSTableR.c, version 1.12, released  09/06/22 at 18:04:32 
   retrieved by SCCS 14/04/23 at 15:50:54     

%% Utility functions for fits read.

:: Offline point peakUp
 
History:
  090622 GIL - fix reading of large fits files (fopen64)
  090620 GIL - add putFITSKey()
  090521 GIL - allow reading only one row of a table at a time, use long longs
  090503 GIL - support the BYTE type for PSRFITS
  080903 GIL - add FITSHeaderR.c
  070704 GIL - read last block one byte at a time
  061013 GIL - add close and read next  table functions
  031216 GIL - accept comments staring in column 8
  030625 GIL - reopen if no header cards remembered
  030504 GIL - return comments
  950912 GIL - do not return obsMJD
  950502 GIL - initial version

DESCRIPTION:
Functions take input FITS file name and fills arrays of FITS header and 
table cards plus a data array the from the fits table.  The tables may 
be read one after another from the input file.  Note that if the input
file name is the same as the previous file name, then the next table in
the file is returned.

A major revision was made to handle very big PSRFITS files, which
are 10 Gigabytes.  To handle indexing of the files and to deal
with reading, with reasonable array sizes, a new set of "Large" routines
were added, and the old (historical) routines were re-written
to call the Large Routines.   The new routines have
the feature that they are re-entrant, and more than one file
may be read using these routines.  The old routines may only
work on one file, the one pointed to by inFITSFile.

*/
#ifdef GBES
#include "vxWorks.h"
#include "usrLib.h"
#endif
#define _LARGEFILE_SOURCE
#define _FILE_OFFSET_BITS 64
#include <stdio.h>
#include "stdlib.h"
#include "string.h"
#include "MATHCNST.H"   /* Mathematical constants. */
#include "KEYWORD.H"    /* FITS keyword constants and structure. */

char *stripWhite (char *);
char *rad2str (double, char *, char *);     /* convert radians to string */
char *mjd2str (long, char *);	            /* convert MJD to date string */
int mjd2AIPS( long inMJD, char * dateStr, char * mapStr);
long AIPS2mjd( char * dateStr);
extern FILE * fopen64( char *, char *);

/* internals */
#ifndef EOS
#define EOS 0
#endif
static FILE * inFITSFile = NULL;

#define MAXLARGE 2147483648            /* 2**31, 1 more than max signed long */

long card2Strs( char inCard[], char aKey[], char aStr[], char aCmt[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* card2Strs() breaks up an input card into three fields, a keyword, a value */
/* and a comment.  Division is based on relations of FITS fields and "="     */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i, j, endI = 0, equalI = 0, dataIA = 0, dataIB = 0;
  char aCard[81] = "";

  strncpy( aCard, inCard, 80);
  aCard[80] = EOS;
  aStr[0] = EOS;
  aCmt[0] = EOS;
  stripWhite( aCard);

  for (i = 0; i < 8 && aCard[i] != ' ' && aCard[i] != '=' && aCard[i] != EOS;
       i ++) 
    aKey[i] = aCard[i];
  aKey[i] = EOS;
  endI = i;

  if (strncmp( aKey, "COMMENT", 7) == 0) {
    if (aStr[8] == '=')                           /* if a COMMENT = card */
      strncpy( aStr, &aCard[9], LENCOMMENT);
    else                                          /* else COMMENT foo card */
      strncpy( aStr, &aCard[8], LENCOMMENT);
    aStr[LENCOMMENT-1] = EOS;
    return(endI);
  } /* end if a comment card */

  for (i = endI; aCard[i] != '=' && aCard[i] != EOS; i ++);  /* find '=' */

  if (aCard[i] != '=') {                          /* if no = may be END card */
    strncpy( aCmt, &aCard[endI], LENCOMMENT);
    aCmt[LENCOMMENT-1] = EOS;
    return(endI);
  }
  else
    equalI = i;

  for (i = equalI + 1; i < equalI + 3; i++) /* find quote, after =  */
    if (aCard[i] == '\'') {
      dataIA = i;
      break;
    }

  if (dataIA > 0) {                  /* if a quoted string */
    j = 0;
    for (i = dataIA; aCard[i] != EOS && i < 40; i++) { /* for all chars*/
      aStr[j] = aCard[i];
      j++;
    }
    aStr[j] = EOS;
    for (i = 1; aStr[i] != EOS; i++) { /* for all chars*/
      if (aStr[i] == '\'' && aStr[i-1] != '\'') { /* if not 2 's */
        dataIB = i + dataIA;         /* record end of string */
        aStr[i+1]  = EOS;           /* terminate after ' */
        break;
      }
    }
  }
  else {                          /* not a quoted string, parsed by blanks */
    /* find first non-blank */
    for (i = equalI + 1; aCard[i] == ' '; i++);
    dataIA = i;                        /* found a non-blank or end of string */
    for (i = dataIA; i < 81 && aCard[i] != '\0' && aCard[i] != ' '; i ++)
      aStr[i-dataIA] = aCard[i];       /* move data to begin of string */
    aStr[i-dataIA] = EOS;              /* terminate data */
    dataIB = i;                        /* one char past end of data */
  }
      
  j = 0;
  if (dataIB > 0 && dataIB < strlen(aCard)) {
    /* find / between data and comment */
    for (i = dataIB; aCard[i] != EOS && aCard[i] != '/'; i ++);
    /* set past white space */
    for (i = i+1; aCard[i] != EOS && aCard[i] == ' '; i ++);
    for (i = i; aCard[i] != EOS; i ++) {
      aCmt[j] = aCard[i];
      j++;
    }
  }
  aCmt[j] = EOS;

  return (dataIB);
} /* end of card2Strs() */

long findCard( char * keyword, char fitsBuffer[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* findCard() takes a 2880 byte of a FITS header, a keyword to match and     */
/* returns index to the card in deck (range 0 to 35) if success, else -1     */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i, iCard = -1;
  
  for (i = 0; i < 36; i ++)                 /* for all cards in deck */
    if (strncmp( keyword, &fitsBuffer[i*80], 8) == 0) {    /* if a match */
      iCard = i;                                           /* save index */
      break;                                               /* stop looking */
    } /* end if a match */

  return( iCard);
} /* end of findCard() */

long parseCard( char aCard[], struct keyword * pKey)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i, lenStr = 0;

  card2Strs( aCard, pKey->key, pKey->str, pKey->cmt);
  pKey->dbl = 0.;                      /* int values to zero */
  stripWhite( pKey->str);
  stripWhite( pKey->cmt);

  if (strcmp("END", pKey->key) == 0 && strlen(pKey->key) == 3) {
    pKey->type = FITSEND;
  }
  else if (strncmp("COMMENT", pKey->key, 7) == 0 || 
           strncmp("HISTORY", pKey->key, 7) == 0) {
    pKey->type = FITSCOMMENT;
    strcpy(pKey->cmt, pKey->str);
  }
  else if (strncmp("SIMPLE", pKey->key, 6) == 0) {
    pKey->type = FITSLOGICAL;
    pKey->dbl = (pKey->str[1] == 'T') ? 1 : 0;
    pKey->str[0] = EOS;
  }
  else if (strncmp("EXTEND", pKey->key, 6) == 0) {
    pKey->type = FITSLOGICAL;
    pKey->dbl = (pKey->str[1] == 'T') ? 1 : 0;
    pKey->str[0] = EOS;
  }
  else if (aCard[8] != '=' )
    pKey->type = FITSUNKNOWN;
  else if (pKey->str[0] == '\'') {     /* if a quoted string */
    pKey->type = FITSSTRING;
    /* remove leading and trailing \' */
    for (i = 1; pKey->str[i] != EOS; i++)  
      pKey->str[i-1] = pKey->str[i];
    pKey->str[i-2] = EOS;
  }
  else { 
    pKey->type = FITSINTEGER;
    stripWhite( pKey->str);
    /* look for decimal/exponential */
    for (i = 0; i < strlen(pKey->str); i++)  
      if (pKey->str[i] == '.' || pKey->str[i] == 'E' || pKey->str[i] == 'e') {
        sscanf(pKey->str, "%le", &(pKey->dbl));
        pKey->type = FITSFLOAT;
        break;
      }
    /* if here, then not a float, is it a byte or integer */       
    lenStr = strlen(pKey->str);
    if ((lenStr < 80) && (lenStr > 2)) {   /* if a plausible length */
      if ((pKey->str[lenStr-1] == 'B')  ||     /* if a byte type */
	  (pKey->str[lenStr-1] == 'b')) { 
	pKey->type = FITSBYTE;
	pKey->str[lenStr-1] = EOS;
	/* this section checks for cards like
TFORM17 = '33554432B'          / NBIN*NCHAN*NPOL*NSBLK int, byte(B) or bit(X)
	*/
	pKey->dbl = atoi( pKey->str);         /* is a byte type field */
      }
    } /* end if a reasonable length */
    if (pKey->type == FITSINTEGER)          /* if an integer, convert string*/
      pKey->dbl = atoi( pKey->str);
  } /* end default numeric type */

  if (pKey->type == FITSSTRING) {      /* look for string like '05/30/95' */
    if (pKey->str[2] == '/' && pKey->str[5] == '/') {
      pKey->type = FITSDATE;
      pKey->dbl = AIPS2mjd( pKey->str);
    }
  }
  if (pKey->type == 100 && strncmp(pKey->key, "NAXIS", 5) == 0)
    printf( "%ld: %-8s = %s / %s\n", 
	    pKey->type, pKey->key, pKey->str, pKey->cmt);
  return (pKey->type);
} /* end of parseCard() */

long getFITSCards( FILE * FITSFile, long maxKeys, struct keyword * keys[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* getFITSCards() reads file and table headers and returns an array of       */
/* keyword structures                                                        */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long nCards = 0, nRead = 0, i = 0, cardType = FITSUNKNOWN;
  char aCard[90] = "";

  for (i = 0; i < maxKeys; i++) {
    nRead = fread( aCard, 80, 1, FITSFile);
    if (nRead != 1) 
      break;
    aCard[80] = EOS;
    cardType = parseCard( aCard, keys[i]);
    stripWhite( aCard);
    nCards++;
    if (cardType == FITSEND) 
      break;
  } /* end of for all cards in header */

  for (i = 0; (i + nCards) % 36 != 0; i++) 
    nRead = fread( aCard, 80, 1, FITSFile);

  return( nCards);
} /* end of getFITSCards */

struct keyword getFITSKey( long maxKeys, char * keyString,
		struct keyword * keys[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* getFITSCards() reads file and table headers and returns an array of       */
/* keyword structures                                                        */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i, n = strlen( keyString);
  struct keyword aKey;

  aKey.type = FITSUNKNOWN;                       /* if FITSUNKNOWN, data bad */

  for (i = 0; i < maxKeys; i++) {
    if (strncmp( keys[i]->key, keyString, n) == 0) {
      aKey = *keys[i];
      break;
    }
  }
  return( aKey);
} /* end of getFITSKey */

long putFITSKey( long maxKey, struct keyword aKey, struct keyword * keys[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* putFITSCards() reads searchs for an existing KEYWORD=Value and replaces   */
/* those values with the input values                                        */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i, found = 0;

  for (i = 0; i < maxKey; i++) {
    if (strncmp( keys[i]->key, aKey.key, 8) == 0) {   /* if a match */
      keys[i]->dbl = aKey.dbl;
      keys[i]->type = aKey.type;
      strncpy(keys[i]->str, aKey.str, LENKEYSTR);
      strncpy(keys[i]->cmt, aKey.cmt, LENCOMMENT);
      keys[i]->str[LENKEYSTR-1] = EOS;
      keys[i]->cmt[LENCOMMENT-1] = EOS;
      found = 1;
      break;
    }
  } /* end for all keywords in list */

  if ( ! found) {                      /* if keyword not already in list */
    keys[maxKey]->dbl = aKey.dbl;      /* transfer the values */
    keys[maxKey]->type = aKey.type;
    strncpy(keys[maxKey]->str, aKey.str, LENKEYSTR);
    strncpy(keys[maxKey]->key, aKey.key, LENFITSKEY);
    strncpy(keys[maxKey]->cmt, aKey.cmt, LENCOMMENT);
    keys[maxKey]->str[LENKEYSTR-1] = EOS;
    keys[maxKey]->cmt[LENCOMMENT-1] = EOS;
    keys[maxKey]->key[LENFITSKEY-1] = EOS;
    maxKey++;
  } /* end if not already in list */

  return( maxKey);
} /* end of putFITSKey */

long getFileName( char * inDir, char * inName, char * inType, char * outName)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* makeFileName() make a file name from a directory and inName.  If the      */
/* the inName is blank, a file name based on the date is created             */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i, dummyMJD = 0, dirMade = 0;
  char dateStr[30] = "", mapStr[30] = "", tmpName[256] = "";

  if ( inDir == NULL)                       /* if null make standard dir */
    strcpy( tmpName, "");                   /* default directory */
  else if (strlen(inDir) == 0)              /* if no chars in name */
    strcpy( tmpName, "");                   /* default directory is current*/
  else
    strncpy( tmpName, inDir, 127);          /* else use input */

  i = strlen( tmpName);                    
  if (i > 0)
    if (tmpName[i-1] != '/')                /* divide directory and file */ 
      strcat( tmpName, "/");
  
  if (inName == NULL)                       /* if in Name not given */
    i = 0;
  else 
    i = strlen( inName);                    /* get length of name */

  if (i > 0 && i < 100)                     /* if input file name not null */
    strcat( tmpName, inName);  
  else {                                    /* else must make file name */
    mjd2AIPS( dummyMJD, dateStr, mapStr);   /* get today and obs first dates*/
    strncat( tmpName, &dateStr[4], 20);     /* use month day part of date */
    stripWhite(tmpName);
  }

  if (inType)                               /* if inType given */
    if (strlen(inType) > 0)
      strncat( tmpName, inType, 20);        /* append to output name */

  if (outName)
    strncpy( outName, tmpName, 100);

  return(dirMade);
} /* end of getFileName() */

FILE * openFITS( char * FITSFileName, long maxKeys, long * nHeader, 
		 struct keyword * headerCards[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* openFITS() opens the input file, if it is different from the previous.    */
/* If new, the File Header cards are read into an array of keyword structures*/
/* The FILE * is NULL on failed open.                          */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ static char lastFileName[256] = "";

  if (strlen(lastFileName) > 0 && *nHeader > 0)  /* if there was a lastfile */
    if (strcmp( lastFileName, FITSFileName) == 0)/* if same file as last */
      return (inFITSFile);                       /* header already read */

  if (strlen( FITSFileName) <= 0) {              /* if invalid name */
    if (inFITSFile) {                            /* just clean up old file */
      fclose(inFITSFile);
      strcpy( lastFileName, FITSFileName);
    }  
    inFITSFile = NULL;
    return(inFITSFile);
  } /* end if invalid name */

#ifdef GBES                               /*if realtime code, use old open */
  if ((inFITSFile = fopen( FITSFileName,"r")) == NULL) {  /* file exists? */
#else
  if ((inFITSFile = fopen64( FITSFileName,"rb")) == NULL) {  /* file exists? */
#endif
    /* file does not exist, try to create */
    printf ("openFITS: File not read-able \"%s\"\n", FITSFileName);
    *nHeader = 0;
    return (inFITSFile);
  }

  *nHeader = getFITSCards( inFITSFile, maxKeys, headerCards);

  strcpy( lastFileName, FITSFileName);

  return (inFITSFile);
} /* end of openFITS() */

char * closeFITS()
/* closeFITS closes the file last opened by openFITS() */
{ if (inFITSFile)
    fclose(inFITSFile);
  inFITSFile = NULL;
  return(NULL);
} /* end of closeFITS() */

long long tableLargeRowR( FILE * fitsFile, long long bytesPerRow, char data[])
/* read one table row from an already open FITS Table file; no error checking*/
{ long long nBytes = 0;

  fread( &data[nBytes], bytesPerRow, 1, inFITSFile); 
  nBytes += bytesPerRow;

  return( nBytes);
} /* end of tableLargeRowR() */

long long tablePaddingR( FILE * fitsFile, long long nBytes)
/* tablePaddingR() reads the last few padding bytes of a FITS Table */
{ long long i = 0, nRead = nBytes, fitsBlockSize = 2880;
  long inArray[4] = { 0., 0., 0., 0.};

  do {                               /* modulo computation work-a-round */
    nRead = nRead - fitsBlockSize;
  } while (nRead > 0);

  if (nRead < 0) { 
    nRead = nRead + fitsBlockSize;
    for (i = 0; i < nRead; i++)      /* read to end of 2880 byte block */
      fread( inArray, 1, 1, fitsFile); 
  }
  return( nRead);
} /* end of tablePaddingR() */

long tableDataR( FILE * fitsFile, long nRows, long bytesPerRow, char data[])
{ long i, nBytes = 0;
  long long largeBytes = 0, largeBytesPerRow = bytesPerRow;

  if ((nRows * bytesPerRow > 0) && data) { /* if any data */
    for (i = 0; i < nRows; i ++) {
      tableLargeRowR( fitsFile, largeBytesPerRow, &data[nBytes]);
      largeBytes += largeBytesPerRow;
    } /* end for all points */
  } /* end if non null FITS */

  largeBytes += tablePaddingR( fitsFile, largeBytes);

  if (largeBytes >= MAXLARGE) {
    fprintf( stderr, "Warning bytes read, %lld, exceeds max LONG type %lld\n",
	     largeBytes, (long long)MAXLARGE);
  } 

  nBytes = largeBytes;    
  return( nBytes);
} /* end of tableDataR() */

long long tableLargeDataR( FILE * fitsFile, long nRows, 
			   long long bytesPerRow, char data[])
{ long long i = 0, nBytes = 0;

  if ((nRows * bytesPerRow > 0) && data) { /* if any data */
    for (i = 0; i < nRows; i ++) {
      tableLargeRowR( fitsFile, bytesPerRow, &data[nBytes]);
      nBytes += bytesPerRow;
    } /* end for all points */
  } /* end if non null FITS */

  nBytes += tablePaddingR( fitsFile, nBytes);

  return( nBytes);
} /* end of tableDataR() */

long long FITSNextLargeTableHeaderR( FILE * fitsFile, long maxKeys, 
	        long * nTable, struct keyword * tableCards[], 
		long * nRows, long long * bytesPerRow)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* FITSNextTableR() reads the next table header in an open fits file         */
/* Note that the data are not read by this routine                           */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long long nBytes = 0, fitsBlockSize = 2880;
  long nBlocks = 0;
  struct keyword aKey;  

  if (fitsFile == NULL) {            /* if file open failed, exit */
    fprintf( stderr, "FITSNextTableR: file not open\n");
    return( -1);
  }
  *nTable = getFITSCards( fitsFile, maxKeys, tableCards);

  nBlocks = *nTable % 36;           /* figure out how many bytes were read */
  if (nBlocks * 36 < *nTable)       /* fits blocks have 36 cards of 80 bytes */
    nBlocks++;
  nBytes = fitsBlockSize*nBlocks;

  aKey = getFITSKey( *nTable, "NAXIS2", tableCards);
  if (aKey.type == FITSINTEGER)
    *nRows = aKey.dbl;
  else {
    return( nBytes);
  }

  aKey = getFITSKey( *nTable, "NAXIS1", tableCards);
  if (aKey.type == FITSINTEGER)
    *bytesPerRow = aKey.dbl;
  else {
    *bytesPerRow = 0;
    return( nBytes);
  }
  return(nBytes);
} /* end of FITSNextLargeTableHeaderR() */

long FITSNextTableR( long maxKeys, 
	        long * nTable, struct keyword * tableCards[], 
		long * nRows, long * bytesPerRow, char * data)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* FITSNextTableR() reads the next table in an open fits file                */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long nBytes = 0;
  long long largeBytes = 0, largeBytesPerRow = 0;

  largeBytes = FITSNextLargeTableHeaderR( inFITSFile, maxKeys, nTable, 
					  tableCards, nRows, 
					  &largeBytesPerRow);
  if (largeBytes <= 0)
    return( -1);
  *bytesPerRow = largeBytesPerRow;     /* transfer to longs */

  largeBytes += tableDataR( inFITSFile, *nRows, *bytesPerRow, data);

  nBytes = largeBytes;
  return(nBytes);
} /* end of FITSNextTableR() */

FILE * FITSLargeHeaderR( char * FITSDir, char * FITSFileName, long maxKeys, 
		long * nHeader, struct keyword * headerCards[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* FITSLargeHeaderR() reads and returns all FITS file header cards           */
/* INPUTS: FITSDir - directory where data will be placed. Lowest level dir   */
/*         will be created if not present.                                   */
/*         FITSFileName - name of file to be read. if Null, then error       */
/*         nHeader - number of FITS file header cards to read from the file  */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ char fileName[256] = "", inType[100] = "";
  FILE * largeFITSFile = NULL;

  getFileName( FITSDir, FITSFileName, inType, fileName);

  largeFITSFile = openFITS( fileName, maxKeys, nHeader, headerCards);

  return(largeFITSFile);
} /* end of FITSLargeHeaderR() */

long FITSHeaderR( char * FITSDir, char * FITSFileName, long maxKeys, 
		long * nHeader, struct keyword * headerCards[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* FITSHeaderR() reads and returns all FITS file header cards                */
/* INPUTS: FITSDir - directory where data will be placed. Lowest level dir   */
/*         will be created if not present.                                   */
/*         FITSFileName - name of file to be read. if Null, then error       */
/*         nHeader - number of FITS file header cards to read from the file  */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long nBytes = 0;
  long long nBlocks = 0, fitsBlockSize = 2880;
  char fileName[256] = "", inType[100] = "";

  getFileName( FITSDir, FITSFileName, inType, fileName);

  inFITSFile = openFITS( fileName, maxKeys, nHeader, headerCards);

  if (inFITSFile == NULL)            /* if file open failed, exit */
    return(-1);

  nBlocks = *nHeader % 36;          /* figure out how many bytes were read */
  if (nBlocks * 36 < *nHeader)      /* fits blocks have 36 cards of 80 bytes */
    nBlocks++;
  nBytes = fitsBlockSize*nBlocks;

  return(nBytes);
} /* end of FITSHeaderR() */

long FITSTableR( char * FITSDir, char * FITSFileName, long maxKeys, 
		long * nHeader, struct keyword * headerCards[],
	        long * nTable, struct keyword * tableCards[], 
		long * nRows, long * bytesPerRow, char * data)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* FITSTableR() creats/appends a FITS table to a file                        */
/* INPUTS: FITSDir - directory where data will be placed. Lowest level dir   */
/*         will be created if not present.                                   */
/*         FITSFileName - name of file to be created. if Null, then a file   */
/*         with todays date is created.                                      */
/*         nHeader - number of FITS file header cards to be added to file    */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long nBytes = 0;
  long long largeBytesPerRow = 0;

  nBytes = FITSHeaderR( FITSDir, FITSFileName, maxKeys, nHeader, headerCards);
  if (nBytes < 0)
    return(nBytes);

  nBytes += FITSNextLargeTableHeaderR( inFITSFile, maxKeys, 
				       nTable, tableCards, 
				       nRows, &largeBytesPerRow);

  nBytes += tableLargeDataR( inFITSFile, *nRows, largeBytesPerRow, data);

  *bytesPerRow = largeBytesPerRow;

  return(nBytes);
} /* end of FITSTableR() */

FILE * FITSLargeTableR( char * FITSDir, char * FITSFileName, long maxKeys, 
			long * nHeader, struct keyword * headerCards[],
			long * nTable, struct keyword * tableCards[], 
			long * nRows, long long * largeBytesPerRow, 
			long long * outBytes)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* FITSLargeTableR() creats/appends a FITS table to a file                   */
/* INPUTS: FITSDir - directory where data will be placed. Lowest level dir   */
/*         will be created if not present.                                   */
/*         FITSFileName - name of file to be created. if Null, then a file   */
/*         with todays date is created.                                      */
/*         nHeader - number of FITS file header cards to be added to file    */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long long nBytes = 0;
  FILE * largeFITSFile = NULL;

  largeFITSFile = FITSLargeHeaderR( FITSDir, FITSFileName, maxKeys, nHeader, 
			     headerCards);
  if (largeFITSFile == NULL)
    return(largeFITSFile);

  nBytes = FITSNextLargeTableHeaderR( largeFITSFile, maxKeys, 
				      nTable, tableCards, 
				      nRows, largeBytesPerRow);

  /* IMPORTANT!!! the user must read all rows in the table *and* call */
  /* tablePaddingR() to complete the table read, before going to next table */
  *outBytes = nBytes;

  return(largeFITSFile);
} /* end of FITSLargeTableR() */
