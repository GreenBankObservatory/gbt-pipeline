/* File printerror.c, version 1.1, released  04/12/29 at 16:26:09 
   retrieved by SCCS 14/04/23 at 15:50:52     

%% prints fits io errors
:: C program
 
HISTORY:
  041229 GIL initial version
 
DESCRIPTION:
prints fits io errors
*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "fitsio.h"


void printerror( int status)
{
    /*****************************************************/
    /* Print out cfitsio error messages and exit program */
    /*****************************************************/

    char status_str[FLEN_STATUS], errmsg[FLEN_ERRMSG];
  
    if (status)
      fprintf(stderr, "\n*** Error occurred during program execution ***\n");

    fits_get_errstatus(status, status_str);   /* get the error description */
    fprintf(stderr, "\nstatus = %d: %s\n", status, status_str);

    /* get first message; null if stack is empty */
    if ( fits_read_errmsg(errmsg) ) 
    {
         fprintf(stderr, "\nError message stack:\n");
         fprintf(stderr, " %s\n", errmsg);

         while ( fits_read_errmsg(errmsg) )  /* get remaining messages */
             fprintf(stderr, " %s\n", errmsg);
    }

    exit( status );       /* terminate the program, returning error status */
} /* end of printerror() */
