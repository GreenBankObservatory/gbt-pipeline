/* File gbtDcr.h, version 1.1, released  02/02/13 at 11:17:23 
   retrieved by SCCS 14/04/23 at 15:50:43     

%% describe the dcr fits data structure

HISTORY
020213 GIL dcr initial version

DESCRIPTION:
gbtDcr.h contains a description of the GBT Dcr FITS files.
*/

#ifndef MAXDCRDATA
#define MAXDCRDATA 16
#endif

struct DCR {
  double dmjd;                 /* date and time */
  long ifFlag;   
  long subScan;   
  long shape[2];              /* arrangement of counts data */
  long counts[MAXDCRDATA];    /* signal intesity counts */
};

