/* File gbtLo.h, version 1.1, released  02/03/28 at 16:33:34 
   retrieved by SCCS 14/04/23 at 15:50:45     

%% describe the if settings, sky frequencies and bandwidths for each band

HISTORY
020328 GIL initial version based on gbtIf.h

DESCRIPTION:
gbtLo.h contains a description of the GBT Lo FITS files
*/

#define LONAMELEN         16

struct LOTABLE {
  double dMjd;                 /* date Modified julian days */
  double ra;                   /* right ascension degrees */
  double dec;                  /* declination degrees */
  double loFreq;               /* LO frequency (Hz)*/
  double vFrame;               /* velocity in the reference frame (m/s) */
  double rVSys;              /* reference frame velocity (m/s) */
}; /* LOTABLE description structure */

struct LOSOUVEL {
  double dMjd;                 /* date Modified julian days (DMJD) */
  double velocity;             /* source velocity  (m/s VELOCITY) */
  double vDot;                 /* source accelleration (m/s/s VDOT) */
  double vDotDot;              /* source jerk  (m/s/s/s VDOTDOT) */
}; /* LOSOUVEL description structure */

struct LOSTATE {
  double blankTime;            /* blank time per phase (seconds BLANKTIM) */
  double phaseTime;            /* phase start time (fraction PHSESTRT) */
  long   sigRefState;          /* if 0, sig else ref (SIGREF) */
  long   calState;             /* if 0, cal off, else cal On (CAL) */
  double frequencyOffset;      /* frequency offset (Hz FREQOFF) */
}; /* LOSTATE description structure */

struct LO {
  double restFreq;             /* rest frequency of line (Hz RESTFREQ) */
  double ifFreq;               /* if center frequency to IFRACK (Hz IFFREQ) */
  double loOffset;             /* lo offset due to receiver (Hz, LOOFFSET) */
  double loMult;               /* lo multipier factor (LOMULT) */
  double requiredTolerance;    /* frequency accuracy (Hz REQDPTOL) */
  double powerLevel;           /* power level (dBm POWERLVL) */
  long   upperSideBand;        /* true if side band */
  long   testTone;             /* true testtone source */
  long   nLoStates;            /* number of lo states */
  struct LOSTATE * states;     /* lo state table */
  long   nLoVelocities;        /* number of lo source velocities */
  struct LOSOUVEL * sources;   /* source velocity table */
  long   nLoFreqs;             /* number of lo frequencies */
  struct LOTABLE  * freqs;     /* lo frequency table */
}; /* end of LO structure */
