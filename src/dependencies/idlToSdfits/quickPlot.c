/* File quickPlot.c, version 1.12, released  12/12/29 at 17:07:56 
   retrieved by SCCS 14/04/23 at 15:50:57     

%% plot function for pointers to IDL structures
:: utility
 
HISTORY:
  121229 GIL add labels to data file for later use
  090521 GIL if zero x range, then set xrange to average +/- 1
  070912 GIL increase line thickness
  070911 GIL deal with fonts while setting up png prints
  051201 GIL make output postscript file fit a page, delete files at last min.
  051118 GIL add a gnuCmds option
  051115 GIL create quickPlot.png, add option for spawning GV
  050511 GIL initial version based on plotIdl that does not include
             any references to external structures
  050429 GIL add option for x-axis plot Frequency or Channel number
  050419 GIL add file Name
  050414 GIL add frequency column
  050408 GIL add another digit to printout
  050407 GIL moved from mainWriteSdfits.c
 
DESCRIPTION:
Take an X axis array and up to 4 input data arrays with labels
and plots them. 
*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* internals */

#ifndef NULL
#define NULL  0
#endif
#ifndef EOS
#define EOS  0
#endif

char * quickPlot( char * plotName, long gv, 
		  char * gnuCmds, char * title, 
		  char * xLabel,  char * yLabel, 
		  long n,  double * xs, 
		  double * y1s, char * y1Label,
		  double * y2s, char * y2Label,
                  double * y3s, char * y3Label,
		  double * y4s, char * y4Label)
/* quickPlot() takes up to 4 data arrays and plots X vs up to 4 Ys */
/* by spawing gnuplot and ghostview.   Because the intermediate files are    */
/* deleted at start this program can only reliably be called once per        */
/* execution.  Returns NULL on OK                                            */
/* quickPlot() generates a text file for input to gnuplot and a sequence of  */
/* gnuplot commands.  The gnuplot function is spawned along with ghostview   */
/* to allow viewing of the output plot, with print capability                */
{ char fileName[256] = "quickPlot", gnuName[256] = "quickPlot",
    psName[256] = "quickPlot", sysStr[256] = "", tempStr[32] = "",
    pngName[200] = "quickPlot.png", thickLineCmd[256] = "";
  double minX = 0, maxX = 0; 
  FILE * pPlot = NULL, * pGnu = NULL;
  long i = 0, thickLines = 0;                 
 
  if ( plotName != NULL) {
    if (strlen( plotName) > 0) {
      strcpy( fileName, plotName);
      strcpy( gnuName, plotName);
      strcpy( psName, plotName);
      strcpy( pngName, plotName);
    }
  } /* if non-null infile Name() */

  strcat( fileName, ".txt");
  strcat( gnuName, ".gnu");
  strcat( psName, ".ps");
  strcat( pngName, ".png");

  /* remove files from previous execution */
  remove(fileName);

  if (xs == NULL || y1s == NULL)
    return("Null input pointers");

  if ((pPlot = fopen( fileName, "w")) == NULL) {
    fprintf( stderr, "quickPlot: Error opening plot file: %s\n", fileName);
    return("Error opening plot file");
  }
  else {
    fprintf( pPlot, "#QuickPlot Data file: %s\n", fileName);
    fprintf( pPlot, "#Title : %s\n", title);
    fprintf( pPlot, "#xLabel: %s\n", xLabel);
    fprintf( pPlot, "#yLabel: %s\n", yLabel);
    // now add labels to data columns
    strncpy( tempStr, xLabel, 9);
    tempStr[9] = EOS;
    fprintf( pPlot, "#   %9s ", tempStr);
    if (y1Label != NULL) {
      strncpy( tempStr, y1Label, 8);
      tempStr[8] = EOS;
      fprintf( pPlot, "%8s ", tempStr);
    }
    else 
      fprintf( pPlot, "%8s ", "             ");
    if (y2Label != NULL) {
      strncpy( tempStr, y2Label, 8);
      tempStr[8] = EOS;
      fprintf( pPlot, "%8s ", tempStr);
    }
    else 
      fprintf( pPlot, "%8s ", "             ");
    if (y3Label != NULL) {
      strncpy( tempStr, y3Label, 8);
      tempStr[8] = EOS;
      fprintf( pPlot, "%8s ", tempStr);
    }
    else 
      fprintf( pPlot, "%8s ", "             ");
    if (y4Label != NULL) {
      strncpy( tempStr, y4Label, 8);
      tempStr[8] = EOS;
      fprintf( pPlot, "%8s ", tempStr);
    }
    fprintf( pPlot, "\n");
  } /* end else output data file OK */

  thickLines = (n < 1000);
  if (thickLines) 
    strcpy(thickLineCmd,"lw 3");

  for (i = 0; i < n; i++) {   /* for all data points */
    fprintf( pPlot, "%4ld %8.4lf %8.4lf", i, xs[i], y1s[i]);
    if (y2s)
      fprintf( pPlot, " %8.4lf", y2s[i]);
    if (y3s)
      fprintf( pPlot, " %8.4lf", y3s[i]);
    if (y4s)
      fprintf( pPlot, " %8.4lf", y4s[i]);
    fprintf( pPlot, "\n");
  } /* end for all data points */

  fclose( pPlot);

  minX = maxX = xs[0];
  for (i = 1; i < n; i++) {  /* find the min, max x range for scale */
    if (xs[i] < minX) 
      minX = xs[i];
    else if (xs[i] > maxX) 
      maxX = xs[i];
  } /* end for all points */

  /* first plot png file, then plot postscript file */
  remove(gnuName);
  if ((pGnu = fopen( gnuName, "w")) == NULL) {
    fprintf( stderr, "quickPlot: Error opening gnu file\n");
    return("Error opening gnu file");
  }

  if (minX == maxX) {
    minX = minX - 1;
    maxX = maxX + 1;
  }
  fprintf( pGnu, "set terminal png medium \n");
  //  fprintf( pGnu, "set font 'Helvetica'\n");
  fprintf( pGnu, "set output \"%s\"\n", pngName);
  fprintf( pGnu, "set xrange [%lf:%lf]\n", minX, maxX);
  fprintf( pGnu, "set xlabel '%s'\n", xLabel);
  fprintf( pGnu, "set ylabel '%s'\n", yLabel);
  fprintf( pGnu, "set title  '%s'\n", title);
  fprintf( pGnu, "set data style lines\n");

  if (gnuCmds)                 /* if non-NULL cmds pointer */
    if (strlen (gnuCmds) > 0) {   /* if any gnuCmds */
      if (strstr ( gnuCmds, "terminal") == NULL) 
	fprintf( pGnu, "%s\n", gnuCmds); /* add to plot to over-ride */
    }

  fprintf( pGnu, "plot '%s' u 2:3 title \"%s\" %s", 
	   fileName, y1Label, thickLineCmd);
  if (y2s)
    fprintf( pGnu, ", '%s' u 2:4 title \"%s\" %s", 
	   fileName, y2Label, thickLineCmd);
  if (y3s)
    fprintf( pGnu, ", '%s' u 2:5 title \"%s\" %s", 
	     fileName, y3Label, thickLineCmd);
  if (y4s)
    fprintf( pGnu, ", '%s' u 2:6 title \"%s\" %s", 
	     fileName, y4Label, thickLineCmd);
  fprintf( pGnu, "\n");

  fclose( pGnu);

  /* remove old file, if present */
  remove(pngName);
  sprintf( sysStr, "gnuplot < %s \n",gnuName);
  system( sysStr);

  /* prepare to write new postscript file */
  remove(gnuName);
  if ((pGnu = fopen( gnuName, "w")) == NULL) {
    fprintf( stderr, "quickPlot: Error opening gnu file\n");
    return("Error opening gnu file");
  }

  fprintf( pGnu, "set terminal postscript color \"Helvetica\" 18\n");
  fprintf( pGnu, "set output \"%s\"\n", psName);
  fprintf( pGnu, "set xrange [%lf:%lf]\n", minX, maxX);
  fprintf( pGnu, "set xlabel '%s'\n", xLabel);
  fprintf( pGnu, "set ylabel '%s'\n", yLabel);
  fprintf( pGnu, "set title  '%s'\n", title);
  fprintf( pGnu, "set data style lines\n");
  if (n < 1000) {
    fprintf( pGnu, "set style line 1 linewidth 3\n");
    fprintf( pGnu, "set style line 2 linewidth 3\n");
    fprintf( pGnu, "set style line 3 linewidth 3\n");
    fprintf( pGnu, "set style line 4 linewidth 3\n");
  }


  if (gnuCmds)                 /* if non-NULL cmds pointer */
    if (strlen (gnuCmds) > 0)    /* if any gnuCmds */
      fprintf( pGnu, "%s\n", gnuCmds); /* add to plot to over-ride */

  fprintf( pGnu, "set size 1\n");           /* make ps file fit on page */
  fprintf( pGnu, "plot '%s' u 2:3 title \"%s\" %s", 
	   fileName, y1Label, thickLineCmd);
  if (y2s)
    fprintf( pGnu, ", '%s' u 2:4 title \"%s\" %s", 
	     fileName, y2Label, thickLineCmd);
  if (y3s)
    fprintf( pGnu, ", '%s' u 2:5 title \"%s\" %s", 
	     fileName, y3Label, thickLineCmd);
  if (y4s)
    fprintf( pGnu, ", '%s' u 2:6 title \"%s\" %s", 
	     fileName, y4Label, thickLineCmd);
  fprintf( pGnu, "\n");

  fclose( pGnu);
  remove(psName);                           /* now remove old plot file */
  sprintf( sysStr, "gnuplot < %s \n",gnuName);
  system( sysStr);

  if (gv) {                       /* optionally plot for user */
    sprintf( sysStr, "ghostview %s &\n", psName);
    system( sysStr);
  }

  sprintf( sysStr, "chmod 666 %s %s\n", pngName, psName);

  return(NULL);
} /* end of quickPlot() */
