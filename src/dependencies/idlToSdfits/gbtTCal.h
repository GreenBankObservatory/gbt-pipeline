/* File gbtTCal.h, version 1.6, released  03/04/08 at 17:50:02 
   retrieved by SCCS 14/04/23 at 15:50:45     

%% describe the reciever TCal measurements

HISTORY
030403 GIL add receptor<=channel
011218 GIL add channel<=feed
010509 GIL define can on/off parameters
010315 GIL initial version based on gbtAntenna.h

DESCRIPTION:
gbtTCal.h contains a description of the GBT TCal FITS files
*/
#define TCALMAXPOLARIZE 32

struct TCAL {
  double frequency; /* center frequency of measurement (Hz) */
  double bandwidth; /* bandwidth of measurement (Hz) */
  double rxTemp;    /* receiver temp (K) */
  double loCalTemp; /* low Cal Temp (K) */
  double hiCalTemp; /* high Cal Temp (K) */
  char   polarize[TCALMAXPOLARIZE]; /* polarization types of Stokes */
  char   receptor[TCALMAXPOLARIZE];  /* add feed+polarization name */
  long   beam;      /* index to feed of the reciever */
};

#define MAXTCALNAME 128

struct TCALMEASURE {            /* parameters of tcal measurement */
  char engineer[MAXTCALNAME];   /* who designed device */
  char tech[MAXTCALNAME];       /* who made device */
  char receiver[MAXTCALNAME];   /* reciever name */
  char receptor[MAXTCALNAME];   /* feed, polarization combination name */
  double dmjd;                  /* date of measurement Modified Julian Day */
  double lowFreq;               /* receiver low frequency cut off (Hz) */
  double highFreq;              /* receiver high frequency cut off (Hz) */
};

#define CALOFF  0
#define CALON   1
#define REFERENCE 0
#define SIGNAL    1

