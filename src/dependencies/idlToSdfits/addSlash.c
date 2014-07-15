/* File addSlash.c, version 1.1, released  05/01/31 at 11:21:50 
   retrieved by SCCS 14/04/23 at 15:51:04     

%% write an AIPS single dish fits file from a idl structure
:: TEST C program
 
HISTORY:
  050126 GIL initial version

DESCRIPTION:
Utility to add a trailing slash to a directory name, if not present
*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* externals */
extern char * stripWhite( char *);

/* internals */

char * addSlash( char * directoryName)
{
  if (directoryName == NULL) {
    fprintf( stderr, "addSlash: NULL directory Name\n");
    return("NULL directory Name");
  }

  stripWhite( directoryName);

  if (directoryName[ strlen( directoryName)-1] != '/')
    strcat( directoryName, "/");

  return(NULL);
} /* end of addSlash() */
