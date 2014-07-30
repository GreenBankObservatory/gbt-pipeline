 /* File readIdlFits.c, version 1.8, released  10/11/22 at 13:19:50 
   retrieved by SCCS 14/04/23 at 15:50:53     

%% program to load IDL (sdfits) data into an IDL strcuture
:: spectra mapping utility

HISTORY
101014 GIL reduce printout by one message
091230 GIL fill in iMjd and dMjd values
070706 GIL note changes in frames
070704 GIL allow re-reading more tables in file
070531 GIL more diagnostic info
051025 GIL allow reading a single visiblity
050902 GIL read lat,long, elev, fix frequency update
050901 GIL complete processing of all keywords
050831 GIL return some standard parameters in "go" structure
050829 GIL parse the polarization and velecity keywords
050815 GIL version that reads some IDL keywords
050716 GIL start to actually read keywords
050715 GIL initial version based on readSpectrometer.c

DESCRIPTON
readIdlFits() reads a fits file and passes data in an idl Structure
OMISSION!
Only one spectrum per from supported.
*/

#include "stdio.h"
#include "stdlib.h"
#include "string.h"
#include "math.h"
#include "time.h"
#include "fitsio.h"
#include "STDDEFS.H"
#include "MATHCNST.H"
#include "gbtIdl.h"
#include "gbtGo.h"
#include "gbtAntenna.h"
#include "gbtScanInfo.h"

/* externals */
extern struct GOPARAMETERS go;
extern struct GBTPOSITION gbtPos;
extern char * mjd2str( long mjd,  char *);
extern char * dateObs2DMjd( char * dateObs, double * dMjd);
extern char * stripWhite( char *);
extern char * cvrtuc( char *);
extern char * fitsReadScan( fitsfile *pFitsFile, long * scan);
extern char * readScanInfo( fitsfile *pFitsFile,  /* FITS file, fitsio.h*/
		     long printFitsInput, 
		     struct SCANINFO * pScanInfo);
extern long aGreaterThanB( char * aVersion, char * bVersion);
extern char * findTableExtension( char * fullFileName, char * extensionName, 
				  long * nRows, long * nBytesPerRow);
extern char * fileSize( char * fileName, long * fileLength);

extern long realTime;           /* if realtime, then re-read file info */
extern char * findFitsTable ( fitsfile * fptr, char * extension, int * hdu);

/* internals */
#define MAXNAMELENGTH 256
#define FITSBLOCKSIZE 2880

static char lastIdlSdfitsFileName[MAXNAMELENGTH] = "";/* for getSpec...() */

char * initLastIdlSdfitsFile() 
/* initLastSpectroemterFile() initializes the last file name to re-examine */
/* the file contents for dynamic file checking */
{
  lastIdlSdfitsFileName[0] = EOS;
  return(NULL);
} /* end of initLastIdlSdfitsFile() */

char * closeIdlSdfits( fitsfile * fptr)
{ int status = 0;
  char * errMsg = NULL; 

  if (fptr != NULL) {
    if ( fits_close_file(fptr, &status) )
      errMsg = "Failed to close FITS file";
  }
  return(errMsg);
} /* end of closeIdlSdfits */

char * openIdlSdfits ( char * fileName, 
		       fitsfile **fptr,  /* pointer to the FITS file*/
		       long doPrint,
		       GBTIDL * idlSdfits,
		       struct SCANINFO * pScanInfo)
/**********************************************************************/
/* Print out all the header keywords in all extensions of a FITS file */
/**********************************************************************/
{ int status = 0, hdutype = 0, i = 1;
  long nRows = 0, nBytesPerRow = 0, mjd = 0;
  char * errMsg = NULL, dateStr[FLEN_CARD] = "", tableName[32] = "SINGLE DISH";

  closeIdlSdfits( *fptr);               /* close file if OPEN */
  *fptr = NULL;

  if (strlen(fileName) > 1) {
    /* check whether this file has the DATA table required */
    errMsg = findTableExtension( fileName, tableName, &nRows, &nBytesPerRow);
  }

  /* if no DATA, no need to go further */
  if (errMsg) {
    fprintf( stderr, "Searching for Table: %s\n", tableName);
    fprintf( stderr, "Error Opening file : %s\n", fileName);
    return(errMsg);
  }

  if (nRows < 1)                           /* if not many rows, check size */
    return("No data in in file (yet)");

  /* now check that file is a fits file and can be read */
  if ( fits_open_file(fptr, fileName, READONLY, &status) ) {
    fprintf( stderr, "Failed to open fits File: %s\n",
	     fileName);
    return( "Failed to open FILE");
  } /* end of fits file open */

  /* get all idlSdfits scan parameters */
  errMsg = readScanInfo( *fptr, doPrint, pScanInfo);

  /* attempt to move to next HDU */
  fits_movabs_hdu(*fptr, i, &hdutype, &status);

  mjd = pScanInfo->dMjd;
  mjd2str( mjd, dateStr);
  strcpy( idlSdfits->date, dateStr);

  strcpy( idlSdfits->source,  pScanInfo->object );
  strcpy( idlSdfits->line_id,  pScanInfo->projId );
  strcpy( idlSdfits->scan_type,   pScanInfo->obsId);

  idlSdfits->scan_num = pScanInfo->scanNumber;

  return(errMsg);
} /* end of openIdlSdfits() */

#define NKEYS       56
#define OBJECT       0
#define BANDWID      1
#define DATE_OBS     2
#define DURATION     3
#define EXPOSURE     4
#define TSYS         5
#define DATA         6
#define TDIM7        7
#define TUNIT7       8
#define CTYPE1       9
#define CRVAL1      10
#define CRPIX1      11
#define CDELT1      12
#define CTYPE2      13
#define CRVAL2      14
#define CTYPE3      15
#define CRVAL3      16
#define CRVAL4      17
#define OBSERVER    18
#define OBSID       19
#define SCAN        20
#define OBSMODE     21
#define FRONTEND    22
#define TCAL        23
#define VELDEF      24
#define VFRAME      25
#define RVSYS       26
#define OBSFREQ     27
#define LST         28
#define AZIMUTH     29
#define ELEVATIO    30
#define RESTFREQ    31
#define EQUINOX     32
#define SAMPLER     33
#define FEED        34
#define SRFEED      35
#define BEAMXOFF    36
#define BEAMEOFF    37
#define SIDEBAND    38
#define PROCSEQN    39
#define PROCSIZE    40
#define LASTON      41
#define LASTOFF     42
#define VELOCITY    43
#define SIG         44
#define CAL         45
#define FOFFREF1    46
#define BACKEND     47
#define PROJID      48
#define TELESCOP    49
#define SITELONG    50
#define SITELAT     51
#define SITEELEV    52
#define IFNUM       53
#define INT         54
#define NSAVE       55

/* PROJID  = 'TREG_111504'        / project identifier */
/* TELESCOP= 'NRAO_GBT'           / the telescope used */
/* BACKEND = 'Spectrometer'       / backend device */
/* SITELONG=            -79.83983 / E. longitude of intersection of the az/e*/
/* SITELAT =             38.43312 / N. latitude of intersection of the az/el */
/* SITEELEV=              824.595 / height of the intersection of az/el axes */
/* CTYPE4  = 'STOKES  '           / fourth axis is Stokes */

char * getIdlFitsHeader ( fitsfile * fptr, long doPrint,
		    int * hdu, long * nRows,
		    long keyIndex[], char * keyForms[])
/* getIdlFitsHeader()() parses the keywords in idl fits 'SINGLE DISH'  table */
/* The TABLE keywords may be in any order and important ones are selected */
/* by an indexing scheme.  Returns NULL on OK, else error message */ 
{ char * errMsg = NULL, tempString[MAXNAMELENGTH] = "", 
    keyword[MAXNAMELENGTH] = "", comment[FLEN_CARD] = "", 
    value[FLEN_CARD] = "";
 static char * keywordName[NKEYS] = {
    "OBJECT",    "BANDWID",    "DATE-OBS",  "DURATION",  "EXPOSURE",
    "TSYS",      "DATA",       "TDIM7",     "TUNIT7",    "CTYPE1",
    "CRVAL1",    "CRPIX1",     "CDELT1",    "CTYPE2",    "CRVAL2",
    "CTYPE3",    "CRVAL3",     "CRVAL4",    "OBSERVER",  "OBSID",
    "SCAN",      "OBSMODE",    "FRONTEND",  "TCAL",      "VELDEF",
    "VFRAME",    "RVSYS",      "OBSFREQ",   "LST",       "AZIMUTH",
    "ELEVATIO",  "RESTFREQ",   "EQUINOX",   "SAMPLER",   "FEED",
    "SRFEED",    "BEAMXOFF",   "BEAMEOFF",  "SIDEBAND",  "PROCSEQN",
    "PROCSIZE",  "LASTON",     "LASTOFF",   "VELOCITY",  "SIG",
    "CAL",       "FOFFREF1",   "BACKEND",   "PROJID",    "TELESCOP", 
    "SITELONG",  "SITELAT",    "SITEELEV",  "IFNUM",     "INT", 
    "NSAVE"};
  int status = 0;
  long nFields = 0, i = 0, jj = 0, kk = 0;

  if (fptr == NULL)
    return("Invalid FITS file Pointer");

  errMsg = findFitsTable ( fptr, "SINGLE DISH", hdu);
  if (errMsg) {
    fprintf ( stderr, "getIdl: could not find 'SINGLE DISH' table\n");
    return(errMsg);
  } /* end if error opening sampler/port table */

  /* get the number of rows in the file, to determin if a new SAMPLER TABLE */
  fits_read_keyword( fptr, "TFIELDS", value, comment, &status);
  if (status == 0)
    sscanf( value, "%ld", &nFields);

  /* get the number of rows in the file */
  fits_read_keyword( fptr, "NAXIS2", value, comment, &status);
  if (status == 0)
    sscanf( value, "%ld", nRows);

  if (*nRows <= 0)
    return( "Invalid Number of Rows");

  for (kk = 0; kk < NKEYS; kk++) { /* init indices to illegal value */
     keyIndex[i] = -1;
     keyForms[i] = NULL;
  }

  /* now match all TYPE? keywords to table columns needed */
  for (jj = 1; jj <= NKEYS*5; jj++)  {
    sprintf( keyword, "TTYPE%ld", jj);
    status = 0;
    if (fits_read_key_str(fptr, keyword, tempString, 
			      comment, &status) == OK) {
      for (kk = 0; kk < NKEYS; kk++) {
	stripWhite( tempString);
	cvrtuc( tempString);
	/* if found a matching index */
	if (strcmp( tempString, keywordName[kk]) ==  0) {
	  keyIndex[kk] = jj;
	  sprintf( keyword, "TFORM%ld", jj);
	  /* now find type if form is found */
          if (fits_read_key_str(fptr, keyword, tempString, 
			      comment, &status) == OK) {
	    keyForms[kk] = (char *)malloc(16);
	    tempString[15] = EOS;
	    strcpy( keyForms[kk], tempString);
	  }	    
	}
      } /* end for all desired keys */
    } /* end if this keyword found */
  } /* end for all desired keys */

  status = 0;

  if (doPrint) {
    for (jj = 0; jj < NKEYS; jj++)
      fprintf( stderr, "Key[%2ld]: %8s %8s %3ld\n", jj, keywordName[jj], 
	       keyForms[jj], keyIndex[jj]);
  }

  return(errMsg);
} /* end of getIdlFitsHeader() */ 

char * readIdlFits ( char * fileName, long iRow, long * nRows, 
			 long doPrint, GBTIDL * idlSdfits)
/* getIdlSdfits() gets multi-dimensional data array out of the current */
/* FITS HDU.  The fits file must already be open and positioned at the data */
/* table */
{ char * errMsg = NULL, value[80] = "", tempValue[80] = "",
    comment[80] = "", dateObs[200] = "", * strings[3] = { NULL, NULL, NULL},
    tdim7[80] = "", ctype2[80] = "", ctype3[80] = "", 
    frontend[80] = "", backend[80] = "", sampler[80] = "", sig[80] = "",
    cal[80] = "", sideband[80];
  int j = 0, status = 0, n = 0, anynull = 0;
  long felem = 1, nelem = 1, i = 0, debug = FALSE, 
    naxes[7] = {0,0,0,0,0,0,0}, longs[32];
  float floatnull = 0.;
  double doublenull = 0, doubles[32], vFrame = 0, rVSys = 0, factor = 1.,
    dMjd = 0.;
  /* keep track of times to recognize a new scan */
  static char lastDateObs[200] = "", lastFileName[200] = "";
  static long lastRow = 1, lastNRows = 1;
  /* keep name to recognize a new scan */
  static fitsfile * fitsFile = NULL;
  static long printCount = 0;
  static struct SCANINFO scanInfo;
  static long keyIndex[NKEYS];
  static char * keyForms[NKEYS];
  static int hdu = 1;

  if (idlSdfits == NULL)
    return( "Null output data pointer");

  if (strcmp( fileName, lastFileName) != 0) {
    for (i = 0; i < NKEYS; i++)
      keyForms[i] = NULL;

    /* now check that file is a fits file and can be read */
    if ( fits_open_file( &fitsFile, fileName, READONLY, &status) ) {
      fprintf( stderr, "Failed to open fits File: %s\n",
	       fileName);
      return( "Failed to open FILE");
    } /* end of fits file open */

    if (debug && printCount < 1) 
      fprintf( stderr, "readIdlFits: about to read file header\n");
    
    errMsg = openIdlSdfits ( fileName, 
		       &fitsFile,  /* pointer to the FITS file*/
		       debug, idlSdfits, &scanInfo);

    if (errMsg) { 
      fprintf( stderr, "openIdl Error: %s\n", errMsg);
      fprintf( stderr, "IDL File Name: %s\n", fileName);
      return( errMsg);
    }
    errMsg = getIdlFitsHeader ( fitsFile, doPrint,
				&hdu, nRows, keyIndex, keyForms);
    strcpy( lastFileName, fileName);
  } /* end of time to open a new file */

  if (errMsg) {
    fprintf( stderr, "getIdl: %s\n", errMsg);
    return( errMsg);
  }

  /* get the number of rows in the file */
  fits_read_keyword( fitsFile, "NAXIS2", value, comment, &status);
  status = 0;
  sscanf( value, "%ld", nRows);

  if (*nRows <= 0) {
    return( "Invalid Number of Rows");
  }
  else if (*nRows != lastNRows) {
    if (doPrint)
      fprintf ( stderr, 
		"Reading IDL Keep File: Number of Rows = %ld\n", *nRows);
    lastRow = 1;
    lastNRows = *nRows;
  }
 
  if (keyIndex[TDIM7] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[TDIM7], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) {
      strcpy( tdim7, strings[0]);
    }
    else {
      fprintf ( stderr, "readIdlFits: Cound not read data dimension\n");
      fprintf ( stderr, "Row %4ld (%ld)\n", iRow+1, keyIndex[TDIM7]);
      return("Cound not read data dimension");
    }
  } /* end if data dimension found */

  n = j = 0;
  /* parse the three components of TDIM7 = "(8,4,2)" */
  for (i = 0; i < strlen(value); i++) {
    if (tdim7[i] == ')' || tdim7[i] == ',') {
      tempValue[j] = '\0';
      sscanf( tempValue, "%ld", &naxes[n]);
      j = 0;
      n++;
      tempValue[j] = '\0';
    }
    else if (tdim7[i] != '(' && tdim7[i] != '\'' && tdim7[i] != ' ') {
      tempValue[j] = tdim7[i];
      j++;
    }
  } /* end of all chars of TDIM3 */

  if (naxes[0] > MAXIDLPOINTS) {
    fprintf ( stderr, "Number of channels, %ld, exceeds the limit of %ld.\n", naxes[0], MAXIDLPOINTS);
    return("Too many channels");
  }

  if (debug)
    fprintf( stderr, "Spectrum has %ld channels\n", naxes[0]);

  /* process Strings */
  if (keyIndex[OBJECT] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[OBJECT], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( idlSdfits->source, strings[0]);
    else
      strcpy( idlSdfits->source, "StaryNight");
    strncpy( go.object, idlSdfits->source, GOSTRLENGTH - 1);
    go.object[GOSTRLENGTH - 1] = EOS;
  } /* end if keyword found */
  else
    strcpy( idlSdfits->source, "StaryNight");

  if (keyIndex[OBSID] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[OBSID], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strncpy( go.observationId, strings[0], GOSTRLENGTH - 1);
  } /* end if keyword found */
  go.observationId[GOSTRLENGTH - 1] = EOS;

  if (keyIndex[OBSERVER] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[OBSERVER], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strncpy( go.observer, strings[0], GOSTRLENGTH - 1);
  } /* end if keyword found */
  go.observer[GOSTRLENGTH - 1] = EOS;

  if (keyIndex[OBSMODE] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[OBSMODE], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strncpy( go.obsType, strings[0], GOSTRLENGTH - 1);
  } /* end if keyword found */
  go.obsType[GOSTRLENGTH - 1] = EOS;

  if (keyIndex[PROJID] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[PROJID], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strncpy( go.projectId, strings[0], GOSTRLENGTH - 1);
  } /* end if keyword found */
  go.projectId[GOSTRLENGTH - 1] = EOS;

  if (keyIndex[DATE_OBS] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[DATE_OBS], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) {
      strcpy( idlSdfits->date, strings[0]);
      dateObs2DMjd( idlSdfits->date, &dMjd);
      go.dateObs = dMjd;
      idlSdfits->dMjd = dMjd;
    }
  } /* end if keyword found */

  if (keyIndex[VELDEF] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[VELDEF], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( idlSdfits->vel_def, strings[0]);
    strncpy( go.velocityDef,  idlSdfits->vel_def, GOSTRLENGTH -1);
  } /* end if keyword found */
  go.velocityDef[GOSTRLENGTH -1] = EOS;

  if (keyIndex[TELESCOP] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[TELESCOP], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strncpy( go.telescope, strings[0], GOSTRLENGTH-1);
  } /* end if keyword found */
  go.telescope[GOSTRLENGTH -1] = EOS;

  if (keyIndex[FRONTEND] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[FRONTEND], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( frontend, strings[0]);
  } /* end if keyword found */

  if (keyIndex[BACKEND] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[BACKEND], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( backend, strings[0]);
  } /* end if keyword found */

  if (keyIndex[BACKEND] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[BACKEND], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( backend, strings[0]);
  } /* end if keyword found */

  if (keyIndex[SAMPLER] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[SAMPLER], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( sampler, strings[0]);
  } /* end if keyword found */

  if (keyIndex[SIG] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[SIG], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( sig, strings[0]);
  } /* end if keyword found */

  if (keyIndex[CAL] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[CAL], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( cal, strings[0]);
  } /* end if keyword found */

  if (keyIndex[SIDEBAND] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[SIDEBAND], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( sideband, strings[0]);
  } /* end if keyword found */

  if (keyIndex[CTYPE2] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[CTYPE2], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( ctype2, strings[0]);

    if (strstr( ctype2, "GL") != 0)
      strcpy( go.coordSys, "GALACTIC");
    else if (strstr( ctype2, "RA") != 0)
      strcpy( go.coordSys, "RADEC");
  } /* end if keyword found */

  if (keyIndex[CTYPE1] > 0) {   /* store first axis type */
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[CTYPE1], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( idlSdfits->channels, strings[0]);
  } /* end if keyword found */

  if (keyIndex[TUNIT7] > 0) {   /* store data calibration */
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[TUNIT7], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( idlSdfits->calibrate, strings[0]);
  } /* end if keyword found */

  if (keyIndex[CTYPE3] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[CTYPE3], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( ctype3, strings[0]);
  } /* end if keyword found */

  if (keyIndex[CTYPE3] > 0) {
    strings[0] = strings[1] = value; status = 0;
    fits_read_col(fitsFile, TSTRING, keyIndex[CTYPE3], iRow+1, 
		    felem, nelem, &floatnull, strings, &anynull, &status);
    if (status == 0) 
      strcpy( ctype3, strings[0]);
  } /* end if keyword found */

  if (keyIndex[BANDWID] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[BANDWID], iRow+1, 
		  felem, nelem, &doublenull, doubles, &anynull, &status);
    if (status == 0) {
      if (doubles[0] < 2000.)                 /* if in MHz */
	doubles[0] *= 1.E6;                   /* convert to Hz */
      idlSdfits->bw = doubles[0];
    }
  } /* end if keyword found */

  if (keyIndex[RESTFREQ] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[RESTFREQ], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	idlSdfits->rest_freq = doubles[0];
      go.restFreq = idlSdfits->rest_freq;
  } /* end if keyword found */

  if (keyIndex[OBSFREQ] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[OBSFREQ], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	idlSdfits->sky_freq = doubles[0];
  } /* end if keyword found */

  if (keyIndex[VFRAME] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[VFRAME], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	vFrame = doubles[0];
      if ((debug  || (iRow == 1)) && doPrint )
	fprintf( stderr, "VFRAME:   %10.2lf\n", vFrame);
  } /* end if keyword found */

  if (keyIndex[EQUINOX] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[EQUINOX], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	go.equinox = doubles[0];
  } /* end if keyword found */

  if (keyIndex[RVSYS] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[RVSYS], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	rVSys = doubles[0];
      if ((debug  || iRow == 1) && doPrint)
	fprintf( stderr, "RVSYS:    %10.2lf\n", rVSys);
  } /* end if keyword found */

  if (keyIndex[AZIMUTH] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[AZIMUTH], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	idlSdfits->az = doubles[0];
  } /* end if keyword found */

  if (keyIndex[ELEVATIO] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[ELEVATIO], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	idlSdfits->el = doubles[0];
  } /* end if keyword found */

  if (keyIndex[VELOCITY] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[VELOCITY], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	idlSdfits->vel = doubles[0];
      go.velocity = idlSdfits->vel;
  } /* end if keyword found */

  if (keyIndex[LST] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[LST], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	idlSdfits->lst = doubles[0];
  } /* end if keyword found */

  if (keyIndex[TCAL] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[TCAL], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	idlSdfits->tcal = doubles[0];
  } /* end if keyword found */

  if (keyIndex[TSYS] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[TSYS], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	idlSdfits->tsys = doubles[0];
  } /* end if keyword found */

  if (keyIndex[EXPOSURE] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[EXPOSURE], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	idlSdfits->tintg = doubles[0];
  } /* end if keyword found */

  if (keyIndex[CRVAL1] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[CRVAL1], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	idlSdfits->sky_freq = doubles[0];
  } /* end if keyword found */

  if (keyIndex[CRPIX1] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[CRPIX1], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	idlSdfits->ref_ch = doubles[0];
  } /* end if keyword found */

  if (keyIndex[CDELT1] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[CDELT1], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
      if (status == 0) 
	idlSdfits->delta_x = doubles[0];
  } /* end if keyword found */

  if (keyIndex[CRVAL2] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[CRVAL2], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
    if (status == 0) 
      idlSdfits->ra = doubles[0];
    if ((debug  || iRow == 1) && doPrint)
      fprintf( stderr, "CRVAL2 %s: %7.2lf\n", ctype2, idlSdfits->ra);
  } /* end if keyword found */

  if (keyIndex[CRVAL3] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[CRVAL3], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
    if (status == 0) 
      idlSdfits->dec = doubles[0];
    if ((debug  || iRow == 1) && doPrint)
      fprintf( stderr, "CRVAL3 %s: %7.2lf\n", ctype3, idlSdfits->dec);
  } /* end if keyword found */

  if (keyIndex[SITELAT] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[SITELAT], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
    if (status == 0) 
      gbtPos.siteLat = doubles[0];
  } /* end if keyword found */

  if (keyIndex[SITELONG] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[SITELONG], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
    if (status == 0) 
      gbtPos.siteLon = doubles[0];
  } /* end if keyword found */

  if (keyIndex[SITEELEV] > 0) {
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[SITEELEV], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
    if (status == 0) 
      gbtPos.siteElev = doubles[0];
  } /* end if keyword found */

  if (keyIndex[CRVAL4] > 0) { /* if found the stokes axis */
    status = 0;
    fits_read_col(fitsFile, TDOUBLE, keyIndex[CRVAL4], iRow+1, 
		    felem, nelem, &doublenull, doubles, &anynull, &status);
    if (status == 0) {
      /* STOKES        <-> polarization */
      /* -1,-2,-3,-4        RR,LL,RL,LR */
      /* -5,-6,-7,-8        XX,YY,XY,YX */
      /* 1,2,3,4            I,Q,U,V */
      if (doubles[0] == -1)
	strcpy( idlSdfits->pol_id, "RR");
      else if (doubles[0] == -2)
	strcpy( idlSdfits->pol_id, "LL");
      else if (doubles[0] == -3)
	strcpy( idlSdfits->pol_id, "RL");
      else if (doubles[0] == -4)
	strcpy( idlSdfits->pol_id, "LR");
      else if (doubles[0] == -5)
	strcpy( idlSdfits->pol_id, "XX");
      else if (doubles[0] == -6)
	strcpy( idlSdfits->pol_id, "YY");
      else if (doubles[0] == -7)
	strcpy( idlSdfits->pol_id, "XY");
      else if (doubles[0] == -8)
	strcpy( idlSdfits->pol_id, "YX");
      else if (doubles[0] == 4)
	strcpy( idlSdfits->pol_id, "V");
      else if (doubles[0] == 3)
	strcpy( idlSdfits->pol_id, "U");
      else if (doubles[0] == 2)
	strcpy( idlSdfits->pol_id, "Q");
      else
	strcpy( idlSdfits->pol_id, "I");
    }
    else
      strcpy( idlSdfits->pol_id, "I");

    if (debug)
      fprintf( stderr, "CRVAL4: %7.2lf %s\n", doubles[0], idlSdfits->pol_id);
  } /* end if keyword found */

  idlSdfits->data_points = naxes[0];
  if (keyIndex[DATA] > 0) {
    nelem = naxes[0];
    status = 0;
    fits_read_col(fitsFile, TFLOAT, keyIndex[DATA], iRow+1, 
		  felem, nelem, &floatnull, 
		  &(idlSdfits->data[0]), &anynull, &status);
  }
  else 
    fprintf( stderr, "readIdl: DATA column not found\n");

  nelem = 1;

  /* process longs */
  if (keyIndex[SCAN] > 0) {
    status = 0;
    fits_read_col(fitsFile, TLONG, keyIndex[SCAN], iRow+1, 
		  felem, nelem, &floatnull, 
		  longs, &anynull, &status);
    if (status == 0)
      idlSdfits->scan_num = longs[0];
  }

  /* process longs */
  if (keyIndex[INT] > 0) {
    status = 0;
    fits_read_col(fitsFile, TLONG, keyIndex[INT], iRow+1, 
		  felem, nelem, &floatnull, 
		  longs, &anynull, &status);
    if (status == 0)
      idlSdfits->iIntegration = longs[0];
  }

  if (keyIndex[PROCSIZE] > 0) {
    status = 0;
    fits_read_col(fitsFile, TLONG, keyIndex[PROCSIZE], iRow+1, 
		  felem, nelem, &floatnull, 
		  longs, &anynull, &status);
    if (status == 0)
      idlSdfits->procSize = longs[0];
    go.procSize = idlSdfits->procSize;
  }

  if (keyIndex[PROCSEQN] > 0) {
    status = 0;
    fits_read_col(fitsFile, TLONG, keyIndex[PROCSEQN], iRow+1, 
		  felem, nelem, &floatnull, 
		  longs, &anynull, &status);
    if (status == 0)
      idlSdfits->procSeqn = longs[0];
    go.procSeqn = idlSdfits->procSeqn;
  }

  if (keyIndex[LASTON] > 0) {
    status = 0;
    fits_read_col(fitsFile, TLONG, keyIndex[LASTON], iRow+1, 
		  felem, nelem, &floatnull, 
		  longs, &anynull, &status);
    if (status == 0)
      go.lastOn = longs[0];
  }

  if (keyIndex[LASTOFF] > 0) {
    status = 0;
    fits_read_col(fitsFile, TLONG, keyIndex[LASTOFF], iRow+1, 
		  felem, nelem, &floatnull, 
		  longs, &anynull, &status);
    if (status == 0)
      go.lastOff = longs[0];
  }

  strcpy( lastDateObs, dateObs);

  /* deterimine if the desired frame is different data frame */
  /* DATA FRAME    == "CTYPE1" == idl->channels */
  /* DESIRED FRAME == "VELDEF" == idl->vel_def  */
  /* if frames are different */
  if ( strncmp( &idlSdfits->vel_def[5], &idlSdfits->channels[5],3) != 0) {
    /* Bob Garwood's  conversion of frequencies from topocentric */
    /* to the refernce frame requested by the observer: */
    /* factor = sqrt((c+vframe)/(c-vframe)) */
    if ((C_LIGHT-vFrame) != 0.) {
      factor = (C_LIGHT+vFrame)/(C_LIGHT-vFrame);
      if (factor > 0.) 
        factor = sqrt(factor);
      else
	factor = 1.0;
    }
    else
      factor = 1.0;
    if ((printCount < 1) && doPrint)
      fprintf( stderr, "Transforming from frame %s to frame %s (factor %lf)\n",
	       idlSdfits->channels, idlSdfits->vel_def, factor);
  } /* end if frames are different */
  else
    factor = 1.0;

  /* scale frequencies */
  idlSdfits->sky_freq = factor * idlSdfits->sky_freq;
  idlSdfits->delta_x = factor * idlSdfits->delta_x;

  /* create a history entry from miscellaneous keywords having no place */
  sprintf( idlSdfits->history, "%s %s SAMPLER=%s SIDE=%s SIG=%s CAL=%s",
	   frontend, backend, sampler, sideband, sig, cal);
  printCount++;
  return(errMsg);
} /* end of readIdlFits() */
