/* File plotIdl.c, version 1.7, released  05/10/20 at 09:18:36 
   retrieved by SCCS 14/04/23 at 15:50:49     

%% plot function for pointers to IDL structures
:: utility
 
HISTORY:
  050829 GIL add velocity frame to Freq axis
  050609 GIL print some scan info at beginning of plot file
  050429 GIL add option for x-axis plot Frequency or Channel number
  050419 GIL add file Name
  050414 GIL add frequency column
  050408 GIL add another digit to printout
  050407 GIL moved from mainWriteSdfits.c
 
DESCRIPTION:
Take up to 4 input idl structure pointers, generate a plot input files
and spawn a viewer.
*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "math.h"
#include "MATHCNST.H"
#include "STDDEFS.H"
#include "gbtIdl.h"

/* externals */
extern char * rad2str( double, char *, char *);
extern char * mjd2str( long, char *);
extern long today2mjd();

/* internals */
char * plotIdl( char * inFileName, long plotFreq,
		GBTIDL * idl, char * idlLabel,
		GBTIDL * idl2, char * idlLabel2,
		GBTIDL * idl3, char * idlLabel3,
		GBTIDL * idl4, char * idlLabel4,
		char * calType)
/* plotIdl() takes up to 4 data structures and plots intensity versus channel*/
/* by spawing gnuplot and ghostview.   Because the intermediate files are    */
/* deleted at start this program can only reliably be called once per        */
/* execution.  Returns NULL on OK                                            */
/* plotIdl() generates a text file for input to gnuplot and a sequence of    */
/* gnuplot commands.  The gnuplot function is spawned along with ghostview   */
/* to allow viewing of the output plot, with print capability                */
{ char fileName[256] = "plotIdl", gnuName[256] = "plotIdl",
    psName[256] = "plotIdl", sysStr[256] = "", raStr[32] = "", 
    decStr[32] = "";
  FILE * pPlot = NULL, * pGnu = NULL;
  long i = 0, plotC = 1, mjd = today2mjd(); /* plot column 1 = chan, 2 = freq*/
  double fr0 = idl->sky_freq, ch0 = idl->ref_ch-1., df = idl->delta_x, f = 0;
 
  if ( inFileName != NULL) {
    if (strlen( inFileName) > 0) {
      strcpy( fileName, inFileName);
      strcpy( gnuName, inFileName);
      strcpy( psName, inFileName);
    }
  } /* if non-null infile Name() */

  if (plotFreq)                /* if plotting freq, use 2nd column */
    plotC = 2;
  strcat( fileName, ".txt");
  strcat( gnuName, ".gnu");
  strcat( psName, ".ps");

  /* remove files from previous execution */
  remove(fileName);
  remove(gnuName);
  remove(psName);

  if (idl == NULL)
    return("Null input pointers");

  if ((pPlot = fopen( fileName, "w")) == NULL) {
    fprintf( stderr, "plotIdl: Error opening plot file: %s\n", fileName);
    return("Error opening plot file");
  }

  mjd2str( mjd, raStr);
  fprintf( pPlot,"# plotIdl execution on %s\n", raStr);
  fprintf( pPlot,"# OBJECT  = '%s'\n", idl->source);
  fprintf( pPlot,"# PROJECT = '%s'\n", idl->history);
  fprintf( pPlot,"# DATE    = '%s'\n", idl->date);
  fprintf( pPlot,"# TYPE    = '%s'\n", idl->scan_type);
  fprintf( pPlot,"# POLID   = '%s'\n", idl->pol_id);
  rad2str( idl->ra, "h.1", raStr);
  fprintf( pPlot,"# RA      =  %s\n", raStr);
  rad2str( idl->dec, "d.0", decStr);
  fprintf( pPlot,"# DEC     = %s\n", decStr);
  fprintf( pPlot,"# NLAGS   = %ld\n",  idl->data_points);
  fprintf( pPlot,"# BANDWIDH= %f\n",  idl->bw);

  for (i = 0; i < idl->data_points; i++) {   /* for all data points */
    f = (fr0 + (((double)i-ch0)*df)) * 1.E-6;
    fprintf( pPlot, "%4ld %12.5lf %8.4lf", i, f, idl->data[i]);
    if (idl2)
      fprintf( pPlot, " %8.4lf", idl2->data[i]);
    if (idl3)
      fprintf( pPlot, " %8.4lf", idl3->data[i]);
    if (idl4)
      fprintf( pPlot, " %8.4lf", idl4->data[i]);
    fprintf( pPlot, "\n");
  } /* end for all data points */

  fclose( pPlot);

  if ((pGnu = fopen( gnuName, "w")) == NULL) {
    fprintf( stderr, "plotIdl: Error opening gnu file\n");
    return("Error opening gnu file");
  }
  rad2str( idl->ra*DEGREE, "h.1", raStr);
  rad2str( idl->dec*DEGREE, "d.0", decStr);
    if (plotC == 1)
      fprintf( pGnu, "set xlabel 'Channel Number (Position %s,%8.3lfd)'\n", 
	       raStr, idl->dec);
    else {
      if (idl->vel_def != NULL) 
	fprintf( pGnu, 
		 "set xlabel 'Frequency (MHz %s at Position %s,%8.3lfd)'\n", 
		 idl->vel_def, raStr, idl->dec);
      else
	fprintf( pGnu, 
		 "set xlabel 'Frequency (MHz at Position %s,%8.3lfd)'\n", 
		 raStr, idl->dec);
  }

  if (plotC == 1)
    fprintf( pGnu, "set xrange [1:%ld]\n", idl->data_points); 
  else
    fprintf( pGnu, "set xrange [%lf:%lf]\n", 
	     (fr0+((10.-ch0)*df))*1.E-6, 
	     (fr0+(((idl->data_points-10.)-ch0)*df))*1.E-6); 
  fprintf( pGnu, "set ylabel 'Intensity (K)'\n");
  fprintf( pGnu, "set title  '%s Calibrated Spectra'\n", idl->source);
  fprintf( pGnu, "set terminal postscript color \"Helvetica\" 15\n");
  fprintf( pGnu, "set data style lines\n");
  fprintf( pGnu, "set output \"%s\"\n", psName);
  fprintf( pGnu, "plot '%s' u %ld:3 title \"%s\"", fileName, plotC, idlLabel);
  if (idl2)
    fprintf( pGnu, ", '%s' u %ld:4 title \"%s\"", fileName, plotC, idlLabel2);
  if (idl3)
    fprintf( pGnu, ", '%s' u %ld:5 title \"%s\"", fileName, plotC, idlLabel3);
  if (idl4)
    fprintf( pGnu, ", '%s' u %ld:6 title \"%s\"", fileName, plotC, idlLabel4);
  fprintf( pGnu, "\n");
    
  fclose( pGnu);

  sprintf( sysStr, "gnuplot < %s ; ghostview %s &\n",gnuName, psName);
  system( sysStr);

  return(NULL);
} /* end of plotIdl() */
