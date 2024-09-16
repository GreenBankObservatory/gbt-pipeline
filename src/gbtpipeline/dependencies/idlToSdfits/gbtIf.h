/* File gbtIf.h, version 1.7, released  04/04/12 at 14:33:53 
   retrieved by SCCS 14/04/23 at 15:50:43     

%% describe the if settings, sky frequencies and bandwidths for each band

HISTORY
040422 GIL support TRANSFORMS
021209 GIL rename FEED to FEEDINDEX
021206 GIL add defines for SRFEED1 and SRFEED2
020328 GIL add defines for SFF
011218 GIL add defines for FITS3.4.0
010309 GIL initial version based on gbtAnttenna

DESCRIPTION:
gbtIf.h contains a description of the GBT If FITS files
*/

#define IFNAMELEN 40
#define NIFKEYS  26                  /* number of IF table keywords */
#define BACKEND        0             /* indices of critical ones */
#define BANK           1             
#define CHANNEL        2             /* == FITS3.4.0 PORT */
#define RECEIVER       3
#define FEEDINDEX      4             /* == FITS3.4.0 RECEPTOR, was FEED */
#define SIDEBAND       5
#define POLARIZATION   6             
#define SKYCENTERFREQ  8             /* indices of critical ones */
#define IFCENTERFREQ   7
#define BANDWIDTH      9
#define SFFMULTIPLIER 14
#define SFFSIDEBAND   15
#define SFFOFFSET     16
#define TRANSFORMS    18             /* long string */
#define PORT          19             /* new in FITS3.4.0 */
#define RECEPTOR      20
#define LOCIRCUIT     21
#define LOCOMPONENT   22
#define SRFEED1       23
#define SRFEED2       24
#define HIGH_CAL      25

struct IF {
  char backend[IFNAMELEN];     /* backend connected to this IF chain */
  char bank[IFNAMELEN];        /* subsection of backend connected to this IF */
  long channel;                /* data input port of backend */
  char receiver[IFNAMELEN];    /* Front end connected to IF chain */
  char feed[IFNAMELEN];        /* portion of front end connnected to IF */
  char sideband[IFNAMELEN];    /* portion of IF frequency range connected */
  char polarize[IFNAMELEN];    /* polarization of IF */
  float ifCenterFreq;          /* center frequency in IF rack input port (Hz)*/
  float skyCenterFreq;         /* sky center frequency at center IF (Hz) */
  float bandwidth;             /* frequency range FW around center frequency */
  float testToneIf;            /* injected  test tone IF frequency (Hz) */
  char   circuit[IFNAMELEN];   /* circuit producing test tone */
  char   component[IFNAMELEN]; /* sub-component of circuit producing tone */
  double sFMultiplier;         /* sky frequency multiplier */
  double sFSideband;           /* sky frequency sideband */
  double sFOffset;             /* sky frequency offset */
  long   transformCount;       /* transform Count */
  char   transforms[IFNAMELEN];/* transform string */
  char   loCircuit[IFNAMELEN]; /* LO input string (LO1A or LO1B) */
  char   loComponent[IFNAMELEN];/* LO input string (synthesizer) */
  long   srFeed1;              /* Switch Feed 1 */
  long   srFeed2;              /* Switch Feed 2 */
  long   highCal;              /* If true, High Receiver Cal selected */
  long   feedIndex;            /* Feed Number for Multi-Feed receivers (1-N) */
}; /* IF description structure */
