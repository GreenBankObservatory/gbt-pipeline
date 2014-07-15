/* File idlStack.c, version 1.7, released  09/12/15 at 07:59:45 
   retrieved by SCCS 11/10/26 at 13:11:20     

%% patternStack() contains utilities for gathering spectra to write AIPS SDFITS
:: C program
 
HISTORY:
  111026 GIL add more digits to the scan id time
  091211 GIL add lineTrim() to select channels bChan:eChan
  080314 GIL also track by date and time
  051020 GIL create a separate array to track integrations
  050908 GIL increase the stack size
  041227 GIL diagnose problems
  041221 GIL only use idl spectra structures for the data stack
  041220 GIL initial version
 
DESCRIPTION:
Functions to store GBT IDL spectra to a idl structure.
These functions are used to gather up calibrated spectra
for output in a single AIPS SDFITS file.

OMISSIONS:
NO T Cal support
*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "math.h"
#include "fitsio.h"
#include "MATHCNST.H"
#include "STDDEFS.H"
#include "gbtIdl.h"

/* externals */
extern char * dateObs2DMjd( char * dateObs, double * dMjd);
/* internals */
#define MAXIDL 200000
#define MJD2000   51895                           /* approximate MJD of 2000 */
#define MILLISECOND  7.2722E-9    /* 0.1 milliscond in radians */

long nIdl = 0;                                    /* count spectra */
GBTIDL * idls[MAXIDL];                            /* keep spectra */
/* a critical part of the stack is keeping track of the integrations + scan */
/* numbers, so that all polarizations of a scan+int combination have the */
/* same scan ID number */
static long scanNumbers[MAXIDL];
static long scanIds[MAXIDL];
static long scanMjds[MAXIDL];
static long scanBeams[MAXIDL];
static long scanStates[MAXIDL];
static double scanUtcs[MAXIDL];
static long debug = FALSE;

char * freeIdl()
/* freeIdl() frees allocated memory for spectral temporary storage */
{ long i = 0;

  for (i = 0; i < nIdl; i++) { 
    if (idls[i])
      free( idls[i]);
    idls[i] = NULL;
  } 

  nIdl = 0;
  return( NULL);
} /* end of freeIdl() */

char * initIdl()
/* initIdl() frees allocated memory for spectral temporary storage, then */
/* initializes the pointers to NULL for re-allocation */
{ char * errMsg = NULL;
  long i = 0;

  errMsg = freeIdl() ;

  /* next assign all pointers to NULL until needed */
  for (i = 0; i < MAXIDL; i++) {        /* Mark all data as freed */
    idls[i] = NULL;
    scanNumbers[i] = -1;                /* no valid integration yet */
    scanIds[i] = -1;                    /* no valid integration yet */
    scanMjds[i] = -1;                   /* no valid integration yet */
    scanUtcs[i] = -1;                   /* no valid integration yet */
    scanBeams[i] = -1;                  /* no valid integration yet */
    scanStates[i] = -1;                 /* no valid integration yet */
  }

  return( errMsg);
} /* end of initIdl() */

char * scanMjdUtcToId( long scan, long mjd, double utc, long * id)
/* scanMjdUtcToId() returns the ID number for this pair */
{ char * errMsg = NULL;
  long i = 0;

  * id = -1;

  for (i = 0; i < nIdl; i++) {          /* For all scans in structure */
    if (scanNumbers[i] == scan) {       /* if scan found */
      if (mjd == scanMjds[i]) {
	if (fabs(utc-scanUtcs[i]) < MILLISECOND) {
	  *id = scanIds[i];
	  return(errMsg);
	} /* end if close in time */
      } /* end if close in date */
    } /* end if match scan number */
  } /* end for all scans in structure */

  return( "Scan, Integration Not Found"); 
} /* end of scanMjdUtcToId() */

char * idToScanMjdUtc( long id, long * scan, long * mjd, double * utc)
/* idToScanIntegration() returns the ID number for this pair */
{ char * errMsg = NULL;

  if (id >= 0 && id < nIdl) {
    *scan = scanNumbers[id];
    *mjd  = scanMjds[id];
    *utc  = scanUtcs[id];
  }
  else 
    errMsg = "Error finding scan, integration";

  return( errMsg); 
} /* end of idToScanMjdUtc() */

char * idToScanIntegration( long id, long * scan, long * integration)
/* idToScanIntegration() returns the ID number for this pair */
{ char * errMsg = NULL;

  if (id >= 0 && id < nIdl) {
    *scan = scanNumbers[id];
    if (idls[id] == NULL)
      errMsg = "Error, index to null record";
    else
      *integration = idls[id]->iIntegration;
  }
  else 
    errMsg = "Error finding scan, integration";

  return( errMsg); 
} /* end of idToScanIntegration() */

char * getScanList( long maxScans, long * nScans, long scanList[])
{ long i = 0, n = 0, j = 0, iScan = 0;
  
  *nScans = 0;
  if (nIdl < 1)
    return("No scans in stucture");

  scanList[0] = idls[0]->scan_num;
  n++;

  for (i = 1; i < nIdl && n < maxScans; i++) {
    iScan = idls[i]->scan_num;
    for (j = 0; j < n; j++) {
      if (scanList[j] == iScan)
	break;
    }
    if (j >= n) {
      scanList[n] = iScan;
      n++;
    }
  } /* end for all idl structures */
  *nScans = n;
  return(NULL);
} /* end of getScanList() */

char * lineTrim( long bChan, long eChan)
/* trim out channels, leave bChan:eChan */
{ long i = 0, j = 0, nOut = eChan - bChan + 1;
  
  if (nIdl < 1)
    return("No scans in stucture");
  if (nOut < 1)
    return("No channels in output data stucture");
  if (bChan < 0)
    bChan = 0;
  /* for all spectra kept */
  for (i = 0; i < nIdl; i++) {
    /* if end Channel past end of data points, keep up to end of data */
    if (idls[i]->data_points < eChan) 
      eChan = idls[i]->data_points - 1;
    nOut = eChan - bChan + 1;
    if (nOut < 1)
      continue;
    /* for each spectrum, transfer the data */
    for (j = 0; j < nOut; j++) 
      idls[i]->data[j] = idls[i]->data[j+bChan];
    idls[i]->ref_ch = idls[i]->ref_ch - bChan;
    idls[i]->data_points = nOut;
  } /* end for all idl structures */

  return(NULL);
} /* end of lineTrim() */

char * getScanBeamStateList( long maxScans, long beam, long state, 
			     long * nScans, long scanList[])
/* return a list of all scans for specific beams and switch states */
{ long i = 0, n = 0, j = 0, iScan = 0;
  
  *nScans = 0;
  if (nIdl < 1)
    return("No scans in stucture");

  for (i = 0; i < nIdl && n < maxScans; i++) {
    if ((scanBeams[i] != beam) ||      /* if not matching state and beam */
	(scanStates[i] != state))
      continue;                        /* check next spectrum */
    iScan = idls[i]->scan_num;
    for (j = 0; j < n; j++) {
      if (scanList[j] == iScan)
	break;
    }
    if (j >= n) {
      scanList[n] = iScan;
      n++;
    }
  } /* end for all idl structures */
  *nScans = n;
  return(NULL);
} /* end of getScanBeamStateList() */

char * getBeamList( long maxScans, long * nBeams, long beamList[])
/* return a list of all beams used in this data */
{ long i = 0, n = 0, j = 0;
  
  *nBeams = 0;
  if (nIdl < 1)
    return("No scans in stucture");
  beamList[0] = scanBeams[i];
  n++;

  for (i = 1; i < nIdl && n < maxScans; i++) {
    /* if a match to this beam already in the list, keep searching for new */
    for (j = 0; j < n; j++) {
      if (beamList[j] == scanBeams[i])
	break;
    }
    if (j >= n) {
      beamList[n] = scanBeams[i];
      n++;
    }
  } /* end for all idl structures */
  *nBeams = n;
  return(NULL);
} /* end of getBeamList() */

char * getStateList( long maxScans, long * nStates, long beamList[])
/* return a list of all beams used in this data */
{ long i = 0, n = 0, j = 0;
  
  *nStates = 0;
  if (nIdl < 1)
    return("No scans in stucture");
  beamList[0] = scanStates[i];
  n++;

  for (i = 1; i < nIdl && n < maxScans; i++) {
    /* if a match to this beam already in the list, keep searching for new */
    for (j = 0; j < n; j++) {
      if (beamList[j] == scanStates[i])
	break;
    }
    if (j >= n) {
      beamList[n] = scanStates[i];
      n++;
    }
  } /* end for all idl structures */
  *nStates = n;
  return(NULL);
} /* end of getStateList() */

char * getIdl( long scanNumber, long maxN, GBTIDL * outIdls[], long * nOut)
{ long i = 0, n = 0, scan = 0, integration = 0, mjd = 0;
  double utc = 0;
  static long printCount = 0;

  *nOut = 0;                                /* assume no idl scans found */
  if (nIdl < 1)
    return("No scans in stucture");

  if (scanNumber < 0)
    return("Invalid scan Number");

  /* for all idl structures, and less than max scans to return */
  for (i = 0; i < nIdl && n < maxN; i++) {
    if (scanNumber == idls[i]->scan_num) {
      outIdls[n] = idls[i];
      if (debug && printCount < 5) {
	integration = outIdls[n]->iIntegration;
	idToScanMjdUtc( scanNumber, &scan, &mjd, &utc);
	fprintf (stderr, 
		 "getIdl: Found scan %ld int %ld -> id %ld (%ld points)\n",
		 scan, integration, 
		 outIdls[n]->scan_num, outIdls[n]->data_points);
        printCount++;
      }
      n++;
    }
  } /* end for all idl structures */
  *nOut = n;
  return(NULL);
} /* end of getIdl() */

char * putIdl( GBTIDL * idl)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* putIdl() adds a spectrum to a idl of scan data.  Many scans can be*/
/* added to a single idl, depending on the proceedure size               */
/* the current nDcr points are added to the end of the previous patter       */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ char * errMsg = NULL;
  long nFloat = sizeof(float), idlSize = sizeof( GBTIDL), headerSize = 0, 
    n = 0, id = 0, mjd = 0;
  double dMjd = 0, utc = 0;
  static long printCount = 0;

  headerSize = idlSize - (nFloat * MAXIDLPOINTS);

  if (debug && printCount < 5)
    fprintf( stderr, "IdlSize=%ld, headerSize= %ld, nFloat = %ld\n", 
	  idlSize, headerSize, nFloat);

  if (nIdl >= MAXIDL)
    return("No More room for spectra");

  if (idl == NULL)
    return("Null Input IDL data pointer");

  if (idl->data_points < 1)
    return("No Data points");

  if (idl->data_points > MAXIDLPOINTS)
    return("Invalid number of data points");

  /* compute number of bytes to copy all data in structure */
  n = headerSize + (idl->data_points*nFloat);

  idls[nIdl] = (GBTIDL *)malloc( n);           /* alloate space for data */
 
  memcpy( idls[nIdl], idl, n);                 /* copy only valid data */

  /* now merge integration and sampler info */
  scanNumbers[nIdl] = idls[nIdl]->scan_num;
  scanBeams[nIdl]   = idls[nIdl]->iBeam;
  scanStates[nIdl]  = idls[nIdl]->iState;
  dateObs2DMjd( idls[nIdl]->date, &dMjd);
  mjd = dMjd;
  utc = dMjd - mjd;
  utc = utc*TWOPI;

  scanMjds[nIdl] = mjd;
  scanUtcs[nIdl] = utc;
  errMsg = scanMjdUtcToId( scanNumbers[nIdl], scanMjds[nIdl], scanUtcs[nIdl],
			   &id);
  if (errMsg) {                                /* if a new scan */
    id = nIdl;
  }
  scanIds[nIdl] = id;                          /* record new id */
  idls[nIdl]->scan_num = scanIds[nIdl];        /* use ID as number for index */

  if (printCount < 5 && debug) {
    fprintf( stderr, "putIdl: scan %ld, with %ld points (dX = %g Hz)\n",
	   idls[nIdl]->scan_num, idls[nIdl]->data_points, idls[nIdl]->delta_x);
    fprintf( stderr, "putIdl: scan %ld, integration %ld -> id %ld\n",
	   scanNumbers[nIdl], idls[nIdl]->iIntegration, scanIds[nIdl]);
    printCount++;
  }

  nIdl++;                                      /* count number o records */

  return(NULL);
} /* end of putIdl */
