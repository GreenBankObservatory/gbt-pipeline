/* File gbtHolography.h, version 1.1, released  02/02/09 at 10:58:40 
   retrieved by SCCS 14/04/23 at 15:50:45     

%% describe the spectral processor fits data structure

HISTORY
020122 GIL file contains frequency resolution not rest frequency
011226 GIL initial version based on gbtSpectromter.h
DESCRIPTION:
gbtSP.h contains a description of the GBT Spectral Processor FITS files.
*/

#ifndef MAXKEYLEN
#define MAXKEYLEN 32
#endif

struct SCANINFO {
  double dMjd;                 /* date and time Modified Julian Days */
  char object[MAXKEYLEN];      /* OBJECT  = 'drift   ' (source) */      
  char projId[MAXKEYLEN];      /* PROJID  = '01may15 ' (project Id) */
  char obsId[MAXKEYLEN];       /* OBSID   = 'test    ' (observation Id) */
  long scanNumber;             /* scan number */
  char manager[MAXKEYLEN];     /* MANAGER = 'BankAMgr' (Device Manager) */
  long simulate;               /* SIMULATE= 'T       ' (simulate mode?) */     
  char observer[MAXKEYLEN];    /* OBSERVER= 'Jansky  ' (Who had this idea) */
  char operator[MAXKEYLEN];    /* OPERATOR= 'Nathan  ' (Who carried it out) */
};

#define MAXRECEIVERS 32

struct ASPRECEIVER {
  long id;                     /* indentifing index */
  char taper[MAXKEYLEN];       /* type of bandwidth taper */
  double obsFreq;              /* observing frequency Hz */
  double ifFreq;               /* if Frequency Hz */
  double freqResolution;       /* frequency resolution Hz */
  double bandWidth;            /* IF bandwidth Hz */
  double tCal;                 /* noise diode equivalent temp K */
  double totalPower;           /* total power level */
  double fastTime;             /* seconds */
  double slowTime;             /* seconds */
  double clipTime;             /* seconds */
  double threshold;            /* seconds */
  long   synthesizerCode;      /* index */
  long   overCode;             /* index */
  long   modeFlag;             /* index */
  long   ifSynthesizerCode;    /* index */
  long   taperOffCode;         /* index */
  long   rfiCode;              /* index */
  long   clockCode;            /* index */
  long   ifLoCode;             /* index */
  long   ifSideband;           /* index */
  long   rfSideband;           /* index */
};

struct SPRECEIVER {
  long nReceivers;             /* number of receivers= number rows = NAXIS2 */
  struct ASPRECEIVER receivers[MAXRECEIVERS]; /* individual samples */  
};
