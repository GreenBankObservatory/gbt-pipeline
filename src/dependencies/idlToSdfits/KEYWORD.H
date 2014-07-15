/* File KEYWORD.H, version 1.3, released  09/05/04 at 08:43:25 
   retrieved by SCCS 14/04/23 at 15:50:41     

%% Definitions of modes for FITS keywords

:: Offline point FITS
 
HISTORY:
  030504 GIL - increase length of coment and keyword by 1
  950503 GIL - initial version
 
DESCRIPTION:
Include file for FITS keyword definitions.  Used for parsing FITS headers.
*/

/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
#define FITSUNKNOWN    0               /* bad fits card */
#define FITSSTRING     1               /* FITS string type */
#define FITSINTEGER    2               /* FITS long type */
#define FITSFLOAT      3               /* FITS double type */
#define FITSDATE       4               /* FITS string/date type */
#define FITSLOGICAL    5               /* FITS logical type */
#define FITSEND        6               /* FITS END card */
#define FITSCOMMENT    7               /* FITS comment card */
#define FITSBYTE       8               /* FITS byte data type */

#define LENFITSKEY     9
#define LENKEYSTR     72
#define LENCOMMENT    72

struct keyword {                       /* FITS Keyword structure */
  double dbl;                          /* integers are stored as doubles */
  long type;                           /* type index, one of serveral */
  char key[LENFITSKEY];
  char str[LENKEYSTR];
  char cmt[LENCOMMENT];
};

