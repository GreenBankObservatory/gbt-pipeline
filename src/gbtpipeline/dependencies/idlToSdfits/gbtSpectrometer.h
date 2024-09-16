/* File gbtSpectrometer.h, version 1.12, released  05/04/08 at 08:11:59 
   retrieved by SCCS 14/04/23 at 15:50:47     

%% describe the spectrometer fits data structure

HISTORY
050405 GIL add counts of number of different states
030311 GIL add counts of number of different states
020405 GIL add ACT_STATE table
020321 GIL update for PORT table changes
011210 GIL move mode to spectrometer structure, add PORT
011018 GIL only work with one integration
010814 GIL increase MAXDATASIZE
010621 GIL add MAGIC and MAXDATASIZE
010620 GIL add observer and operator to SPECTROMETER
010516 GIL initial version
DESCRIPTION:
gbtSpectrometer.h contains a description of the GBT Spectrometer FITS files.

The structures below are intended to support both very wide spectra, 
nlags <= 262144 and/or large number of integrations.  
However it is not possible to do both at once, and a book keeping
scheme is implimented to keep track of the maximum data to be processed.

The scheme is implimented by use of pointers to data structures
so that these may be filled and cleared as needed.
*/

#ifndef MAXKEYLEN 
#define MAXKEYLEN 40
#endif

struct SPECTROMETER {
  double dMjd;                 /* date and time Modified Julian Days */
  char object[MAXKEYLEN];      /* OBJECT  = 'drift   ' (source) */      
  char projId[MAXKEYLEN];      /* PROJID  = '01may15 ' (project Id) */
  char obsId[MAXKEYLEN];       /* OBSID   = 'test    ' (observation Id) */
  long scanNumber;             /* scan number */
  char manager[MAXKEYLEN];     /* MANAGER = 'BankAMgr' (Device Manager) */
  long simulate;               /* SIMULATE= 'T       ' (simulate mode?) */     
  char observer[MAXKEYLEN];    /* OBSERVER= 'Jansky  ' (Who had this idea) */
  char operator[MAXKEYLEN];    /* OPERATOR= 'Nathan  ' (Who carried it out) */
  char mode[MAXKEYLEN];        /* MODE    = '1W2-0XY-800'  */
  char bank[MAXKEYLEN];        /* BANK    = 'A'  */
};

struct ASAMPLER {
  long samplerA;               /* sampler number 0-7 High speed, 0-31 low */ 
  long samplerB;               /* sampler number == samplerA for auto-corr */
  long level;                  /* 3 or 9 levels of sampler */
  double speed;                /* sampler speed, 100E6 or 1600E6 Hz */
  double bandWidth;            /* bandwidth(Hz) 800E6, 200E6 50E6, or 12.5E6 */
};

#define MAXSAMPLERS 32

struct SAMPLER {
  long nSamplers;              /* number of samplers = number rows = NAXIS2 */
  struct ASAMPLER samplers[MAXSAMPLERS]; /* individual samples */  
  char bank[MAXKEYLEN];        /* BANK    = 'A       '  Spectrometer Bank  */
  char quadrant[MAXKEYLEN];    /* QUADRANT= '1       '  Quadrants in Bank  */
  long fft;                    /* FFT     = 0  == NO FFT done, else true */
  long nLags;                  /* NLAGS   = 2048     lags in correlation */
  char mode[MAXKEYLEN];        /* MODE    = '1W2-0XY-800'  */
  long selfTest;               /* SELFTEST= 0 == Not selftest, else true */
  long nyquist;                /* NYQUIST = 0 == Not twice nyquist else true */
  long polarize;               /* POLARIZE= 'CROSS' == TRUE, else flase */
  char samplersUsed[MAXKEYLEN];/* SAMPUSED= '0 1     ' index to sampler used */
};

struct APORT {
  char bank[MAXKEYLEN];        /* band letter (A,B,C or D) */ 
  long port;                   /* port index, must match IF FITS files */
  double attenSet;             /* attenuation */
  double measuredPower;        /* power level counts */
  double ratio;                /* near 1 +/- .3 for optimum 3, 9 levels */
  long level;                  /* number of sampler leves (3 or 9) */  
  double speed;                /* sampler speed 1E10 or 8E11 (Hz) */
  double bandWidth;            /* bandwidth 50, 12.5, 200 or 800 x 10E6 Hz */
  double freqStart;            /* spectrometer IF frequency start (Hz) */
  double freqStop;             /* spectrometer IF frequency stop (Hz) */
};

struct SPECPORT {
  long nPorts;              /* number of PORTS */
  struct APORT ports[MAXSAMPLERS];/* individual port */  
};

struct AIPHASE {               /* define one internal switching phase */
  double blankTime;            /* blanking time at start of phase (sec) */
  double phaseTime;            /* time in this phase (sec) include blank */
  double phaseStart;           /* start time relative to total phase cycle */
  long   sigRef;               /* signal/ref state for this phase */
  long   cal;                  /* cal on/off state for this phase */
}; /* end of struct AIPHASE */

#define MAXIPHASES 16

struct IPHASE {                /* define internal switching signal phases */
  long nPhase;                 /* number of internal states = NUMPHASE */
  struct AIPHASE phases[MAXIPHASES];   /* description of each phase */
  double switchPeriod;         /* SWPERIOD=4.000E+00 Total Switching period*/
  char master[MAXKEYLEN];      /* MASTER  = 'Spectrometer' Signals Master */
}; /* end of struct IPHASE */

struct ASTATE {
  long iSigRef ;               /* internal sig/ref value for this state */
  long iASigRef;               /* internal advance sig ref for this state */
  long iCal    ;               /* internal cal for this state */
  long eSigRef ;               /* external sig/ref value */
  long eASigRef;               /* external advance sig/ref value */
  long eCal    ;               /* external cal */
}; /* end of struct ASTATE */

#define MAXSTATES 64

struct STATE {
  long nStates;                /* number of states == NAXIS2 */
  long nISigRef ;               /* internal sig/ref value for this state */
  long nIASigRef;               /* internal advance sig ref for this state */
  long nICal    ;               /* internal cal for this state */
  long nESigRef ;               /* external sig/ref value */
  long nEASigRef;               /* external advance sig/ref value */
  long nECal    ;               /* external cal */
  struct ASTATE states[MAXSTATES];    /* description of each state */
}; /* end of STATE structure */

struct ASPECDATA { 
  long nLags;
  long nSamplers;
  long nStates;
  long iIntegration;           /* index to which integration */
  double dMjd;                 /* date/time of integration mid point MJDs */
                               /* duration of integration (seconds) */
  double intDuration[MAXSTATES*MAXSAMPLERS]; 
  float * data;                /* pointer to data array */
}; /* end of struct ASPECDATA */

#define MAXINTEGRATIONS 3600   /* max number of integrations per scan */

struct SPECDATA { 
  long nIntegrations;          /* number of integrations == NAXIS2 == rows */
  long integrationSize;        /* number of floats in one integration */
  long maxIntegrations;        /* number of integrations that may be filled */
  long maxData;                /* maximum allowed data to be stored at once */
  struct ASPECDATA integration;
  double crpix1;               /* CRPIX1= 1E+00 Reference Pixel of Lag data */
  double crval1;               /* CRVAL1= 0E+00 Reference Value of Ref. Pixel*/
  double cdelt1;               /* CDELT1= 6.25E-10 Time between Lags (sec) */
  long intCycles;              /* INTEGCYC=6104 / Memory Cycles Per Int. */
  long intSwitchCycles;        /* Number of Switching Periods Per Integration*/
}; /* end of struct SPECDATA */

#define MAGIC      -99999.
#define MAXDATASIZE   (16*65536)
