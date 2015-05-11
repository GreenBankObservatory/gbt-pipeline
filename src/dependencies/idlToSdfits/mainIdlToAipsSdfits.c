/* File mainIdlToAipsSdfits.c, version 1.24, released  11/02/03 at 13:48:54 
   retrieved by SCCS 11/10/26 at 11:45:54     

%% write an AIPS single dish fits file from an idl sdfits structure
:: TEST C program
 
HISTORY:
  130114 GIL clean up documentation of command line arguments
  120326 GIL add more help
  111027 GIL force nPol to an input value
  101122 GIL allow combining data from multiple files
  101014 GIL add verbosity
  100918 GIL update version number and date
  100908 GIL update help
  100728 GIL transmit the image size in go Fits parameters
  100505 GIL optionally remove plots, flag high Tsys
  091230 GIL trim ends from summary spectrum, update help
  091229 GIL accumulate signal and reference scans
  091215 GIL try to regularize the range selection, always even 10 pixels
  091214 GIL try to regularize the range selection, always even 10 pixels
  091211 GIL allow median of single baseline offset (not slope) subtraction
  081231 GIL add option to add a beam channel for calibration
  080314 GIL prepare to separate data from different switch and beam states
  080223 GIL fix printout of polarization
  070706 GIL deal with source names with spaces
  070704 GIL read all tables in the input IDL file
  070621 GIL use tSys values from data, not header
  070617 GIL fix writing Tsys
  070614 GIL revise noise output file, add command line flagging
  070607 GIL flag previous scan if flagging current
  070605 GIL add noise, flag log
  070604 GIL force RR, LL to fix AIPS issues
  070601 GIL version that averages channels
  070531 GIL version that only writes selected channels
  060309 GIL version update
  060307 GIL check for only a single polarization
  060119 GIL check for Nans in data
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
OMISSIONS:
Currently will only read the first table from a GBTIDL
keep file.  The first steps are implimented to allow
reading of multiple tables, but that does not yet work.
*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include "math.h"
#include "dirent.h"
#include "fitsio.h"
#include "MATHCNST.H"
#include "STDDEFS.H"
#include "gbtIdl.h"
#include "gbtGo.h"
#include "gbtAntenna.h"

#define MAXSCANS      100000
#define MAXBEAMS      64
#define MAXSTATES      8
#define J2000    0
#define B1950    1
#define AZEL     2
#define GALACTIC 3
#define MAXIDLSTRING 1024
/* this version is used in the help */
/* Make sure this is the same value as the separate  SOFTVERSION */
/* in writeSdfits.c written to the HISTORY */
#define SOFTVERSION "8.6"

/* externals */
extern long gbtGoInit;
extern struct GOPARAMETERS go;
extern long nIdl;                        /* number of spectra in structure */
extern GBTIDL * idls[];                  /* spectra structures */

extern char * quickPlot( char * plotName, long gv, 
		  char * gnuCmds, char * title, 
		  char * xLabel,  char * yLabel, 
		  long n,  double * xs, 
		  double * y1s, char * y1Label,
		  double * y2s, char * y2Label,
                  double * y3s, char * y3Label,
		  double * y4s, char * y4Label);
extern char * findTableExtension( char * fullFileName, char * extensionName, 
				  long * nRows, long * nBytesPerRow);
extern double angularDistance( double raA, double decA, 
			       double raB, double decB);
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
extern char * getBeamList( long maxScans, long * nBeams, long beamList[]);
extern char * getStateList( long maxScans, long * nStates, long stateList[]);
extern char * putIdl( GBTIDL * idl);
extern char * writeSdfits( char * fitsName, long nScans, long scanList[],
		    long coordType, long nIf);
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
extern char * stripPathName( char * fileName);
extern long inIntList( long inInt, char * intList) ;
extern double median4( double a, double b, double c, double d);
extern char * idToScanIntegration( long id, long * scan, long * integration);
extern char * lineTrim( long bChan, long eChan) ;
extern char * calcAveRmsRange( double a[], long aStart, long aEnd, 
       long bStart, long bEnd, double * aveOut, double * rmsOut);
/* internals */
#define MAXNAMES 500
#define FFTSMOOTHWIDTH 256
#define BEAMFACT     -2.772589        /* - 4. ln(2) */      
long nSpectra = 0;
struct GOPARAMETERS go;
struct GBTPOSITION gbtPos;

char * fixPolarizationForAips() 
/* fixPolarizationForAips() reads through all the stored idl spectra */
/* and replaces the XX and YY with RR and LL spectra ids */
/* eventually this function will be obsolete */
{ long i = 0, j = 0;
  if (nIdl <= 0) 
    return("No Spectra to check");

  /*  fprintf( stderr, "Checking %ld spectra for X or Y (First is %s)\n", 
      nIdl, idls[0]->pol_id); */
  for (i = 0; i < nIdl; i++) {
    for (j = 0; j < strlen(idls[i]->pol_id); j++) {
      if (idls[i]->pol_id[j] == 'X')
	idls[i]->pol_id[j] =  'R';
      else if (idls[i]->pol_id[j] == 'Y')
	idls[i]->pol_id[j] = 'L'; 
    }
  } /* end for all spectra */
  return(NULL);
} /* end of fixPolarizationForAips() */

char * computeBeamModel( double refRa, double refDec, double freqMHz) 
/* computeBeamModel() reads through all the stored idl spectra and replaces */
/* the second channel with the beam model with reference width */
/* INPUTS refRa    reference RA position (radians)   */
/* INPUTS refDec   reference Declination position (radians)   */
/* INPUTS freqMHz  frequency for FWHM beam width calculation (MHz)  */
/* OUTPUT is to the idl structures */
{ long i = 0;
  double dR = 0, dRmax = 1., factor = 1.,
    thetaFWHM = 1., lambdaCm = 1.0, theta2 = 1.;
  if (nIdl <= 0) 
    return("No Spectra to check");

  lambdaCm = C_LIGHT/(1000.*freqMHz);
  thetaFWHM = 0.423 * lambdaCm * ARCMIN;
  theta2 = BEAMFACT/(thetaFWHM*thetaFWHM);  /* combine factors for speed */

  fprintf( stderr, 
	   "Beam model for %7.3lfd,%7.3lfd with width %5.2lf' (FWHM)\n",
	   refRa/DEGREE,refDec/DEGREE, thetaFWHM/ARCMIN);

  dRmax = 8.*thetaFWHM;
  for (i = 0; i < nIdl; i++) {        /* for all spectra */
    dR = angularDistance( DEGREE*(double)idls[i]->ra, DEGREE*(double)idls[i]->dec, 
			  refRa, refDec);
    if (i == 0) 
      fprintf( stderr, "%ld dR=%7.3lf' %7.3lf,%7.3lf\n",
	       i, dR/ARCMIN, idls[i]->ra, idls[i]->dec);
    if (dRmax > dR) {          /* if close enough for the full calc */
      factor = 1000.*exp( theta2*dR*dR);
      idls[i]->data[1] = factor;
      if (factor > 1.)
	fprintf( stderr, "%ld dR=%7.3lf' %7.3lf,%7.3lf %7.2lf\n",
	       i, dR/ARCMIN, idls[i]->ra, idls[i]->dec, factor);
    }
    else                       /* else far from ref, just zero the values */
      idls[i]->data[1] = 0;
  } /* end for all spectra */
  return(NULL);
} /* end of computeBeamModel() */

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
  fprintf( stderr, "idlToSdfits: Program takes a GBTIDL Keep file,\n");
  fprintf( stderr, 
	   " and writes calibrated AIPS-compatible Single Dish Fits Files\n");
  fprintf( stderr, 
	   "idlToSdfits: usage\n");
  fprintf( stderr, 
	   "idlToSdfits [-a <N>] [...] [-o <outName>] [-c <start:stop>] [-s <scanList>] <idlFitsFileName1> [<idlFitsFileName2>]\n");
  fprintf( stderr, 
	   "where [-a <N>]           optionally average N channels to output\n");
  fprintf( stderr, 
	   "where [-b <channelList>] optionally write RMS noise in channelList\n");
  fprintf( stderr, 
	   "                         ie -b 10:200,5000:6000 (channel range 1 to N)\n");
  fprintf( stderr, 
	   "where [-c <start:stop>]  optionally keep only selected channels\n");
  fprintf( stderr, 
	   "                         channel range 1 to N \n");
  fprintf( stderr, 
	   "where [-d <directory>]   optionally specify the input directory\n");
  fprintf( stderr, 
	   "where [-e <lineSigma]    optionally keep only channels with lines > lineSigma RMS value\n");
  fprintf( stderr,   
	   "where [-f <flagList>]    optionally flag selected scans\n");
  fprintf( stderr, "   ie:  -f 7,9-8%c10%c15%c20-1%c10\n", ':','_',':',':' );
  fprintf( stderr, "   Indicates two groups of scan,integrations are flagged\n");
  fprintf( stderr, 
	   "   Group A:  Scans 7 and 9, integrations 8 to 10 in these scans\n");
  fprintf( stderr, 
	   "   Group B:  Scans 15,16,17,18,19,20, integrations 1 to 10\n");
  fprintf( stderr, 
	   "   Summary: Scans and Integration lists are separated by - \n");
  fprintf( stderr, 

	   "   and Groups of Scan;Integrations are separated by %c\n",'_');
  fprintf( stderr, 
	   "where [-g <gainFactor>]  optionally scale spectra by 1/gainFactor\n");
  fprintf( stderr, 
	   "where [-h]               optionally put beam map in channel 2\n");
  fprintf( stderr, 
	   "where [-j]               optionally zero NAN values on output, else flag\n");
  fprintf( stderr, 
	   "where [-k <tSys>]        optionally use constant <tSys> value\n");
  fprintf( stderr, 
	   "where [-l]               optionally do not display the summary line plots\n");
  fprintf( stderr, 
	   "where [-m <maxTsys>]     optionally enter max allowed Tsys\n");
  fprintf( stderr, 
	   "where [-n <rmsNoise>]    optionally flag integrations with excess noise\n");
  fprintf( stderr, 
	   "                         use -b argument to specifiy spectral range\n");
  fprintf( stderr, 
	   "where [-o <outName>]     optionally supply output file name\n");
  fprintf( stderr, 
	   "where [-q]               optionally do a quick (10 sample) median baseline\n");
  fprintf( stderr, 
	   "where [-r]               optionally apply a few channel median for RFI removal\n");
  fprintf( stderr, 
	   "where [-s <scanList>]    optionally use only selected scans\n");
  fprintf( stderr, 
	   "                         (ie -s 1,2,5:10)\n");
  fprintf( stderr, 
	   "where [-t]               optionally replace channel 1 with Tsys\n");
  fprintf( stderr, 
	   "where [-u <rest freq MHz>]  optionally line rest frequency in MHz\n");
  fprintf( stderr, 
	   "where [-v <verbosityLevel>] optionally change printout level (0=min, medium=2, 3=max\n");
  fprintf( stderr, 
	   "                         to produce a continuum image.\n");
  fprintf( stderr, 
	   "where [-w <continuum Width>]  optionally subtrack median filtered spectral baseline\n");
  fprintf( stderr, 
	   "  Note, channels ranges are selected (-c) before averaging (-a)\n");
  fprintf( stderr, 
	   "  Note, channels are averaged before median filter baselines (-w)!\n");
  fprintf( stderr, 
	   "where [-x <tRx>]         optionally provide a receiver temperature\n");
  fprintf( stderr, 
	   "where [-y]               optionally allow XX and YY polarizations\n");
  fprintf( stderr, 
	   "where [-z <minTsys>]     optionally enter min allowed Tsys\n");
  fprintf( stderr, " Data are given negative weights if outside allowed Tsys\n");
  fprintf( stderr, 
	   "where [-1]               Force only 1 output polarizations\n");
  fprintf( stderr, 
	   "where [-2]               Force 2 output polarizations\n");
  fprintf( stderr, 
	   "where [-4]               Force 4 output polarizations\n");
  fprintf( stderr, 
	   "The -1,-2 or -4 options assure compatiblity of different observations with AIPS processing of the spectra\n");
  fprintf( stderr, 
	   "where <idlFitsFileName>  name of input IDL keep file to convert\n");
  fprintf( stderr, 
	   "where <idlFitsFileName2> optional name of 2nd input IDL file to convert\n");
  fprintf( stderr, 
	   "                         if the two input files contain orthogonal polarizations,\n");
  fprintf( stderr, 
	   "                         values are merged with common coordiantes\n");
  fprintf( stderr, 
	   "The output file has extension '.sdf' == Single Dish Fits\n");
  fprintf( stderr,
	   "NOTE: spectra with more than %1d channels can not be handled by idlToSdfits\n",MAXIDLPOINTS);
  fprintf( stderr,
	   "NOTE: only %1d spectra can be written in each call to idlToSdfits\n", MAXSCANS);
  fprintf( stderr, 
	   "Version %s: Date: %s\n", SOFTVERSION, "May 11, 2015" );
  fprintf( stderr, 
	   "----Original Code by Glen Langston\n\n");
  fprintf( stderr, 
	   "----For help and bug reporting visit the NRAO helpdesk at help.nrao.edu\n\n");
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
    /* first calculate the min and max frequencies */
    vMin = gbtIdl->sky_freq + ((1. - gbtIdl->ref_ch)*gbtIdl->delta_x);
    vMax = gbtIdl->sky_freq + 
      ((gbtIdl->data_points - gbtIdl->ref_ch)*gbtIdl->delta_x);
    /* now comput min and max velocities */
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

long scanList[MAXSCANS], noiseList[MAXSCANS], beamList[MAXBEAMS],
  stateList[MAXSTATES], keepScanList[MAXSCANS];
double elXs[MAXSCANS], elYs[MAXSCANS], tSysXs[MAXSCANS], tSysYs[MAXSCANS],
  tRmsXs[MAXSCANS], tRmsYs[MAXSCANS];
#define MAXMEDIAN 132768
double tempDoubles[MAXMEDIAN], medianDoubles[MAXMEDIAN], maxLines[MAXMEDIAN];
long lineScans[MAXSCANS], lineInts[MAXSCANS];

char * lineFind( GBTIDL * pIdl, double lineSigma, long doPrint, 
		 long bChan, long eChan, long * nLine, double lines[])
{ long i = 0, j = 0, n = 0, nChan = pIdl -> data_points;
  double ave = 0, rms = 0, nSigma = lineSigma; 

  if (nChan < 1) 
    return(NULL);
  if (bChan < 1)                  /* limit search range to allow smoothing */
    bChan = 1;
  if (eChan > nChan - 2) 
    bChan = nChan - 2;

  for (i = bChan; i < eChan; i++) {
    tempDoubles[n] = 
      (pIdl -> data[i-1] + pIdl -> data[i] + pIdl -> data[i+1])/3.;
    n++;
  } /* end for all noise channels to average */

  calcAveRmsRange( tempDoubles, 0, 2, 2, n, &ave, &rms);
  nSigma = lineSigma * rms;

  /* for all values, look for signficant peaks */
  for ( i = 0; i < n; i++) {
    /* if significant */
    if (tempDoubles[i] > nSigma) {
      *nLine = *nLine + 1;
      j = i+bChan;
      /* if the strongest line in this channel */
      if (tempDoubles[i] > lines[j]) {
	lines[j] = tempDoubles[i];
	lineScans[j] = pIdl->scan_num;
	lineInts[j] = pIdl->iIntegration;
	if (doPrint) 
	  fprintf( stderr, "Line%8ld:%6ld %4ld %4ld %10.3lf\n",
		   *nLine, j, lineScans[j], lineInts[j], lines[j]);
      } /* end if the strongest line in this channel */
    } /* end if a strong line */
  } /* end for all channels in search region */
	    
  return(NULL);
} /* end of lineFind() */

char * lineSummary( long doPrint, long nLine, long nChan, 
		    double lines[], long *bChan, long *eChan)
{ long i = 0, range = 0, n = 0, minChan = 0, maxChan = 0, peakChan = 0;
  double xs[MAXMEDIAN];
  
  if (nChan < 1) 
    return(NULL);

  /* for all values, look for signficant peaks */
  for ( i = 0; i < nChan; i++) {
    xs[i] = i;
    /* if significant */
    if (lines[i] != 0) {
      if (minChan == 0) 
	minChan = i;
      maxChan = i;
      if (lines[i] > lines[peakChan]) 
	peakChan = i;
      n++;
    } /* end if a strong line */
  } /* end for all channels in search region */

  range = maxChan - minChan;
  if (range < 80) 
    range = 80;

  *bChan = minChan - (range/4);
  if (*bChan < 0) 
    *bChan = 0;
  *eChan = maxChan + (range/4);
  if (*eChan >= nChan) 
    *eChan = nChan - 1;
  /* now round to even 10 channels */
  *bChan = *bChan / 10;
  *bChan = (*bChan * 10);
  *eChan = *eChan / 10;
  *eChan = (*eChan * 10) - 1;

  /* now trim out spectra without any data */
  for (i = *bChan; i < nChan; i++) {
    if (lines[i] != 0) 
      break;
    *bChan = i+1;
  }
  for (i = *eChan; i > 0; i--) {
    if (lines[i] != 0) 
      break;
    *eChan = i;
  }

  if (doPrint) {
    if (n > 0) {
      fprintf( stderr, "Channels %ld:%ld have lines, peak at %ld: %10.3lf\n",
	     *bChan + 1, *eChan + 1, peakChan, lines[peakChan]);
	     
      quickPlot( "lineSummary", TRUE, "", "Peak Line Intensity versus Channel",
		 "Channel", "Intensity", *eChan - *bChan, &xs[*bChan],
		 &lines[*bChan], "Peak Line Intensities", NULL, NULL, 
		 NULL, NULL, NULL, NULL);
    }
    else
      fprintf( stderr, "No Lines found in spectra\n");

  } /* end if printing results */

  return(NULL);
} /* end of lineSummary() */

char * idlAveRms( GBTIDL * pIdl, long nNoise, 
		  long channels[], double * ave, double * rms)
{ long i = 0, j = 0, n = 0, nChan = pIdl -> data_points;

  *ave = *rms = 0; 

  if (nChan < 1) 
    return(NULL);

  n = 0;
  for (i = 1; i < nNoise; i++) {
    j = channels[i];
    if (j >= 0 && j < nChan) {
      tempDoubles[n] = pIdl -> data[j];
      n++;
    }
  } /* end for all noise channels to average */

  calcAveRmsRange( tempDoubles, 0, 2, 2, n, ave, rms);

  return(NULL);
} /* end of idlAveRms() */

char * writeNoiseSummary( FILE * pNoise, GBTIDL * pIdl, long nNoise, 
			  long channels[], double * ave, double * rms)
{ char raStr[32] = "", decStr[32] = "", * errMsg = NULL;
  long nChan = pIdl -> data_points;

  *ave = *rms = 0; 

  if (nChan < 1) 
    return(errMsg);

  errMsg = idlAveRms( pIdl, nNoise, channels, ave, rms);

  if (pNoise != NULL) {
    rad2str( pIdl->ra*DEGREE, "h.1", raStr);
    rad2str( pIdl->dec*DEGREE, "d.0", decStr);
    raStr[strlen(raStr)-1] = EOS;
    decStr[strlen(decStr)-1] = EOS;
    fprintf( pNoise, " %12.4lf %12.4lf :Rms,Ave ", *rms, *ave);
    fprintf( pNoise, " %4ld %4ld :Scan,Int %s:Pol %s,%s :Ra,Dec\n",
	     pIdl->scan_num, pIdl->iIntegration+1, pIdl->pol_id, 
	     raStr, decStr);
  }
  return(errMsg);
} /* end of writeNoiseSummary() */

int isFlaggedScanInt( char * flagStr, long iScan, long iInt, long doPrint)
/* isFlaggedScanInt returns true if this scan, int is flagged */
/* flag string has a complex syntax to allow multiple types of flagging */
/* example:  "7,9-8:10%15-1:10" */
/* means flag two groups of scan,integrations: */
/* Group A:  Scans 7 and 9, integrations 8 to 10 in both scans */
/* Group B:  Scan 15, integrations 1 to 10 in that scan */
/* Summary scans and integration lists are separated by - */
/* Pairs of Scan;Integrations are separated by % */
{ 
  char scanStr[1000] = "", intStr[1000] = "", pairStr[1000]="", group = '_',
    pair='-';
  long isFlagged = FALSE, i = 0, iStart = 0, j = 0, k = 0, lenPair = 0,
    isScan = FALSE, isInt = FALSE, nGroups = 0;
 
  if (strlen(flagStr) < 1)
    return isFlagged;

  i=0;                                 /* for all chars in flagged string */
  do {

    if (flagStr[i] == group || i == strlen( flagStr) - 1) {
      if (flagStr[i] == group)
        lenPair = i - iStart;
      else
	lenPair = strlen(flagStr) - iStart;

      lenPair++;
      strncpy( pairStr, &flagStr[iStart], lenPair);
      if (pairStr[lenPair] == group)
	pairStr[lenPair] = EOS;
      pairStr[lenPair+1] = EOS;
      iStart = i + 1;                   /* prepare for next scan;int pair */
      nGroups++;
      for (j = 0; j < lenPair; j++) {
	if (pairStr[j] == pair) {
          strcpy( scanStr, pairStr);
	  scanStr[j] = EOS;
	  strcpy( intStr, &pairStr[j+1]);
	  isScan = inIntList( iScan, scanStr);
          /* now terminate int list at start of next pair */
	  for (k = 0; k < strlen(intStr); k++) {
	    if (intStr[k] == group)
	      intStr[k] = EOS;
	  }
	  isInt  = inIntList( iInt, intStr);
          isFlagged = isScan && isInt;
          if (isFlagged) {
	    fprintf( stderr, "Flagged Scan-Int=%4ld-%4ld; its in list %s-%s\n",
		     iScan, iInt, scanStr, intStr);
	    return isFlagged;
	  } /* end if in flagged list */
	} /* if mid-point of scan;integration list found */
      } /* end for all characters in the pair */
      if (doPrint) 
	fprintf( stderr,"Checking Group %4ld_ Scans-Int pairs: %s-%s\n",
		 nGroups, scanStr,intStr);
    } /* end if end of a scan;integratin pair */
    i++;
  } while (i < strlen( flagStr));
  return isFlagged;
} /* end of isFlaggedScanInt() */

int main(int argc, char * argv[]) 
/* main() is an IDL callable C function that takes a file name,             */
/* a command parameter and an IDL spectrum and adds the spectrum to a FITS */
/* file.  The data are stored in a temporary array until time for writting  */
{ char raStr[32] = "", decStr[32] = "", * errMsg = NULL, fitsName[512] = "",
    textName[512]="", charScanList[512] = "",
    plotName[512]="plotIdl", title[256] = "", xLabel[256] = "",
    yLabel[256] = "", gnuCmds[512] = "", argument[32] = "",
    noiseName[512] = "", todayStr[32] = "";
  int status = 0;
  long coordType = J2000, doPrint = FALSE, hasNans = FALSE, doRFI = FALSE,
    nPols = 0, nChan = 0, nScans = 1, nAve = 0, nSum = 0, doXY = FALSE,
    i = 0, skipCount = 101, k = 0, iRow = 0, maxScans = MAXSCANS, nFile = 0,
    iFile = 0, nRows = 1, iStartSampler = 0, isXyPol = FALSE, iTable = 0,
    count = 0, inContWidth = 0, countX = 0, contWidth, nNoise = 0, 
    countY = 0, doTSys = FALSE, startChan = 0, maxChannels = MAXSCANS,
    stopChan = 0, doFlag = FALSE, nBeams = 1, nStates = 1,
    flaggedLast = 0, mjd =  today2mjd(), firstNanChan = 0, lastNanChan = 0,
    zeroNans = FALSE, doBeam = FALSE, doQuickBaseline = FALSE, bChan = 0,
    eChan = 0, doEndTrim = FALSE, nLine = 0, nKeepScans = 0,
    doLineSummary = FALSE, doPlot = TRUE, nTFlag = 0, verbosity=1;
  char *names[500], fileName[512] = "SCAN=41", flagStr[1024]="",
    channels[MAXIDLSTRING] = "", bandForNoise[512] = "", * pName = NULL, 
    projectName[MAXIDLSTRING] = "AGBT03B_019_01",
    directoryName[MAXIDLSTRING] = "./", summaryName[MAXIDLSTRING] = "",
    summaryDir[MAXIDLSTRING] = "", summaryTag[512]="";
  GBTIDL gbtIdl, sumX, sumY, firstIdl, lastIdl, tempIdl;
  double gain = .69, gainFactor = 1./.69, tSys = 0., tSysAve = 0,
    oMedian = 0, oAve = 0, oRms = 0, oMin = 0, oMax = 0, ave = 0, rms = 0,
    noiseLimit = 0., tInt = 0., elMin = 0, elMax = 0,
    aveRa = 0, aveDec = 0, tRx = 14., xs[32767], ys[32767], y2s[32767],
    freqMHz = 1420.4, lineSigma = 10, minTSys = 0.0, maxTSys = 1.e9,
    minRa = 0, maxRa = 0, minDec = 0, maxDec = 0, restFreq = 0;
  FILE * pTex = NULL, * pData = NULL, * pNoise = NULL;

  if (nSpectra <= 0) 
    freeIdl();

  if (argc < 2) {
    idlToSdfitsHelp();
    return(-1);
  }

  /* parse command line arguments */
  i = 1; 
  while (i < argc - 1) {
    strncpy( argument, argv[i], 2);
    argument[2] = EOS;
    if ( (strstr( argument, "-a")) || strstr( argument, "-A")) {
      i++;
      sscanf( argv[i], "%ld", &nAve);
      if (verbosity > 2)
	fprintf ( stderr, "Averaging %ld channels before write\n", nAve);
    }
    else if ( (strstr( argument, "-b")) || strstr( argument, "-B")) {
      i++;
      strcpy( bandForNoise, argv[i]);
      if (verbosity > 2)
      fprintf ( stderr, "Measureing RMS Noise in Bands: %s\n", 
		bandForNoise);
      makeIntList( maxChannels, noiseList, &nNoise, bandForNoise);
      if (verbosity > 2)
      fprintf ( stderr, "Noise Channel List:  %ld entries: %ld to %ld\n",
		nNoise, noiseList[0], noiseList[nNoise-1]);
    }
    else if ( (strstr( argument, "-c")) || strstr( argument, "-C")) {
      i++;
      sscanf( argv[i], "%ld:%ld", &startChan,&stopChan);
      if (verbosity > 2)
      fprintf ( stderr, "Writing channels %ld to %ld\n", 
		startChan, stopChan);
      sprintf( channels, "%ld:%ld", startChan, stopChan);
      /* change from 1 based to 0 based counting */
      /* stop channel is not changed because tests are all < N (not N-1) */
      startChan = startChan - 1;
      if (startChan < 0)
	startChan = 0;
    }
    else if ( (strstr( argument, "-d")) || strstr( argument, "-D")) {
      i++;
      strcpy( directoryName, argv[i]);
      if (verbosity > 2)
      fprintf( stderr,"Directory is %s\n", directoryName);
    }
    else if ( (strstr( argument, "-e")) || strstr( argument, "-E")) {
      doEndTrim = TRUE;
      i++;
      sscanf( argv[i], "%lf", &lineSigma);
      if (verbosity > 2)
      fprintf( stderr,"Trimming Line-free spectral ends; lines > %lf Sigma\n",
	       lineSigma);
    }
    else if ( (strstr( argument, "-f")) || strstr( argument, "-F")) {
      i++;
      strcpy( flagStr, argv[i]);
      if (verbosity > 2)
      fprintf ( stderr, "Flagging Scan;integrations= %s\n", flagStr);
      /* print summary of flagging */
      isFlaggedScanInt( flagStr, -1, -1, TRUE);
    }
    else if ( (strstr( argument, "-g")) || strstr( argument, "-G")) {
      i++;
      sscanf( argv[i], "%lf", &gain);
      if (gain != 0.) 
	gainFactor = 1.0 / gain;
      if (verbosity > 2)
      fprintf ( stderr, "Efficiency = %lf (factor %lf)\n", 
		gain, gainFactor);
     }
    else if ( (strstr( argument, "-h")) || strstr( argument, "-H")) {
      doBeam = TRUE;
      if (verbosity > 2)
      fprintf ( stderr, "Replacing channel 2 with a beam map\n");
    }
    else if ( (strstr( argument, "-i")) || strstr( argument, "-I")) {
      i++;
      sscanf( argv[i], "%ld", &iStartSampler);
      if (verbosity > 2)
      fprintf ( stderr, "Start Sampler = %ld\n", iStartSampler);
    }
    else if ( (strstr( argument, "-j")) || strstr( argument, "-J")) {
      zeroNans = TRUE;
      if (verbosity > 2)
      fprintf ( stderr, "Replacing NANs with Zero\n");
    }
    else if ( (strstr( argument, "-k")) || strstr( argument, "-K")) {
      i++;
      sscanf( argv[i], "%lf", &tSys);
      if (verbosity > 2)
      fprintf ( stderr, "Using T sys %lf for reference\n", tSys);
    }
    else if ( (strstr( argument, "-l")) || strstr( argument, "-L")) {
      doPlot = FALSE;
      if (verbosity > 2)
      fprintf ( stderr, "Not generating summary line Plot \n");
    }
    else if ( (strstr( argument, "-m")) || strstr( argument, "-M")) {
      i++;
      sscanf( argv[i], "%lf", &maxTSys);
      if (verbosity > 2)
      fprintf ( stderr, "Maximum T sys Limit = %lf\n", maxTSys);
    }
    else if ( (strstr( argument, "-n")) || strstr( argument, "-N")) {
      i++;
      sscanf( argv[i], "%lf", &noiseLimit);
      if (verbosity > 2)
      fprintf ( stderr, "Noise limit = %lf\n", noiseLimit);
      doFlag = TRUE;
    }
    else if ( (strstr( argument, "-o")) || strstr( argument, "-O")) {
      i++;
      strcpy( fitsName, argv[i]);
      if (verbosity > 2)
      fprintf( stderr,"Output Name is %s\n", fitsName);
    }
    else if ( (strstr( argument, "-p")) || strstr( argument, "-P")) {
      i++;
      strcpy( projectName, argv[i]);
      if (verbosity > 2)
      fprintf( stderr,"Project is %s\n", projectName);
    }
    else if ( (strstr( argument, "-q")) || strstr( argument, "-Q")) {
      doQuickBaseline = TRUE;
      if (verbosity > 2)
      fprintf( stderr,"Doing quick median baseline subtraction\n");
    }
    else if ( (strstr( argument, "-r")) || strstr( argument, "-R")) {
      doRFI = TRUE;
      if (verbosity > 2)
      fprintf ( stderr, "Median Filtering to remove RFI\n");
    }
    else if ( (strstr( argument, "-s")) || strstr( argument, "-S")) {
      i++;
      strcpy( charScanList, argv[i]);
      fprintf ( stderr, "Scan List = %s\n", charScanList);
      makeIntList( maxScans, keepScanList, &nKeepScans, charScanList);
      if (verbosity > 2)
      fprintf ( stderr, "Scan List has %ld entries: %ld to %ld\n",
		nKeepScans, keepScanList[0], keepScanList[nKeepScans-1]);
    }
    else if ( (strstr( argument, "-t")) || strstr( argument, "-T")) {
      doTSys = TRUE;
      if (verbosity > 2)
      fprintf ( stderr, "Setting Channel 1 to TSys\n");
    }
    else if ( (strstr( argument, "-v")) || strstr( argument, "-V")) {
      i++;
      sscanf( argv[i], "%ld", &verbosity);
    }
    else if ( (strstr( argument, "-u")) || strstr( argument, "-U")) {
      i++;
      sscanf( argv[i], "%lf", &restFreq);
      gbtIdl.rest_freq = restFreq * 1.E6;
      if (verbosity > 2)
      fprintf ( stderr, "RestFreq %12.3lf (MHz)\n", restFreq);
    }
    else if ( (strstr( argument, "-w")) || strstr( argument, "-W")) {
      i++;
      sscanf( argv[i], "%ld", &inContWidth);
      if (verbosity > 2)
      fprintf ( stderr, 
		"Median Filter width for continuum baseline: %ld\n",
		inContWidth);
    }
    else if ( (strstr( argument, "-x")) || strstr( argument, "-X")) {
      i++;
      sscanf( argv[i], "%lf", &tRx);
      if (verbosity > 2)
      fprintf ( stderr, "Receiver Temperature Estimate = %lf\n", tRx);
    }
    else if ( (strstr( argument, "-y")) || strstr( argument, "-Y")) {
      doXY = TRUE;
      if (verbosity > 2)
      fprintf ( stderr, "Allowing XX and YY polarizations\n");
    }
    else if ( (strstr( argument, "-z")) || strstr( argument, "-Z")) {
      i++;
      sscanf( argv[i], "%lf", &minTSys);
      if (verbosity > 2)
      fprintf ( stderr, "Minimum T sys Limit = %lf\n", minTSys);
    }
    else if ( strstr( argument, "-1")) {
      nPols = 1;
      if (verbosity > 2)
	fprintf ( stderr, "Forcing one Polarization output\n");
    }
    else if ( strstr( argument, "-2")) {
      nPols = 2;
      if (verbosity > 2)
	fprintf ( stderr, "Forcing two Polarizations output\n");
    }
    else if ( strstr( argument, "-4")) {
      nPols = 4;
      if (verbosity > 2)
	fprintf ( stderr, "Forcing four Polarizations output\n");
    }
    else
      break;
    i++;
  } /* end while more arguments */

  /* remaining arguments are file names */
  nFile = argc - i;
  if (verbosity > 3) 
    fprintf( stderr, "Converting %ld files to AIPS SDFITS format\n", nFile);

  contWidth = inContWidth;
  gbtInit( &go, &gbtPos, &gbtGoInit);

  gbtIdl.max_points = MAXIDLPOINTS;
  firstIdl.max_points = MAXIDLPOINTS;
  lastIdl.max_points = MAXIDLPOINTS;

  /* read first data to find data shape */
  strcpy( fileName, directoryName);
  addSlash( fileName);
  strcpy( summaryDir, fileName);
  strcat( fileName, argv[argc-1]);
  strcat( summaryDir, "summary/");
  status = mkdir( summaryDir, S_IRWXU | S_IRWXG | S_IRWXO);
  /*  fprintf( stderr, "%s mkdir() Status = %d!\n", summaryDir, status); */
  strcat( summaryName, summaryDir);
  strcpy( summaryTag, argv[argc-1]);
  stripPathName( summaryTag);
  stripExtension( summaryTag);
  strcat( summaryName, summaryTag);

  /* if more than one file argument */
  pData = fopen( fileName, "r");
  if (pData == NULL) {
    fprintf( stderr, "Error: Can not open file %s\n", fileName);
    return(-1);
  }
  else
    fclose(pData);

  errMsg = readIdlFits( fileName, iRow, &nRows, doPrint, &firstIdl);
  nChan = firstIdl.data_points;

  if (stopChan <= startChan) {      /* if start, stop not set, use max */
    startChan = 0;
    stopChan = nChan;
  }
  if (startChan < 0)                       /* keep channels in range */
    startChan = 0;

  if (stopChan > nChan) {                    
    if (verbosity > 0)
      fprintf( stderr, "Stop Channel input error; %ld > %ld channels\n",
	     stopChan, nChan);
    stopChan = nChan;
  }
    
  if (verbosity > 2)
    fprintf( stderr, "Number of Channels in input Spectrum; %ld\n", nChan);
 
  if ((nRows / 15) > skipCount) {
    skipCount = nRows /30;
    skipCount = (2*skipCount) + 1;
  }

  /* transfer all file names to list */
  for (iFile = 0; iFile < nFile; iFile++) {
    i = argc - nFile + iFile;
    if (verbosity > 2) 
      fprintf( stderr, "File %ld: %s\n", i, argv[i]);
    names[iFile] = argv[i];
  }

  /* names[0] = fileName;                      work with only 1 file for now */
  nScans = 1; 
  /* for all input files */
  for (iFile = 0; iFile < nFile; iFile++) {
    strcpy( fileName, names[iFile]);
    if (verbosity > 2)
      fprintf( stderr, "Processing File %s\n", fileName);

    /* for all tables in the GBTIDL keep file */
    for (iTable = 0; iTable < 1; iTable++) {
      
      /*      errMsg = findTableExtension( fileName, "SINGLE DISH",
				   &nRows, &nBytesPerRow);
      if (errMsg || nBytesPerRow < 1) 
	break;
      */
    /* for all samplers (frequency ranges and polarizations) */
    for (iRow = 0; iRow < nRows; iRow++) {

      errMsg = readIdlFits( fileName,
			    iRow, &nRows, FALSE, &gbtIdl);
      if (errMsg) {
	if (verbosity > 0)
	  fprintf( stderr, "Reading %s: %s\n",fileName, errMsg);
	break;
      }

      if (strlen( charScanList) > 0) {  /* if user input scan list */
        /* check if scan in selected scan list (does not check integrations)*/
	if ( !inIntList( gbtIdl.scan_num, charScanList)) /* if not in list */
	  continue;                     /* ignore data */
      } /* end if user input scan list */

      nChan = gbtIdl.data_points;
      if (nChan < 1)
	continue;

      /* if flagging selected scans and integrations */
      if (isFlaggedScanInt( flagStr, gbtIdl.scan_num, gbtIdl.iIntegration, 
			    FALSE))
	continue;

      if (startChan != 0 || stopChan != nChan) {
        k = 0;                               /* index of copy; move to temp */
	for (i = startChan; i < nChan && i < stopChan; i++) {
	  tempIdl.data[k] = gbtIdl.data[i];
	  k++;
	}
	if (count == 0  && verbosity > 0)
	  fprintf( stderr, "Triming spectrum from %ld to %ld channels\n",
		   nChan, k);
	nChan = k;
	for (i = 0; i < nChan; i++)          /* now copy back from temp */
	  gbtIdl.data[i] = tempIdl.data[i];
	gbtIdl.data_points = nChan;
	gbtIdl.ref_ch = gbtIdl.ref_ch - startChan;
      } /* end if trimming down the spectrum */
    
      if (doRFI) {                        /* flag out narrow RFI lines */
	for (i = 2; i < nChan-2; i++)        /* for all input channels */
	  medianDoubles[i] = median4( gbtIdl.data[i-2], gbtIdl.data[i-1],
				      gbtIdl.data[i+1], gbtIdl.data[i+2]);
	for (i = 2; i < nChan-2; i++)        /* for all input channels */
	  gbtIdl.data[i] = median4( medianDoubles[i-2], medianDoubles[i-1],
				    medianDoubles[i+1], medianDoubles[i+2]);
      } /* end if flagging isolated RFI */

      if (nAve > 1 && nAve <= nChan) {       /* if averaging data */
        k = 0;                               /* index of copy; move to temp */
	nSum = 0;
	tempIdl.data[k] = 0;
	for (i = 0; i < nChan; i++) {        /* for all input channels */
	  tempIdl.data[k] = tempIdl.data[k] + gbtIdl.data[i];
	  nSum ++;
	  if (nSum == nAve) {
	    tempIdl.data[k] = tempIdl.data[k]/(double)nSum;
	    k++;
	    tempIdl.data[k] = 0;
	    nSum = 0;
	  }
	} /* end for all input channels */
	if ( nSum > 0) {
	  tempIdl.data[k] = tempIdl.data[k]/(double)nSum;
	  k++;
	}
	nChan = k;
	for (i = 0; i < nChan; i++)          /* now copy back from temp */
	  gbtIdl.data[i] = tempIdl.data[i];
	gbtIdl.data_points = nChan;
	gbtIdl.ref_ch = (gbtIdl.ref_ch-0.5)/((double)nAve) + 0.5;
	gbtIdl.delta_x = gbtIdl.delta_x * (double)nAve;
      } /* end if averaging channels */

      if (nNoise <= 0) {	             /* now need channels for Tsys */
	sprintf( bandForNoise, "%ld:%ld",3*nChan/8, 5*nChan/8);
	makeIntList( maxChannels, noiseList, &nNoise, bandForNoise);
      } /* end if no input tSys values */

      if (doTSys) 
	errMsg = idlAveRms( &gbtIdl, nNoise, noiseList, &tSysAve, &rms);

      if (contWidth > 2 && contWidth < nChan) {
	for (i = 0; i < nChan; i++) 
	  tempDoubles[i] = gbtIdl.data[i];
        medianFilter( nChan, contWidth/2, tempDoubles, medianDoubles);
	for (i = 0; i < nChan; i++) 
	  gbtIdl.data[i] = gbtIdl.data[i] - medianDoubles[i];
      }	/* end if median filtering */

      if (doQuickBaseline) {
	k = nChan/11;
	/* select 10 values widely spaced across the entire spectrum */
	for (i = 0; i < 10; i++) 
	  tempDoubles[i] = gbtIdl.data[(i+1)*k];
	/* select the median of all these values */
	medianFilter( 10, 5, tempDoubles, medianDoubles);
	/* subtract the median from all channels (0th order baseline) */
	for (i = 0; i < nChan; i++) 
	  gbtIdl.data[i] = gbtIdl.data[i] - medianDoubles[4];
      } /* end if doing median baseline */

      if (gbtIdl.pol_id[0] == 'X' || gbtIdl.pol_id[0] == 'Y')
	isXyPol = TRUE;

      if ((iRow % skipCount == 0) && iRow > 0 && (verbosity > 1))
	fprintf( stderr, "Row=%5ld Channels=%5ld: %s %7.3lf K\n", 
		 iRow, nChan, gbtIdl.pol_id, gbtIdl.tsys);

      hasNans = FALSE;
      firstNanChan = lastNanChan = -1;
      for (i = 0; i < nChan; i++) {
	if (isnan( gbtIdl.data[i] )) {
	  hasNans = TRUE;
	  if (firstNanChan < 0)
	    firstNanChan = i;
	  lastNanChan = i;
	  if (zeroNans)
	    gbtIdl.data[i] = 0;
	} /* end if a NAN in the data */
      } /* end for all channels */

      if (hasNans) {  /* if NANS in data, report */
        if (zeroNans) {
	  if (verbosity > 0) 
	    fprintf( stderr, 
		   "Scan %ld (%s %7.3lf K) NANs zeroed: Channels %ld-%ld\n",
		   gbtIdl.scan_num, gbtIdl.pol_id, gbtIdl.tsys, 
		   firstNanChan, lastNanChan);
	}
        else {
	  if (verbosity > 0)
	    fprintf( stderr, 
		   "Scan %ld (%s %7.3lf K, Channels %ld to %ld) has Nans; data flagged\n",
		   gbtIdl.scan_num, gbtIdl.pol_id, gbtIdl.tsys,
		   firstNanChan, lastNanChan);
	  continue;
	}
      } /* end if obs has NANs */

      if (count == 0) {  /* if very first acceptable spectrum */
	memcpy( (char *)&firstIdl, (char *)&gbtIdl, sizeof(GBTIDL));
	nChan = firstIdl.data_points;      /* use number of channels to init */
	if (nChan < 1) {
	  if (verbosity > 0) 
	    fprintf( stderr, "No data for %s\n", fileName);
	  return(-1);
	}

	if (strlen( fitsName) < 1) {             /* if no name, create it */
	  /* if a TCal_ file, remove extenstion and prefix */
	  pName = strstr( fileName, "TCal_");
	  if (pName != NULL) {
	    strcpy(fitsName, (pName+5));
	    stripExtension( fitsName);
	  }
	  else {  /* else use source name */
	    stripWhite( firstIdl.source);
	    for (i = 0; i < strlen( firstIdl.source); i++)
	      if (firstIdl.source[i] == ' ')
		firstIdl.source[i] = '_';
	    strcpy( fitsName, firstIdl.source);
	  }
	  strcat( fitsName, ".sdf");
	  if (verbosity > 1) 
	    fprintf( stderr, "Output: %s (Single Dish Fits = sdf) from %s\n", 
		   fitsName, fileName);
	} /* end if no input name */

	strcpy( textName, summaryName);
	strcat( textName, ".tex");
	openTex( textName, &firstIdl, &pTex);
	
	fflush(pTex);  /* save in case of crash during processing */
	
	strcpy( plotName, fitsName);
	stripExtension( plotName);  
	firstIdl.nStates = 1;

        if (nNoise > 0) {	
	  strcpy( noiseName, summaryName);
	  strcat( noiseName, ".noi");
	  
	  pNoise = fopen( noiseName, "w");
	  if (pNoise == NULL) {
	    if (verbosity > 0) 
	      fprintf( stderr, "Error opening Scan RMS noise Log: %s\n",
		       noiseName);
	  }
	  else {
	    fprintf( pNoise, 
		     "#Logging noise for each Scan/Int/Pol of file:%s\n",
		     fileName);
	    mjd2str( mjd, todayStr);
	    fprintf( pNoise, 
		     "#Execution on %s\n", todayStr);
	    fprintf( pNoise, 
	     "#Measureing noise in channels %s of %ld output channels\n",
		     bandForNoise, nChan);
	  } /* end else summarise file */
	} /* end if logging RMS noise*/
	/* for all channels, prepare track channels with lines */
	for (i = 0; i < nChan; i++) {
	  maxLines[i] = 0;
	} /* end for all channels */
	for (i = 0; i < MAXSCANS; i++) {
	  lineScans[i] = 0;
	  lineInts[i] = 0;
	}
      } /* end if first acceptable scan */
    
      /* write summary of scan noise and position average */
      writeNoiseSummary( pNoise, &gbtIdl, nNoise, noiseList, &ave, &rms);

      if (noiseLimit > 0. && rms > noiseLimit && (verbosity > 0) ) {
	fprintf( stderr, "Flagging scan: %4ld, Int:%4ld Pol:%s; %12.4lf > %12.4lf\n",
		 gbtIdl.scan_num, gbtIdl.iIntegration, gbtIdl.pol_id,
		 rms, noiseLimit);
	flaggedLast = 2;
	continue;
      } /* end if a noise limit and this scan exceeds it */

      if (doTSys)  /* if putting T_{sys} in the first channel */
	gbtIdl.data[0] = tSysAve;

      /* if tsys exceeds maximum, then flag */      
      if (gbtIdl.tsys > maxTSys || gbtIdl.tsys < minTSys) {
	nTFlag++;
	gbtIdl.tsys = 0;
      }

      /* if integration was flagged, flag the next two */
      if (flaggedLast > 0) {
	flaggedLast--;
	if (verbosity > 1)
	  fprintf( stderr, 
		 "Skipping scan: %4ld, Int:%4ld Pol:%s; %12.4lf > %12.4lf\n",
		 gbtIdl.scan_num, gbtIdl.iIntegration, gbtIdl.pol_id,
		 rms, noiseLimit);
	continue;
      }
      else
	errMsg = putIdl( &gbtIdl);            /* save for write */

      if (errMsg) {
	if (verbosity > 1) {
	  fprintf( stderr, "Error Storing the keep structure\n");
	  fprintf( stderr, "Error Message: %s\n", errMsg);
	}
        break;
      }

      /* now find lines in the data */
      lineFind( &gbtIdl, lineSigma, doPrint, nChan/20, 19*nChan/20,
		&nLine, maxLines);

      memcpy( (char *)&lastIdl, (char *)&gbtIdl, sizeof(GBTIDL));
      tInt += gbtIdl.tintg;                 /* accumulate observing time */

      if (count < MAXSCANS-1)
	count++;
      else {
	/* this is always important enough to print out */
	/* this used to be limited to just verbosity > 1 case */
	fprintf( stderr, "Max Spectrum Count of %ld Exceeded\n", (long)MAXSCANS);
	fprintf( stderr, "Writing %ld Rows\n", count);
	break;
      }	

      aveRa = aveRa + gbtIdl.ra;
      aveDec = aveDec + gbtIdl.dec;
      /* if first value initialize coordinate range search */
      if (count <= 1) {
	minRa = maxRa = gbtIdl.ra;
	minDec = maxDec = gbtIdl.dec;
      }
      else {
	if (gbtIdl.ra < minRa)
	  minRa = gbtIdl.ra;
	if (gbtIdl.ra > maxRa)
	  maxRa = gbtIdl.ra;
	if (gbtIdl.dec < minDec)
	  minDec = gbtIdl.dec;
	if (gbtIdl.dec > maxDec)
	  maxDec = gbtIdl.dec;
      } /* end else trying to find the min and max ranges */

      if (gbtIdl.tsys  > 0) {             /* if a good observation */
      if (('R' == gbtIdl.pol_id[0]) ||    /* sum each polarizations */
	  ('X' == gbtIdl.pol_id[0]))  {   /* sum each polarizations */
	elXs[countX]   = gbtIdl.el*DEGREE;  /* keep els and Tsys for fit*/
	tSysXs[countX] = gbtIdl.tsys;
	if (nNoise > 0)
	  tRmsXs[countX] = rms;
	
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
	if (nNoise > 0)
	  tRmsYs[countY] = rms;
	if (countY == 0)
	  memcpy( (char *)&sumY, (char *)&gbtIdl, sizeof(GBTIDL));
	else {
	  for (i = 0; i < gbtIdl.data_points; i++) 
	    sumY.data[i] += gbtIdl.data[i];
	}
	countY++;
      } /* end else second sampler */

    } /* end for all rows */
    } /* end if good spectrum */
    } /* end for all tables */
  } /* end for all files */

  /* scanList is a list of milliseconds of MJD+UTC time, not scan number! */
  getScanList( maxScans, &nScans, scanList);
  getBeamList( maxScans, &nBeams, beamList);
  getStateList( maxScans, &nStates, stateList);

  if (nBeams > 1 && (verbosity > 2)) 
    fprintf( stderr, "Observation has %ld beams (%ld .. %ld)\n",
	     nBeams, beamList[0], beamList[nBeams-1]);

  if (nStates > 1 && (verbosity > 2)) 
    fprintf( stderr, "Observation has %ld states (%ld .. %ld)\n",
	     nStates, stateList[0], stateList[nStates-1]);

  if (errMsg && (verbosity > 1)) 
    fprintf( stderr, "Error writing data: %s\n", errMsg);

  if (countX <= 0 && countY <= 0) {
    fprintf( stderr, "No spectra, Exiting\n");
    return(-1);
  }
  else if (countX > 0 && countY <= 0) {
    if (verbosity > 1)
      fprintf( stderr, "Only one Polarization: %s\n", sumX.pol_id);
    memcpy( (char *)&sumY, (char *)&sumX, sizeof(GBTIDL));
  }
  else if (countY > 0 && countX <= 0) {
    if (verbosity > 1)
      fprintf( stderr, "Only one Polarization: %s\n", sumY.pol_id);
    memcpy( (char *)&sumX, (char *)&sumY, sizeof(GBTIDL));
  }
    
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
  else {                                 /* else exit without write */
    if (verbosity > 1)
      fprintf( stderr, "Map contained no spectra, exiting\n");
    return(-1);
  }

  /* copy parameters to the GO structure for writeSdfits file creation */
  strcpy( go.object, firstIdl.source);
  go.scan =  firstIdl.scan_num;
  dateObs2DMjd( firstIdl.date, &go.dateObs);
  go.ra2000 = aveRa*DEGREE;
  go.dec2000 = aveDec*DEGREE;
  /* re-use go polar motion values for x,y ranges */
  gbtPos.iersPMX = (maxRa - minRa)*DEGREE;
  if (gbtPos.iersPMX > PI) /* if covering more than 180 degrees, assume wrap */
    gbtPos.iersPMX = (TWOPI + minRa - maxRa)*DEGREE;
  gbtPos.iersPMY = (maxDec - minDec)*DEGREE;
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
	   
  fprintf( pTex, "The map contained %ld spectra from scans %ld to %ld.\n",
	   count, firstIdl.scan_num, lastIdl.scan_num);
  if (verbosity > 0)
    fprintf( stderr, 
	   "The map contained %ld spectra from scans %ld to %ld.\n",
	   count, firstIdl.scan_num, lastIdl.scan_num);

  if (!doXY) {/* if must replace X with R and Y with L polarization */
    if (isXyPol && (verbosity > 2))
      fprintf( stderr, 
	       "Forcing XX,YY=>RR,LL Stokes output to avoid AIPS troubles\n");
    fixPolarizationForAips();
  } /* end if replacing X,Y with R,L */

  freqMHz = gbtIdl.sky_freq * .000001;   /* convert center to MHz */
  if (doBeam) 
    computeBeamModel( go.ra2000, go.dec2000, freqMHz);

  if (doLineSummary)
    lineSummary( doLineSummary, nLine, nChan, maxLines, &bChan, &eChan);

  /* if triming out all but line region, then run through all spectra */
  if (doEndTrim) 
    lineTrim( bChan, eChan);
    
  errMsg = writeSdfits( fitsName, nScans, scanList, coordType, nPols);

  fprintf( pTex, "The region was observed on %s until %s.\n",
	   firstIdl.date, gbtIdl.date);
  fprintf( pTex, "Integration time was %.0lf seconds per spectrum.\n\n",
	   sumX.tintg);
  fprintf( pTex, "The coordinate system of the observation was %s.\n",
	   go.coordSys);
  rad2str( aveDec*DEGREE, "d.0", decStr);

  if (nTFlag > 0) {
    fprintf( pTex, 
	     "Flagged %ld spectra for T Sys out of range %9.3lf to %9.3lf\n", 
	     nTFlag, minTSys, maxTSys);
    if (verbosity > 2)
      fprintf( stderr, 
	     "Flagged %ld spectra for T Sys out of range %9.3lf to %9.3lf\n", 
	     nTFlag, minTSys, maxTSys);
  }

  if (coordType == GALACTIC) {
    rad2str( aveRa*DEGREE, "d.0", raStr);
    fprintf( pTex, 
	     "The average coordinates of these observations were %s,%s.\n", 
	     raStr, decStr);
  }
  else {
    rad2str( aveRa*DEGREE, "h.1", raStr);
    if (verbosity > 2)
      fprintf( stderr, "The average Ra, Dec of these observations were %s,%s.\n",
	   raStr, decStr);
  }

  for (i = 0; i < sumX.data_points; i++) {
    xs[i] = sumX.sky_freq + (((double)i - sumX.ref_ch)*sumX.delta_x) ;
    xs[i] *= 0.000001; /* convert to MHz */
    ys[i] = sumX.data[i];
    y2s[i] = sumY.data[i];
  }

  sprintf( title, "%s scans %ld:%ld", go.object, 
	   firstIdl.scan_num, lastIdl.scan_num);
  strcpy( title, fitsName);
  stripExtension( title); 

  sprintf( xLabel, "Frequency (MHz %s at %.2lf,%.2lf deg. %s)", 
	   go.velocityDef, aveRa, aveDec, go.coordSys);
  sprintf( yLabel, "Average Intensity (%s)", sumX.calibrate);

  chdir( summaryDir);
  if (countX > 0 && countY > 0) 
    /* plot data with frequency axis */
    quickPlot( plotName, doPlot, gnuCmds, title, xLabel, yLabel, 
	       sumX.data_points - 1, 
	       &xs[1], &ys[1], sumX.pol_id, &y2s[1], sumY.pol_id,
	     NULL, NULL, NULL, NULL);
  else if (countX > 0) 
    /* plot data with frequency axis */
    quickPlot( plotName, doPlot, gnuCmds, title, xLabel, yLabel, 
	       sumX.data_points -1, 
	       &xs[1], &ys[1], sumX.pol_id, NULL, NULL,
	       NULL, NULL, NULL, NULL);
  else if (countY > 0) 
    /* plot data with frequency axis */
    quickPlot( plotName, doPlot, gnuCmds, title, xLabel, yLabel, 
	       sumY.data_points  - 1, 
	       &xs[1], &y2s[1], sumY.pol_id, NULL, NULL,
	       NULL, NULL, NULL, NULL);

  if (countX > 0) {
    medianAveRmsMinMax( countX, elXs, &oMedian, &oAve, &oRms, &elMin, &elMax);

    if (verbosity > 2)
      fprintf( stderr, 
	     "%s Stats: med=%.3lf ave=%.3lf rms=%.3lf min=%.3lf max=%.3lf\n",
	     " El ", 
	     oMedian/DEGREE, oAve/DEGREE, oRms/DEGREE, elMin/DEGREE, 
	     elMax/DEGREE);

    medianAveRmsMinMax( countX, tSysXs, &oMedian, &oAve, &oRms, &oMin, &oMax);

    if (verbosity > 2)
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

    medianAveRmsMinMax( countX, tRmsXs, &oMedian, &oAve, &oRms, &oMin, &oMax);
    if (verbosity > 2)
      fprintf( stderr, 
	     "%s %s Stats: med=%.3lf ave=%.3lf rms=%.3lf min=%.3lf max=%.3lf\n",
	     "Trms", sumX.pol_id, oMedian, oAve, oRms, oMin, oMax);
  
  } /* if any X polarization data */

    medianAveRmsMinMax( countX, tSysXs, &oMedian, &oAve, &oRms, &oMin, &oMax);

  if (countY > 0) {  
    medianAveRmsMinMax( countY, elYs, &oMedian, &oAve, &oRms, &elMin, &elMax);

    medianAveRmsMinMax( countY, tSysYs, &oMedian, &oAve, &oRms, &oMin, &oMax);
 
    if (verbosity > 2)
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

    medianAveRmsMinMax( countY, tRmsYs, &oMedian, &oAve, &oRms, &oMin, &oMax);
    if (verbosity > 2)
      fprintf( stderr, 
	     "%s %s Stats: med=%.3lf ave=%.3lf rms=%.3lf min=%.3lf max=%.3lf\n",
	     "Trms", sumY.pol_id, oMedian, oAve, oRms, oMin, oMax);
  } /* end if any Y data */

  fprintf( pTex, 
	   "The region was observed in elevation range %.3lf to %.3lf d.\n",
	   elMin/DEGREE, elMax/DEGREE);
  if (verbosity > 2)
    fprintf( stderr, 
	   "The region was observed in elevation range %.3lf to %.3lf d.\n",
	   elMin/DEGREE, elMax/DEGREE);

  /* now add command line info to tex file */
  fprintf( pTex, "\nThe idlToSdfits command line arguments are:\n");  
  for (i = 0; i < argc; i++)
    fprintf( pTex, "%s ", argv[i]);
  fprintf( pTex, "\n");

  fclose( pTex);

  if (verbosity > 2)
    fprintf( stderr, "Wrote AIPS UV-FITS file: %s\n", fitsName);
  return(0);
} /* end of idlToSdfits() == main */
