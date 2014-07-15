/* File gbtScanInfo.h, version 1.3, released  04/04/20 at 16:55:57 
   retrieved by SCCS 14/04/23 at 15:50:46     

%% describe the GBT Scan FITS file header

HISTORY
040420 GIL add bank for spectrometer
020725 GIL add fitsVersion and mcVersion
020213 GIL initial version of generic GBT FITS file info

DESCRIPTION:
gbtScanInfo.h contains a description of the GBT FITS file headers
*/

#ifndef MAXKEYLEN
#define MAXKEYLEN 40
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
  char fitsVersion[MAXKEYLEN]; /* FITS version string */
  char mcVersion[MAXKEYLEN];   /* moniter and control FITS version string */
  char bank[MAXKEYLEN];        /* BANK = 'A'          (spectrometer only) */
};




