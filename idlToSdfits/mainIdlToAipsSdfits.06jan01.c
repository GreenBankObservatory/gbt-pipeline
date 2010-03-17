/* File %M%, version %R%.%L%, released  %E% at %U% 
   retrieved by SCCS %D% at %T%     

%% write an AIPS single dish fits file from an idl sdfits structure
:: TEST C program
 
HISTORY:
  051206 GIL add -C option for channels
  050906 GIL add -T option for channel 1 = tSYS
  050902 GIL fix assignment of coordinates of GALACTIC case
  050901 GIL clean up the last few keywords
  050831 GIL potentially write galactic coordinates
  050829 GIL allow setting the output file name.
  050815 GIL first version to pass file name to readIdlFits.c
  050716 GIL clean up un-used variables
  050715 GIL initial version based on writeSdfits
  ...
  021211 GIL inital version based on gbtObsSummary.c
 
DESCRIPTION:
Write an AIPS single dish fits file from a GBT observation and a
set of spectra in a IDL SDFITS file
*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "math.h"
#include "dirent.h"
#include "fitsio.h"
#include "MATHCNST.H"
#include "STDDEFS.H"
#include "gbtIdl.h"
#include "gbtGo.h"
#include "gbtAntenna.h"

#define MAXSCANS      300000
#define J2000    0
#define B1950    1
#define AZEL     2
#define GALACTIC 3
#define MAXIDLSTRING 1024
#define SOFTVERSION "5.1"

/* externals */
extern long gbtGoInit;
extern struct GOPARAMETERS go;

char * quickPlot( char * plotName, long gv, 
		  char * gnuCmds, char * title, 
		  char * xLabel,  char * yLabel, 
		  long n,  double * xs, 
		  double * y1s, char * y1Label,
		  double * y2s, char * y2Label,
                  double * y3s, char * y3Label,
		  double * y4s, char * y4Label);
extern char * addSlash( char *);
extern char * stripWhite( char *);
extern char * medianBaseline( float *, long , long );
extern char * aveRmsRange( float data[], long aStart, long aEnd, 
       long bStart, long bEnd, double * aveOut, double * rmsOut);
extern char * cvrtuc( char *);
extern char * rad2str( double, char *, char *);
extern long today2mjd();
extern char * freeIdl();
extern char * mjd2str( long, char *);
extern char * getScanList( long maxScans, long * nScans, long scanList[]);
extern char * putIdl( GBTIDL * idl);
extern char * writeSdfits( char * fitsName, long nScans, long scanList[],
		    long coordType, long nIf, long nChan);
extern char * setFullPath( char * pathName, char * fileName);
extern char * gbtInit( struct GOPARAMETERS * pGo, struct GBTPOSITION * pGbtPos,
		       long *pGoInit);
extern double medianRms(long n, float a[]);
char * medianAveRmsMinMax( long n, double a[], 
			   double * oMedian, double * oAve, double * oRms, 
			   double * oMin, double * oMax);
extern char *makeIntList( long maxInt, long list[], long * nInList, char *);
char * medianPeak( long n, long lineWidth, double maxValue, float fluxes[]);
char * calcTSys( long n, double aveArray[], double diffArray[], double * tSys);

extern void medianFilter ( int count, int medWid2, double inarr[], 
			   double outarr[]);
extern char * readIdlFits ( char * fileName, long iRow, long * nRows, 
		     long doPrint, GBTIDL * idlSdfits);
extern char * dateObs2DMjd( char * dateObs, double * dMjd);
extern char * openOutRevision(char * outName, FILE ** pFileName);
extern char * stripExtension( char * fullFileName);

/* internals */
#define MAXNAMES 500
#define FFTSMOOTHWIDTH 256
long nSpectra = 0;
struct GOPARAMETERS go;
struct GBTPOSITION gbtPos;

double tauFactor( double el, double tau)
/* tauFactor() returns the correction factor for the atmospheric attenuation */
/* Uses the atmospheric thickness model as a function of zenith angle z, from*/
/* "Tools of Radio Astronomy", K. Rohlfs, T.L. Wilson, pg 189.               */
/* INPUTS: el     Elevation (Radians)                                        */
/*         tau    attenuation at zenith Nepers (range is usually 0.007 to .2)*/
/* OUTPUT: factor correction factor at elevation                             */
{ double secZ = 1., x = 0, factor = 1.;

  if (el < DEGREE)
    return(1.);

  secZ = 1./sin(el);
  x = -0.0045 + (1.00672 * secZ) - (0.002234*secZ*secZ) - 
    (0.0006247*secZ*secZ*secZ);      /* from Tools of Radio Astronomy */

  factor = exp( +tau * x);           /* compute scale factor = 1/attenuation*/

  return(factor);
} /* end of tauFactor() */

double tAtmosphere( double el, double tau, double tAtm)
/* tAtmosphere() returns the atmospheric contribution to the system temp.    */
/* INPUTS: el     Elevation (Radians)                                        */
/*         tau    attenuation at zenith Nepers (range is usually 0.007 to .2)*/
/*         tAtm   integrated atmospheric temperature (range is 260 to 280 K) */
/* OUTPUT: tAtmEl atmospheric temperature contribution at elevation          */
{ double tAtmEl = 0., secZ = 1., x = 0, factor = 1.;

  if (el < DEGREE)
    return(1.);

  secZ = 1./sin(el);
  x = -0.0045 + (1.00672 * secZ) - (0.002234*secZ*secZ) - 
    (0.0006247*secZ*secZ*secZ);      /* from Tools of Radio Astronomy */

  factor = exp( -tau * x);           /* compute scale factor */

  tAtmEl = tAtm*( 1. - factor);

  return(tAtmEl);
} /* end of tAtmosphere() */

char * idlToSdfitsHelp() 
/* idlToSdfitsHelp() is explains how to use idlToSdfits() */
{ 
  fprintf( stderr, "idlToSdfits: Take a GBTIDL Keep file and\n");
  fprintf( stderr, 
	   "convert it to an AIPS-compatible Single Dish Fits File\n");
  fprintf( stderr, 
	   "idlToSdfits: usage\n");
  fprintf( stderr, 
	   "idlToSdfits [-t] [-c <start>:<stop>] [-o <outName>] <idlFitsFileName>\n");
  fprintf( stderr, 
	   "where [-t]               optionally replace channel 1 with Tsys\n");
  fprintf( stderr, 
	   "                         (in order to produce a continuum image)\n");
  fprintf( stderr, 
	   "where [-c <start>:<stop>] optionally select channels for output\n");
  fprintf( stderr, 
	   "                         channel number range from 1 to N\n");
  fprintf( stderr, 
	   "where [-o <outName>]     optionally specify output file name\n");
  fprintf( stderr, 
	   "where <idlFitsFileName>  input name of IDL keep file to convert\n");
  fprintf( stderr, 
	   "example: idlToSdfits -t -c 10:20 -o output.fits input.fits\n");
  fprintf( stderr, 
	   "------------ Glen Langston == glangsto@nrao.edu\n");
  fprintf( stderr, 
	   "------------ December 07, 2005 \n");
  return(NULL);
} /* end of idlToSdfitsHelp() */

char * openTex( char * fileName, GBTIDL * gbtIdl, FILE ** pFile)
/* texOpen() opens a tex output file and writes the source summary          */
{ char todayStr[32] = "";
  long mjd =  today2mjd();
  double dNu = 1, dV = 0, vMin = 0, vMax = 0;

  remove(fileName);

  if ((*pFile = fopen( fileName, "w")) == NULL) {
    fprintf( stderr, "ERROR opening TeX summary file: %s\n", fileName);
    return( "ERROR opening TeX file");
  }
  mjd2str( mjd, todayStr);

  fprintf( *pFile, 
	   "The GBT observations by %s of source %s\n",
	   go.observer, gbtIdl->source);
  fprintf( *pFile, 
	   "were processed on %s using 'idlToSdfits' version %s.\n", 
	   todayStr, SOFTVERSION);
  fprintf( *pFile, "\nGBT Project %s was processed for imaging by AIPS.\n", 
	   go.projectId);

  if (strstr( gbtIdl->pol_id, "X") || strstr( gbtIdl->pol_id, "Y"))
    fprintf( *pFile, "The region was observed in Linear Polarization.\n");
  else
    fprintf( *pFile, "The region was observed in Circular Polarization.\n");

  fprintf( *pFile, "\nCenter frequency was %lf MHz ", 
	   gbtIdl->sky_freq * 1.E-6);
  fprintf( *pFile, "and the bandwidth was %lf MHz.\n", gbtIdl->bw * 1.E-6);
  fprintf( *pFile, "The spectrum had %ld spectral channels, ",
	   gbtIdl->data_points);
  dNu = gbtIdl->delta_x;
  if (dNu < 0)
    dNu = -dNu;
  dV = dNu*C_LIGHT/gbtIdl->sky_freq;
  fprintf( *pFile, "with %.0lf Hz channel width.\n", dNu);
  fprintf( *pFile, "The Doppler tracking First LO reference frame was '%s',\n",
	   gbtIdl->vel_def);
  fprintf( *pFile, "and the velocity resolution was %.3lf km/sec.\n",
	   dV*1.E-3);
  if (gbtIdl->rest_freq > 0.) {    /* if have a line freq to calc velocity */
    vMin = gbtIdl->sky_freq - ((1. - gbtIdl->ref_ch)*gbtIdl->delta_x);
    vMax = gbtIdl->sky_freq - 
      ((gbtIdl->data_points - gbtIdl->ref_ch)*gbtIdl->delta_x);
    vMin = C_LIGHT*(vMin-gbtIdl->rest_freq)/(gbtIdl->rest_freq);
    vMax = C_LIGHT*(vMax-gbtIdl->rest_freq)/(gbtIdl->rest_freq);
    fprintf( *pFile, 
	     "The Line Rest Frequency for these observations was %.6lf MHz.\n",
	   gbtIdl->rest_freq*1.E-6);
    if (vMin < vMax)
      fprintf( *pFile, 
	     "The velocity range is %.3lf to %.3lf km/sec.\n",
	   -vMin*1.E-3, -vMax*1.E-3);
    else
      fprintf( *pFile, 
	     "The velocity range is %.3lf to %.3lf km/sec.\n",
	   -vMax*1.E-3, -vMin*1.E-3);
  } /* end of  line frequency is known */
    
  fprintf( *pFile, "\n");
  return(NULL);
} /* end of openTex() */

long scanList[MAXSCANS];
double elXs[MAXSCANS], elYs[MAXSCANS], tSysXs[MAXSCANS], tSysYs[MAXSCANS];
   
int main(int argc, char * argv[]) 
/* main() is an IDL callable C function that takes a file name,             */
/* a command parameter and an IDL spectrum and adds the spectrum to a FITS */
/* file.  The data are stored in a temporary array until time for writting  */
{ char raStr[32] = "", decStr[32] = "", * errMsg = NULL, fitsName[512] = "",
    textName[512]="", charScanList[512] = "1:10",
    plotName[512]="plotIdl", title[256] = "", xLabel[256] = "",
    yLabel[256] = "";
  long coordType = J2000, doPrint = FALSE,
    nPols = 2, nChan = 0, nScans = 1, 
    i = 0, j = 0, 
    iRow = 0, maxScans = MAXSCANS, iFile = 0,
    nRows = 1, lineWidth = 0, contWidth, iStartSampler = 0,
    count = 0, calWidth = FFTSMOOTHWIDTH, countX = 0,
    countY = 0, doTSys = FALSE, startChan = 0,
    stopChan = 0, doSRREnds = FALSE, doCalOnOff = FALSE;
  char *names[500], fileName[512] = "SCAN=41", 
    channels[MAXIDLSTRING] = "", 
    projectName[MAXIDLSTRING] = 
    "AGBT03B_019_01", 
    directoryName[MAXIDLSTRING] = "./";
  GBTIDL gbtIdl, sumX, sumY, firstIdl, lastIdl;
  double lineNu = 0, gain = .69,
    gainFactor = 1./.69, calRmsLimit = 0.5, 
    tSys = 0., oMedian = 0, oAve = 0, oRms = 0, oMin = 0, oMax = 0, 
    minTSys = 13., nSigma = 7., tInt = 0.,
    aveRa = 0, aveDec = 0, tRx = 14., xs[32767], ys[32767], y2s[32767];
  FILE * pTex = NULL, * pData = NULL;

  if (nSpectra <= 0) 
    freeIdl();

  if (argc < 2) {
    idlToSdfitsHelp();
    return(-1);
  }

  /* parse command line arguments */
  i = 1; 
  while (i < argc) {
    if ( (strstr( argv[i], "-d")) || strstr( argv[i], "-D")) {
      i++;
      strcpy( directoryName, argv[i]);
      fprintf( stderr,"Directory is %s\n", directoryName);
    }
    else if ( (strstr( argv[i], "-e")) || strstr( argv[i], "-E")) {
      doSRREnds = TRUE;
      fprintf ( stderr, "Using Scan Ends for SRR calibration\n");
    }
    else if ( (strstr( argv[i], "-f")) || strstr( argv[i], "-F")) {
      i++;
      sscanf( argv[i], "%lf", &minTSys);
      fprintf ( stderr, "Minimum T sys Limit = %lf\n", minTSys);
    }
    else if ( (strstr( argv[i], "-g")) || strstr( argv[i], "-G")) {
      i++;
      sscanf( argv[i], "%lf", &gain);
      if (gain != 0.) 
	gainFactor = 1.0 / gain;
      fprintf ( stderr, "Efficiency = %lf (factor %lf)\n", 
		gain, gainFactor);
    }
    else if ( (strstr( argv[i], "-h")) || strstr( argv[i], "-H")) {
      doCalOnOff = TRUE;
      fprintf ( stderr, "Dividing all integrations by Cal On - Cal Off\n");
    }
    else if ( (strstr( argv[i], "-i")) || strstr( argv[i], "-I")) {
      i++;
      sscanf( argv[i], "%ld", &iStartSampler);
      fprintf ( stderr, "Start Sampler = %ld\n", iStartSampler);
    }
    else if ( (strstr( argv[i], "-k")) || strstr( argv[i], "-K")) {
      i++;
      sscanf( argv[i], "%lf", &tSys);
      fprintf ( stderr, "Using T sys %lf for reference\n", tSys);
    }
    else if ( (strstr( argv[i], "-l")) || strstr( argv[i], "-L")) {
      i++;
      sscanf( argv[i], "%lf", &lineNu);
      fprintf ( stderr, "Line Frequency = %lf MHz\n", lineNu);
    }
    else if ( (strstr( argv[i], "-m")) || strstr( argv[i], "-M")) {
      i++;
      sscanf( argv[i], "%ld", &lineWidth);
      fprintf ( stderr, "MedianWidth = %ld\n", lineWidth);
    }
    else if ( (strstr( argv[i], "-n")) || strstr( argv[i], "-N")) {
      i++;
      sscanf( argv[i], "%lf", &nSigma);
      fprintf ( stderr, "Noise sigma limit = %lf\n", nSigma);
    }
    else if ( (strstr( argv[i], "-o")) || strstr( argv[i], "-O")) {
      i++;
      strcpy( fitsName, argv[i]);
      fprintf( stderr,"Output Name is %s\n", fitsName);
    }
    else if ( (strstr( argv[i], "-p")) || strstr( argv[i], "-P")) {
      i++;
      strcpy( projectName, argv[i]);
      fprintf( stderr,"Project is %s\n", projectName);
    }
    else if ( (strstr( argv[i], "-r")) || strstr( argv[i], "-R")) {
      i++;
      sscanf( argv[i], "%lf", &calRmsLimit);
      fprintf ( stderr, "Calibrated Rms Limit = %lf\n", calRmsLimit);
    }
    else if ( (strstr( argv[i], "-s")) || strstr( argv[i], "-S")) {
      i++;
      strcpy( charScanList, argv[i]);
      fprintf ( stderr, "Scan List = %s\n", charScanList);
      makeIntList( maxScans, scanList, &nScans, charScanList);
      fprintf ( stderr, "Scan List has %ld entries: %ld to %ld\n",
		nScans, scanList[0], scanList[nScans-1]);
    }
    else if ( (strstr( argv[i], "-t")) || strstr( argv[i], "-T")) {
      doTSys = TRUE;
      fprintf ( stderr, "Setting Channel 1 to TSys\n");
    }
    else if ( (strstr( argv[i], "-w")) || strstr( argv[i], "-W")) {
      i++;
      sscanf( argv[i], "%ld", &calWidth);
      fprintf ( stderr, "FFT Smooth Width = %ld\n", calWidth);
    }
    else if ( (strstr( argv[i], "-x")) || strstr( argv[i], "-X")) {
      i++;
      sscanf( argv[i], "%lf", &tRx);
      fprintf ( stderr, "Receiver Temperature Estimate = %lf\n", tRx);
    }
    else if ( (strstr( argv[i], "-y")) || strstr( argv[i], "-Y")) {
      i++;
      sscanf( argv[i], "%ld", &contWidth);
      fprintf ( stderr, "Median Filter width for continuum baseline: %ld\n",
		contWidth);
    }
    else if ( (strstr( argv[i], "-c")) || strstr( argv[i], "-C")) {
      i++;
      sscanf( argv[i], "%ld:%ld", &startChan,&stopChan);
      fprintf ( stderr, "Writing channels %ld to %ld\n", 
		startChan, stopChan);
      sprintf( channels, "%ld:%ld", startChan, stopChan);
    }
    else
      break;
    i++;
  } /* end while more arguments */

  gbtInit( &go, &gbtPos, &gbtGoInit);

  gbtIdl.max_points = MAXIDLPOINTS;
  firstIdl.max_points = MAXIDLPOINTS;
  lastIdl.max_points = MAXIDLPOINTS;

  /* read first data to find data shape */
  strcpy( fileName, directoryName);
  addSlash( fileName);
  strcat( fileName, argv[argc-1]);

  pData = fopen( fileName, "r");
  if (pData == NULL) {
    fprintf( stderr, "Error: Can not open file %s\n", fileName);
    return(-1);
  }
  else
    fclose(pData);

  errMsg = readIdlFits( fileName, iRow, &nRows, doPrint, &firstIdl);
 
  nChan = firstIdl.data_points;             /* use number of channels to init */
  if (nChan < 1) {
    fprintf( stderr, "No data for %s\n", fileName);
    return(-1);
  }
  if (stopChan <= startChan) {            /* if start, stop not set, use max */
    startChan = 0;
    stopChan = nChan;
  }

  if (stopChan > nChan) {                    
    fprintf( stderr, "Stop Channel input error; %ld > %ld channels\n",
	     stopChan, nChan);
    stopChan = nChan;
  }
   
  if (startChan < 0)                            /* keep channels in range */
    startChan = 0;

  if (strlen( fitsName) < 1) {                  /* if no name, create it */
    stripWhite( firstIdl.source);
    sprintf( fitsName, "%s.fit", firstIdl.source);
    fprintf( stderr, "Output Name: %s\n", fitsName);
  }

  strcpy( textName, fitsName);
  stripExtension( textName); 
  strcat( textName, ".tex");
  openTex( textName, &firstIdl, &pTex);

  fflush(pTex);  /* save in case of crash during processing */

  strcpy( plotName, fitsName);
  stripExtension( plotName);  
  firstIdl.nStates = 1;

  names[0] = fileName;                   /* work with only 1 file for now */
  nScans = 1; 
  /* for all input files */
  for (iFile = 0; iFile < nScans; iFile++) {
    strcpy( fileName, names[iFile]);

    /* for all samplers (frequency ranges and polarizations) */
    for (iRow = 0; iRow < nRows; iRow++) {

      errMsg = readIdlFits( fileName, 
			    iRow, &nRows, FALSE, &gbtIdl);
      if (errMsg)
	break;

      /* if selecting a channel range */
      if (startChan > 0 && (stopChan > startChan) && 
	  (stopChan < gbtIdl.data_points)) {
	j = 0;
	for (i = startChan-1; i < stopChan; i++) {
	  gbtIdl.data[j] = gbtIdl.data[i];
	  j++;
	}
        gbtIdl.data_points = (stopChan - startChan) + 1;
	gbtIdl.ref_ch = gbtIdl.ref_ch - (startChan - 1);
      } /* end if selecting a range */

      nChan = gbtIdl.data_points;
      if ((iRow % 101 == 0) && iRow > 0)
	fprintf( stderr, "Row=%5ld Channels=%5ld: %s %7.3lf K\n", 
		 iRow, nChan, gbtIdl.pol_id, gbtIdl.tsys);

      if (doTSys)
	gbtIdl.data[0] = gbtIdl.tsys;

      errMsg = putIdl( &gbtIdl);            /* save for write */
      if (errMsg) {
	fprintf( stderr, "Error Storing the keep structure\n");
	fprintf( stderr, "Error Message: %s\n", errMsg);
        break;
      }
      tInt += gbtIdl.tintg;                 /* accumulate observing time */

      if (count < MAXSCANS-1)
	count++;
      else {
	fprintf( stderr, "Max Scan Count %ld Exceeding\n", (long)MAXSCANS);
	fprintf( stderr, "Writing %ld Rows\n", count);
	break;
      }	

      aveRa = aveRa + gbtIdl.ra;
      aveDec = aveDec + gbtIdl.dec;

      if (('R' == gbtIdl.pol_id[0]) ||    /* sum each polarizations */
	  ('X' == gbtIdl.pol_id[0]))  {   /* sum each polarizations */
	elXs[countX]   = gbtIdl.el*DEGREE;  /* keep els and Tsys for fit*/
	tSysXs[countX] = gbtIdl.tsys;
	
	if (countX == 0)
	  memcpy( (char *)&sumX, (char *)&gbtIdl, sizeof(GBTIDL));
	else {
	  for (i = 0; i < gbtIdl.data_points; i++) 
	    sumX.data[i] += gbtIdl.data[i];
	}
	countX++;
      }
      else {
	elYs[countY]   = gbtIdl.el*DEGREE;  /* keep els and Tsys for fit*/
	tSysYs[countY] = gbtIdl.tsys;
	if (countY == 0)
	  memcpy( (char *)&sumY, (char *)&gbtIdl, sizeof(GBTIDL));
	else {
	  for (i = 0; i < gbtIdl.data_points; i++) 
	    sumY.data[i] += gbtIdl.data[i];
	}
	countY++;
      } /* end else second sampler */
      
    } /* end for all rows */
  } /* end for all files */

  memcpy( (char *)&lastIdl, (char *)&gbtIdl, sizeof(GBTIDL));
  scanList[0] = gbtIdl.scan_num;
  getScanList( maxScans, &nScans, scanList);

  if (errMsg) 
    fprintf( stderr, "Error writing data: %s\n", errMsg);

  if (countX > 0.) {
    for (i = 0; i < sumX.data_points; i++) 
      sumX.data[i] *= (1./(double)countX);
  }
  if (countY > 0.) {
    for (i = 0; i < sumY.data_points; i++) 
      sumY.data[i] *= (1./(double)countY);
  }    

  if (count > 0) {                      /* if data, compute ave coords */
    aveRa = aveRa/(double)count;
    aveDec = aveDec/(double)count;
  }
  else                                  /* else exit without write */
    return(-1);

  /* copy parameters to the GO structure for writeSdfits file creation */
  strcpy( go.object, firstIdl.source);
  go.scan =  firstIdl.scan_num;
  dateObs2DMjd( firstIdl.date, &go.dateObs);
  go.ra2000 = aveRa*DEGREE;
  go.dec2000 = aveDec*DEGREE;

  if (strstr( go.coordSys, "GAL") != 0) {
    coordType = GALACTIC;
    go.gLon = aveRa*DEGREE;             /* ave coordiantes are lon,lat */
    go.gLat = aveDec*DEGREE;
  }
  else if (strstr (go.coordSys, "AZ") != 0)
    coordType = AZEL;
  else if (go.equinox < 1975.)
    coordType = B1950;
  else
    coordType = J2000;
	   
  fprintf( pTex, "The map contained %ld integrations from scans %ld to %ld.\n",
	   count, firstIdl.scan_num, lastIdl.scan_num);
  errMsg = writeSdfits( fitsName, nScans, scanList,
			coordType, nPols, nChan);

  fprintf( pTex, "The region was observed on %s until %s.\n",
	   firstIdl.date, gbtIdl.date);
  fprintf( pTex, "Integration time was %.0lf seconds per spectrum.\n\n",
	   sumX.tintg);
  fprintf( pTex, "The coordinate system of the observation was %s.\n",
	   go.coordSys);
  rad2str( aveDec*DEGREE, "d.0", decStr);
  if (coordType == GALACTIC) {
    rad2str( aveRa*DEGREE, "d.0", raStr);
    fprintf( pTex, 
	     "The average coordinates of these observations were %s,%s.\n", 
	     raStr, decStr);
  }
  else {
    rad2str( aveRa*DEGREE, "h.1", raStr);
    fprintf( stderr, "The average Ra, Dec of these observations were %s,%s.\n",
	   raStr, decStr);
  }

  /* add _cal for calibrated data */
  strcat( plotName, "_Cal");

  for (i = 0; i < sumX.data_points; i++) {
    xs[i] = sumX.sky_freq + (((double)i - sumX.ref_ch)*sumX.delta_x) ;
    xs[i] *= 0.000001; /* convert to MHz */
    ys[i] = sumX.data[i];
    y2s[i] = sumY.data[i];
  }

  sprintf( title, "%s scans %ld:%ld", go.object, 
	   firstIdl.scan_num, lastIdl.scan_num);
  sprintf( xLabel, "Frequency (MHz %s at %.2lf,%.2lf deg. %s)", 
	   go.velocityDef, aveRa, aveDec, go.coordSys);
  sprintf( yLabel, "Average Intensity (%s)", sumX.calibrate);

  /* plot data with frequency axis */
  quickPlot( plotName, TRUE, "", title, xLabel, yLabel, sumX.data_points - 1, 
	     &xs[1], &ys[1], sumX.pol_id, &y2s[1], sumY.pol_id,
	     NULL, NULL, NULL, NULL);

  medianAveRmsMinMax( countX, elXs, &oMedian, &oAve, &oRms, &oMin, &oMax);
 
  fprintf( stderr, 
	   "%s Stats: med=%.3lf ave=%.3lf rms=%.3lf min=%.3lf max=%.3lf\n",
	   " El ", 
	   oMedian/DEGREE, oAve/DEGREE, oRms/DEGREE, oMin/DEGREE, oMax/DEGREE);

  fprintf( pTex, 
	   "The region was observed in elevation range %.3lf to %.3lf d.\n",
	   oMin/DEGREE, oMax/DEGREE);
  fprintf( stderr, 
	   "The region was observed in elevation range %.3lf to %.3lf d.\n",
	   oMin/DEGREE, oMax/DEGREE);

  medianAveRmsMinMax( countX, tSysXs, &oMedian, &oAve, &oRms, &oMin, &oMax);
 
  fprintf( stderr, 
	   "%s %s Stats: med=%.3lf ave=%.3lf rms=%.3lf min=%.3lf max=%.3lf\n",
	   "Tsys", sumX.pol_id, oMedian, oAve, oRms, oMin, oMax);
  fprintf( pTex, 
	   "The median system temperature of all %s scans was %.3lf K.\n",
	   sumX.pol_id, oMedian);
  fprintf( pTex, 
	   "The minimum, maximum and RMS system temperatures of \nall ");
  fprintf( pTex, "%s scans were %.3lf, %.3lf and %.3lf K.\n",
	   sumX.pol_id, oMin, oMax, oRms);

  medianAveRmsMinMax( countY, tSysYs, &oMedian, &oAve, &oRms, &oMin, &oMax);
 
  fprintf( stderr, 
	   "%s %s Stats: med=%.3lf ave=%.3lf rms=%.3lf min=%.3lf max=%.3lf\n",
	   "Tsys", sumY.pol_id, oMedian, oAve, oRms, oMin, oMax);
  fprintf( pTex, 
	   "The median system temperature of all %s scans was %.3lf K.\n",
	   sumY.pol_id, oMedian);
  fprintf( pTex, 
	   "The minimum, maximum and RMS system temperatures of \nall ");
  fprintf( pTex, "%s scans were %.3lf, %.3lf and %.3lf K.\n",
	   sumY.pol_id, oMin, oMax, oRms);

  /* now add command line info to tex file */
  fprintf( pTex, "\nThe idlToSdfits command line arguments are:\n");  
  for (i = 0; i < argc; i++)
    fprintf( pTex, "%s ", argv[i]);
  fprintf( pTex, "\n");

  fclose( pTex);

  fprintf( stderr, "Wrote AIPS UV-FITS file: %s\n", fitsName);
  return(0);
} /* end of idlToSdfits() == main */
