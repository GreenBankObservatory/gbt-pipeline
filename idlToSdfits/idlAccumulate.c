/* File idlAccumulate.c, version 1.1, released  09/12/30 at 10:31:57 
   retrieved by SCCS 09/12/30 at 10:31:58     

%% patternStack() contains utilities for gathering spectra to write AIPS SDFITS
:: C program
 
HISTORY:
  091229 GIL initial version to accumulate values for specific locations
 
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
#define MAXIDLACCUM 200
#define MJD2000   51895                           /* approximate MJD of 2000 */
#define MILLISECOND  7.2722E-6                    /* milliscond in radians */

long nIdlAccum = 0;                               /* count spectra */
GBTIDL * idlAccums[MAXIDL];                       /* keep spectra */
GBTIDL * idlRefs[MAXIDL];                         /* keep spectra */
/* a critical part of the stack is keeping track of the integrations + scan */
/* numbers, so that all polarizations of a scan+int combination have the */
/* same scan ID number */
static lonGx accumNumbers[MAXIDL];
static long accumIds[MAXIDL];
static long accumMjds[MAXIDL];
static long accumBeams[MAXIDL];
static long accumStates[MAXIDL];
static double accumUtcs[MAXIDL];
static long debug = FALSE;

char * freeIdlAccum()
/* freeIdl() frees allocated memory for spectral temporary storage */
{ long i = 0;

  for (i = 0; i < nIdlAccum; i++) { 
    if (idlAccums[i])
      free( idlAccums[i]);
    idlAccums[i] = NULL;
  } 

  nIdlAccum = 0;
  return( NULL);
} /* end of freeIdl() */

char * initIdlAccum()
/* initIdl() frees allocated memory for spectral temporary storage, then */
/* initializes the pointers to NULL for re-allocation */
{ char * errMsg = NULL;
  long i = 0;

  errMsg = freeIdl() ;

  /* next assign all pointers to NULL until needed */
  for (i = 0; i < MAXIDL; i++) {        /* Mark all data as freed */
    idlAccums[i] = NULL;
    accumNumbers[i] = -1;                /* no valid integration yet */
    accumIds[i] = -1;                    /* no valid integration yet */
    accumMjds[i] = -1;                   /* no valid integration yet */
    accumUtcs[i] = -1;                   /* no valid integration yet */
    accumBeams[i] = -1;                  /* no valid integration yet */
    accumStates[i] = -1;                 /* no valid integration yet */
  }

  return( errMsg);
} /* end of initIdl() */

char * scanMjdUtcToIdAccum( long scan, long mjd, double utc, long * id)
/* scanMjdUtcToId() returns the ID number for this pair */
{ char * errMsg = NULL;
  long i = 0;

  * id = -1;

  for (i = 0; i < nIdlAccum; i++) {          /* For all scans in structure */
    if (accumNumbers[i] == scan) {       /* if scan found */
      if (mjd == accumMjds[i]) {
	if (fabs(utc-accumUtcs[i]) < MILLISECOND) {
	  *id = accumIds[i];
	  return(errMsg);
	} /* end if close in time */
      } /* end if close in date */
    } /* end if match scan number */
  } /* end for all scans in structure */

  return( "Scan, Integration Not Found"); 
} /* end of scanMjdUtcToId() */

char * idToScanMjdUtcAccum( long id, long * scan, long * mjd, double * utc)
/* idToScanIntegration() returns the ID number for this pair */
{ char * errMsg = NULL;

  if (id >= 0 && id < nIdlAccum) {
    *scan = accumNumbers[id];
    *mjd  = accumMjds[id];
    *utc  = accumUtcs[id];
  }
  else 
    errMsg = "Error finding scan, integration";

  return( errMsg); 
} /* end of idToScanMjdUtc() */

char * idToScanIntegrationAccum( long id, long * scan, long * integration)
/* idToScanIntegration() returns the ID number for this pair */
{ char * errMsg = NULL;

  if (id >= 0 && id < nIdlAccum) {
    *scan = accumNumbers[id];
    if (idlAccums[id] == NULL)
      errMsg = "Error, index to null record";
    else
      *integration = idlAccums[id]->iIntegration;
  }
  else 
    errMsg = "Error finding scan, integration";

  return( errMsg); 
} /* end of idToScanIntegration() */

char * getScanListAccum( long maxScans, long * nScans, long scanList[])
{ long i = 0, n = 0, j = 0, iScan = 0;
  
  *nScans = 0;
  if (nIdlAccum < 1)
    return("No scans in stucture");

  scanList[0] = idlAccums[0]->scan_num;
  n++;

  for (i = 1; i < nIdlAccum && n < maxScans; i++) {
    iScan = idlAccums[i]->scan_num;
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
} /* end of getScanListAccum() */

char * lineTrimAccum( long bChan, long eChan)
/* trim out channels, leave bChan:eChan */
{ long i = 0, j = 0, nOut = eChan - bChan + 1;
  
  if (nIdlAccum < 1)
    return("No scans in stucture");
  if (nOut < 1)
    return("No channels in output data stucture");
  if (bChan < 0)
    bChan = 0;
  /* for all spectra kept */
  for (i = 0; i < nIdlAccum; i++) {
    /* if end Channel past end of data points, keep up to end of data */
    if (idlAccums[i]->data_points < eChan) 
      eChan = idlAccums[i]->data_points - 1;
    nOut = eChan - bChan + 1;
    if (nOut < 1)
      continue;
    /* for each spectrum, transfer the data */
    for (j = 0; j < nOut; j++) 
      idlAccums[i]->data[j] = idlAccums[i]->data[j+bChan];
    idlAccums[i]->ref_ch = idlAccums[i]->ref_ch - bChan;
    idlAccums[i]->data_points = nOut;
  } /* end for all idl structures */

  return(NULL);
} /* end of lineTrimAccum() */

char * getScanBeamStateListAccum( long maxScans, long beam, long state, 
			     long * nScans, long scanList[])
/* return a list of all scans for specific beams and switch states */
{ long i = 0, n = 0, j = 0, iScan = 0;
  
  *nScans = 0;
  if (nIdlAccum < 1)
    return("No scans in stucture");

  for (i = 0; i < nIdlAccum && n < maxScans; i++) {
    if ((accumBeams[i] != beam) ||      /* if not matching state and beam */
	(accumStates[i] != state))
      continue;                        /* check next spectrum */
    iScan = idlAccums[i]->scan_num;
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
} /* end of getScanBeamStateListAccum() */

char * getBeamListAccum( long maxScans, long * nBeams, long beamList[])
/* return a list of all beams used in this data */
{ long i = 0, n = 0, j = 0;
  
  *nBeams = 0;
  if (nIdlAccum < 1)
    return("No scans in stucture");
  beamList[0] = accumBeams[i];
  n++;

  for (i = 1; i < nIdlAccum && n < maxScans; i++) {
    /* if a match to this beam already in the list, keep searching for new */
    for (j = 0; j < n; j++) {
      if (beamList[j] == accumBeams[i])
	break;
    }
    if (j >= n) {
      beamList[n] = accumBeams[i];
      n++;
    }
  } /* end for all idl structures */
  *nBeams = n;
  return(NULL);
} /* end of getBeamListAccum() */

char * getStateListAccum( long maxScans, long * nStates, long beamList[])
/* return a list of all beams used in this data */
{ long i = 0, n = 0, j = 0;
  
  *nStates = 0;
  if (nIdlAccum < 1)
    return("No scans in stucture");
  beamList[0] = accumStates[i];
  n++;

  for (i = 1; i < nIdlAccum && n < maxScans; i++) {
    /* if a match to this beam already in the list, keep searching for new */
    for (j = 0; j < n; j++) {
      if (beamList[j] == accumStates[i])
	break;
    }
    if (j >= n) {
      beamList[n] = accumStates[i];
      n++;
    }
  } /* end for all idl structures */
  *nStates = n;
  return(NULL);
} /* end of getStateListAccum() */

char * getIdlAccum( long scanNumber, long maxN, GBTIDL * outIdlAccums[], long * nOut)
{ long i = 0, n = 0, scan = 0, integration = 0, mjd = 0;
  double utc = 0;
  static long printCount = 0;

  *nOut = 0;                                /* assume no idl scans found */
  if (nIdlAccum < 1)
    return("No scans in stucture");

  if (scanNumber < 0)
    return("Invalid scan Number");

  /* for all idl structures, and less than max scans to return */
  for (i = 0; i < nIdlAccum && n < maxN; i++) {
    if (scanNumber == idlAccums[i]->scan_num) {
      outIdlAccums[n] = idlAccums[i];
      if (debug && printCount < 5) {
	integration = outIdlAccums[n]->iIntegration;
	idToScanMjdUtc( scanNumber, &scan, &mjd, &utc);
	fprintf (stderr, 
		 "getIdlAccum: Found scan %ld int %ld -> id %ld (%ld points)\n",
		 scan, integration, 
		 outIdlAccums[n]->scan_num, outIdlAccums[n]->data_points);
        printCount++;
      }
      n++;
    }
  } /* end for all idl structures */
  *nOut = n;
  return(NULL);
} /* end of getIdlAccum() */

char * putIdlAccum( GBTIDL * idl)
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* putIdlAccum() accumulates a spectrum to a idl of scan data.  Many scans   */
/* added to a single idl accumulation, depending on the proceedure size      */
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

  if (nIdlAccum >= MAXIDL)
    return("No More room for spectra");

  if (idl == NULL)
    return("Null Input IDL data pointer");

  if (idl->data_points < 1)
    return("No Data points");

  if (idl->data_points > MAXIDLPOINTS)
    return("Invalid number of data points");

  /* compute number of bytes to copy all data in structure */
  n = headerSize + (idl->data_points*nFloat);

  idlAccums[nIdlAccum] = (GBTIDL *)malloc( n);           /* alloate space for data */
 
  memcpy( idlAccums[nIdlAccum], idl, n);                 /* copy only valid data */

  /* now merge integration and sampler info */
  accumNumbers[nIdlAccum] = idlAccums[nIdlAccum]->scan_num;
  accumBeams[nIdlAccum]   = idlAccums[nIdlAccum]->iBeam;
  accumStates[nIdlAccum]  = idlAccums[nIdlAccum]->iState;
  dateObs2DMjd( idlAccums[nIdlAccum]->date, &dMjd);
  mjd = dMjd;
  utc = dMjd - mjd;
  utc = utc*TWOPI;

  accumMjds[nIdlAccum] = mjd;
  accumUtcs[nIdlAccum] = utc;
  errMsg = scanMjdUtcToId( accumNumbers[nIdlAccum], accumMjds[nIdlAccum], 
			   accumUtcs[nIdlAccum], &id);
  if (errMsg) {                                /* if a new scan */
    id = nIdlAccum;
  }
  accumIds[nIdlAccum] = id;                          /* record new id */
  /* use ID as number for index */
  idlAccums[nIdlAccum]->scan_num = accumIds[nIdlAccum];   

  if (printCount < 5 && debug) {
    fprintf( stderr, "putIdlAccum: scan %ld, with %ld points (dX = %g Hz)\n",
	   idlAccums[nIdlAccum]->scan_num, idlAccums[nIdlAccum]->data_points, idlAccums[nIdlAccum]->delta_x);
    fprintf( stderr, "putIdlAccum: scan %ld, integration %ld -> id %ld\n",
	   accumNumbers[nIdlAccum], idlAccums[nIdlAccum]->iIntegration, accumIds[nIdlAccum]);
    printCount++;
  }

  nIdlAccum++;                                      /* count number o records */

  return(NULL);
} /* end of putIdlAccum */
