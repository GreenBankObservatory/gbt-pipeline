 /* File findFitsTable.c, version 1.1, released  05/08/15 at 10:45:26 
   retrieved by SCCS 14/04/23 at 15:50:57     

%% program to load IDL (sdfits) data into an IDL strcuture
:: spectra mapping utility

HISTORY
050815 GIL initial version taken from readIdlFits.c

DESCRIPTON
findFitsTable() moves throught a FITS file until finding the hdu with
the required table name.
*/

#include "stdio.h"
#include "stdlib.h"
#include "string.h"
#include "math.h"
#include "time.h"
#include "fitsio.h"
#include "STDDEFS.H"
#include "MATHCNST.H"

/* externals */
extern char * stripWhite( char *);

/* internals */
#define MAXHDU  100
#define FITSBLOCKSIZE 2880

char * findFitsTable ( fitsfile * fptr, char * extension, int * hdu)
/* findFitsTable() finds the required fits table within a file */
/* this function assumes the fits file is open */
/* returns NULL if table found, else error message.  */
{ int startHdu = * hdu, status = 0, iHdu = 1, hduType = 0, i = 0;
  char comment[FLEN_CARD] = "", value[FLEN_CARD] = "";

  if (fptr == NULL)
    return("findFitsTable: Null input pointer");

  /* attempt to move to next HDU, until we get an EOF error */
  for (iHdu = startHdu; iHdu < MAXHDU; iHdu++) {
    fits_movabs_hdu(fptr, iHdu, &hduType, &status); 
    if (status)
      break;
    fits_read_keyword( fptr, "EXTNAME ", value, comment, &status);
    /* if an extension keyword */
    if (status == 0) {
      for (i = 0; i < strlen(value); i++)
	if (value[i] == '\'')
	  value[i] = ' ';
      stripWhite(value);
      /* if extension found */
      if (strcmp( value, extension) == 0) {
	*hdu = iHdu;
	return(NULL);
      }
    } /* end if read OK */
    status = 0;
  } /* end for all hdus from start to end */

  status = 0;
  /* so far not found, check that the it was not earlier in the file */
  /* attempt to move to next HDU, until we get an EOF error */
  for (iHdu = 2; iHdu < startHdu; iHdu++) {
    fits_movabs_hdu(fptr, iHdu, &hduType, &status); 
    if (status)
      break;
    fits_read_keyword( fptr, "EXTNAME ", value, comment, &status);
    /* if an extension keyword */
    if (status == 0) {
      for (i = 0; i < strlen(value); i++)
	if (value[i] == '\'')
	  value[i] = ' ';
      stripWhite(value);
      /* if extension found */
      if (strcmp( value, extension) == 0) {
	*hdu = iHdu;
	return(NULL);
      }
    } /* end if read OK */
    status = 0;
  } /* end for all hdus from start to end */
      
  return("EXTENSION not found");
} /* end of findFitsTable() */
