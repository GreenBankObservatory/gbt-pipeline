/* File gbtGo.h, version 1.2, released  04/04/13 at 16:48:45 
   retrieved by SCCS 14/04/23 at 15:50:44     

%% describe the GBT Observe parameters

HISTORY
020208 GIL gLat, gLon
020207 GIL add many more values
020206 GIL initial version

DESCRIPTION:
gbtGo.h contains a description of the GBT Observer parameters.
The GO file contains a description of the observation the Observer desired.
The other FITS files for the Scan contain the measured parameters, which
should be similar to the desired parameters, but the measured parameters
take prescidence, when they are available.
*/

#define GOSTRLENGTH 40

struct GOPARAMETERS {
  char object[GOSTRLENGTH];             /* source name */
  char projectId[GOSTRLENGTH];          /* project name */
  char observationId[GOSTRLENGTH];      /* observation name */
  char observer[GOSTRLENGTH];           /* observer name */
  long scan;                            /* integer scan number */
  long simulate;                        /* if true, not using telescope */
  char procName[GOSTRLENGTH];           /* observing proceedure */
  char procType[GOSTRLENGTH];           /* proceedure type */
  long procSeqn;                        /* scan number in a series */
  long procSize;                        /* number of scans in a series */
  char obsType[GOSTRLENGTH];            /* observing mode */
  char switchState[GOSTRLENGTH];        /* switching state */
  char switchSignal[GOSTRLENGTH];       /* switching signal(cal on/off etc)*/
  long lastOn;                          /* last On scan  position switching*/
  long lastOff;                         /* last Off scan position switching*/
  char coordSys[GOSTRLENGTH];           /* cordinate system (RADEC) */
  char raDecSys[GOSTRLENGTH];           /* system of RADEC coordianates */
  double equinox;                       /* equinox of ra,dec (1950, 2000) */
  double ra;                            /* ra (radians) of observation */
  double dec;                           /* dec (radians) of observation */
  double az;                            /* az (radians) of observation */
  double el;                            /* el (radians) of observation */
  double lst;                           /* lst (radians) of observation */
  double ra2000;                        /* J2000 ra of observation */
  double dec2000;                       /* J2000 dec of observation */
  double gLat;                          /* galactic Latitude of observation */
  double gLon;                          /* galactic Longitude of observation */
  double velocity;                      /* velocity of line in m/s */
  double restFreq;                      /* rest frequency of line (Hz) */
  char velocityDef[GOSTRLENGTH];        /* velocity definition */
  char gbtMcVer[GOSTRLENGTH];           /* code version */
  char fitsVer[GOSTRLENGTH];            /* fits format style version */
  double dateObs;                       /* double dMjd date */
  char timeSys[GOSTRLENGTH];            /* date system (ie UTC) */
  char telescope[GOSTRLENGTH];          /* telescope name (ie NRAO_GBT) */
};

#define SPBACKEND     0
#define ACSBACKEND    1
#define HOLOBACKEND   2
#define DCRBACKEND    3
#define BCPMBACKEND   4

