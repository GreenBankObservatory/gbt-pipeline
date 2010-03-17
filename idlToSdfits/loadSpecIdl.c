/* File loadSpecIdl.c, version 1.4, released  04/04/14 at 14:59:48 
   retrieved by SCCS 07/07/06 at 09:48:58     

%% program to load fits data for plotting
:: spectral processor test program

HISTORY
040414 GIL move global idlArrays to fillSpecIdl.c
040413 GIL increase temporary array sizes
040412 GIL intial version 

DESCRIPTION:
loadSpecIdl() function define externals for calls to calSpectrometer()
*/
#include "stdio.h"
#include "stdlib.h"
#include "string.h"
#include "MATHCNST.H"
#include "STDDEFS.H"
#include "export.h"
#include "transform.h"
#include "gbtIf.h"
#include "gbtLo.h"
#include "gbtSpectrometer.h"
#include "gbtGo.h"
#include "gbtScanInfo.h"

/* externals */
extern char * calSpectrometer( char * fileName, long iState, long * nStates, 
			long iSampler, long * nSamplers, 
			long doTrans, long maxData, 
			long * spectraLength, double specArray[], 
			long iIntegration, long * nIntegrations,
			long * mjd, double * utc, double  * az, double * el, 
			struct SPECTROMETER * spectrometer,
			struct SPECPORT * port,
			       double * refFrequency, double * bandWidth);
extern char * nextStateSamplerIntegration( long * iState, long nStates,
				    long * iSampler, long nSamplers,
					   long * iIntegration, long nIntegrations);
extern char * findGbtFiles ( char * obsFileName, char * goName, 
			     char * antennaName, 
		      char * rcvrName, char * loName, char * ifName, 
		      char * spectrometerName, char * spName,
		      char * dcrName, char * bcpmName, char * holographyName);
extern char * getLo( char * loName, double dMjd, struct LO * lo, 
		     double * loFreq);
extern char * stripExtension( char * fullFileName);
extern char * getBackendIf( char * ifName, long printMessages, 
			    struct SCANINFO * scanInfo,
			    char * backend, char * bank, 
			    long channel, struct IF * ifPoint);
extern char * saveTCal( char * tCalName, double frequency, long feedIndex, 
		 char * polarization, char * feed, 
		 double * loTCalTemp, double * hiTCalTemp);

/* globals */

/* internals */
static struct LO lo;
static struct SCANINFO ifScanInfo;

int s_stop() {                  /* f2c function() not used */
  return 0;
}
int s_wsle() {
  return 0;
}
int s_wsfe() {
  return 0;
}
int e_wsle() {
  return 0;
}
int e_wsfe() {
  return 0;
}
int do_lio() {
  return 0;
}

/* determine FT processing from globals */
long doVanVleck = 1, doHanning = 1;
long calOnFirst = 0;             /* if 0, cal On spectra are first */

#define MAXNAMELENGTH  256
#define EPSILON .001

extern struct SPECTROMETER idlSpectrometer;
extern struct SPECPORT idlPort;
/* spectrometer data are read into a temporary array */
extern double idlSpecArray[];
extern long idlSpecLength, idlSpecMax;   

char * specIdl( char * fileName, long maxData, long * n, 
		    float xs[], float ys[])
{ static char * errMsg = NULL, 
    goName[MAXNAMELENGTH] = "", antennaName[MAXNAMELENGTH] = "", 
    rcvrName[MAXNAMELENGTH] = "", loName[MAXNAMELENGTH] = "", 
    spectrometerName[MAXNAMELENGTH] = "", tempFileName[MAXNAMELENGTH] = "",
    spName[MAXNAMELENGTH] = "", dcrName[MAXNAMELENGTH] = "", 
    bcpmName[MAXNAMELENGTH] = "", holographyName[MAXNAMELENGTH] = "";
  static long iState = 0, nStates = 0, iSampler = 0, nSamplers = 0, 
    doTrans = TRUE, iIntegration = 0, nIntegrations = 0, mjd = 0;
  double utc = 0, az = 0, el = 0, refFrequency = 0,
    bandWidth = 0, dNu = 0, nu = 0;
  static long iPort = 0, i = 0, feedSRIndex = 1, refChan = 0, j = 0,
    nSkip = 0,initLo = FALSE;
  static double loTCalTemp = 1, hiTCalTemp = 1, skyFreq = 0, ifCenter = 0;
  static char lastFileName[MAXNAMELENGTH] = "", 
        ifName[MAXNAMELENGTH] = "", bank[10] = "A";
  static double loFreq = 0, lastSkyFreq = 0;
  struct IF ifPoint;
  
  /* if a new file */
  if (strcmp( lastFileName, fileName)) {
    /* find all the files associated with the obervations */
    errMsg = findGbtFiles ( fileName, goName, antennaName, 
		      rcvrName, loName, ifName, 
		      spectrometerName, spName,
		      dcrName, bcpmName, holographyName);
    if (errMsg) 
      fprintf( stderr,"Error reading GBT Files: %s\n", errMsg);

    nStates = 0;                    /* number of states unknown */
    strcpy( lastFileName, fileName);
    if (!initLo) {                  /* on first use, must init pointers */
      lo.states = NULL;
      lo.freqs  = NULL;
      lo.sources = NULL;
      initLo = TRUE;                /* note no need to re-init */
    } /* end if for first init */

    /* read lo value for this integration */
    errMsg = getLo( loName, 0., &lo, &loFreq);
    if (errMsg) 
      fprintf( stderr,"Error reading Lo  File: %s\n", errMsg);

    /* if test tone data in this LO file, must find other file */
    if (lo.testTone) {                /* must find other lo file */
      fprintf( stderr, "looking for LO1B file: %s\n", loName);
      if (strstr( loName, "LO1A")) {   /* find LO1A in loName */
	*(strstr( loName, "LO1A")+3) = 'B';  /* A->B */
	fprintf( stderr, "looking for LO1B file: %s\n", loName);
	errMsg = getLo( loName, 0., &lo, &loFreq);
      }
    } /* end if must look for other LO file */
    errMsg = NULL;

    /* determine bank name from file name */
    strcpy( tempFileName, fileName);
    stripExtension( tempFileName);
    /* last character of file before extension is the bank name */
    strcpy( bank, &tempFileName[strlen(tempFileName)-1]);
  } /* end if a new file */

  errMsg = calSpectrometer( fileName, iState, &nStates, 
			iSampler, &nSamplers, 
			doTrans, idlSpecMax, 
			&idlSpecLength, idlSpecArray,
			iIntegration, &nIntegrations,
			&mjd, &utc, &az, &el, &idlSpectrometer,
			&idlPort,
			    &refFrequency, &bandWidth);
  fprintf( stderr, "specIdl: state=%ld/%ld sampler=%ld/%ld int=%ld/%ld n=%ld\n",
	  iState, nStates, iSampler, nSamplers, 
	  iIntegration, nIntegrations,	idlSpecLength);

  if (errMsg) {
    fprintf( stderr, "loadSpec: Error: %s\n", errMsg);
    fprintf( stderr, "loadSpec: File : %s\n", fileName);
  }

  if (bandWidth == 0)                  /* if bandwidth not read, use default*/
    bandWidth = 50.E6;

  if (iSampler < idlPort.nPorts) {  /* find index into IF manager file */
    iPort = idlPort.ports[iSampler].port;
    ifCenter = idlPort.ports[iSampler].freqStart;
  }
  else {
    ifCenter = bandWidth;
    fprintf( stderr, "No port for sampler %ld\n", iSampler);
  }

  if ((bandWidth > 12.5E6 - EPSILON) &&          /* if 12.5 MHz band */
      (bandWidth < 12.5E6 + EPSILON)) {
    ifCenter = 31.25E6;
  }
  else if ((bandWidth > 50.E6 - EPSILON) &&      /* if lower side band */
	   (bandWidth < 50.E6 + EPSILON)) {
    ifCenter = 75.0E6;
    bandWidth = -50E6;
  }
  else if ((bandWidth > 200.E6 - EPSILON) &&     /* if lower side band */
	   (bandWidth < 200.E6 + EPSILON)) {
    ifCenter =  900.0E6;
    bandWidth = -200E6;
  }
  else                                            /* else 800 Mhz */
    ifCenter = 1200.0E6;
 
  if (iPort <= 0) {                     /* if port not found */
    /* IF samplers are 1 to 8 for high speed and 9 to ? for low */
    if (bandWidth < 1.E8 && bandWidth > -1.E8) {
      iPort = iSampler + 9;
      /* if second set of spectrometer imputs 1 => 9, 2 => 13 */
      if (nSamplers < 8 && iSampler >= nSamplers/2) 
	iPort += (4 - (nSamplers/2));
    }
    else
      iPort = iSampler + 1;
  }

  refChan = idlSpecLength / 2;

  /* default case is frequency is IF center frequency */
  if (bandWidth > 0.)
    skyFreq = bandWidth/2.;
  else
    skyFreq = -1.*(bandWidth/2.);

  /* now that the port is known, find IF parameters */
  if (strlen( ifName) > 1) {
    errMsg = getBackendIf( ifName, FALSE, &ifScanInfo, 
			   "Spectrometer", bank, iPort, &ifPoint);

    if (errMsg == NULL) {                    /* if no error finding IF */
      /*      skyFreq -= ifCenter; */
      skyFreq = (ifPoint.sFSideband * ifCenter);
      skyFreq += (loFreq * ifPoint.sFMultiplier) + ifPoint.sFOffset;

      if (skyFreq <= 0.)
        skyFreq = ifPoint.skyCenterFreq;

      refFrequency = skyFreq;

      if (skyFreq != lastSkyFreq) {     
        fprintf( stderr, "loFreq = %9.0f, lo.if = %9.0f, if.ifCent = %9.0f\n",
 	       loFreq, lo.ifFreq, ifPoint.ifCenterFreq);
        fprintf( stderr, "sFOffset = %9.0f, ifCenter = %9.0f ifPort = %ld\n", 
	       ifPoint.sFOffset, ifCenter, iPort);
	fprintf( stderr, "Port %ld, Bandwidth := %f\n", iPort, bandWidth);
	lastSkyFreq = skyFreq;
      }

      /*      feedSRIndex = rcvrFeedIndex( ifPoint, iState, nStates); */
      feedSRIndex = ifPoint.srFeed1;

      /* get tcal for this frequency */
      errMsg = saveTCal( rcvrName, skyFreq, 
			 feedSRIndex, ifPoint.polarize, ifPoint.feed, 
			 &loTCalTemp, &hiTCalTemp);
      if ((skyFreq - EPSILON > refFrequency) ||
	  (skyFreq + EPSILON < refFrequency))
	fprintf( stderr, "Cal Values for %12.1f Hz, Center Freq %12.1f Hz\n",
		 skyFreq, refFrequency);
	   
    } /* end if a matching backend input number */
    else {
      bandWidth = -50.E6;               /* set default bandwidth */
      fprintf ( stderr, "Error getting IF info: %s\n", errMsg);
      errMsg = NULL;
    } /* end if error reading if info */
  } /* end if a ifFile() */

  /* now that bandwidth and frequencies are set, calc x axis */
  if (idlSpecLength <= 0) 
    dNu = EPSILON;
  else 
    dNu = bandWidth/(double)idlSpecLength;

  fprintf ( stderr, "specData: dNu=%lf, skyFreq=%lf at %ld\n", 
	    dNu, skyFreq, refChan);
  nu = skyFreq - ((double)refChan*dNu);

  nSkip = 1;                               /* if too many points, skip some */
  while (maxData*nSkip < idlSpecLength) 
    nSkip = 2*nSkip;

  j = 0;
  for (i = 0; i < idlSpecLength; i = i + nSkip) {
    xs[j] = nSkip*nu*1.E-9;
    nu = nu + dNu;
    ys[j] = idlSpecArray[i];
    j++;
  } /* end for all output data */
  *n = j;                              /* data out is total count */

  errMsg = nextStateSamplerIntegration( &iState, nStates,
				        &iSampler, nSamplers,
					&iIntegration, nIntegrations);

  return (errMsg);
} /* end of loadSpecIdl() */

/* function call compatible with the IDL call_external function */
/* Arguments to function must be changed in conjuction with the IDL */
/* procedure calling it */

void loadSpecIdl(int argc, void *argv[])
{ char fileName[512] = "";
  IDL_STRING * gbtSpecFileName;
  float *xs, *yOn1s, *yOff1s, *yOn2s, *yOff2s;
  long *n, *nMax;

  if (argc < 1) {
    printf( "specDataIdl: Insufficient arguments\n");
    printf( "specDataIdl: usage:\n");
    printf( "             call_external( 'specDataIdl', fileName, nMax, ");
    printf( "n, xs, yOn1s, yOff1s, yOn2s, yOff2s)\n");
    printf( "where nMax  : maxixmum number of array values to return\n");
    printf( "where n     : number of array values returned\n");
    printf( "where xs    : frequency array of values returned\n");
    printf( "where yOn1s : first Pol, cal On values\n");
    printf( "where yOff1s: first Pol, cal Off values\n");
    printf( "where yOn2s : second Pol, cal On values\n");
    printf( "where yOff2s: second Pol, cal Off values\n");
    return;
  } /* end if not enough arguments */

  gbtSpecFileName = (IDL_STRING *)argv[0]; /* Array pointer */
  strncpy( fileName, gbtSpecFileName->s, gbtSpecFileName->slen);
  fileName[gbtSpecFileName->slen] = '\0';
  nMax  = (long *) argv[1]; /* long pointer */  

  printf( "In specDataIdl: %d: %s %lx\n", argc, fileName, *nMax);

  n     = (long *) argv[2]; /* long pointer */
  xs    = (float *) argv[3]; /* Array pointer */
  yOn1s = (float *) argv[4]; /* Array pointer */
  yOff1s= (float *) argv[5]; /* Array pointer */
  yOn2s = (float *) argv[6]; /* Array pointer */
  yOff2s= (float *) argv[7]; /* Array pointer */

  specIdl( fileName, *nMax, n, xs, yOn1s);
  specIdl( fileName, *nMax, n, xs, yOff1s);
  specIdl( fileName, *nMax, n, xs, yOn2s);
  specIdl( fileName, *nMax, n, xs, yOff2s);

  return;
} /* end of specDataIdl() */
