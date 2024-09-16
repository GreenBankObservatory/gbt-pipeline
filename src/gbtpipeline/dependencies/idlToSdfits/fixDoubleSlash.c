/* File fixDoubleSlash.c, version 1.2, released  04/05/12 at 15:06:01 
   retrieved by SCCS 14/04/23 at 15:51:03     

%% string utility function to replace // by / for merged directory names
:: string utility

HISTORY
040512 GIL also strips out any types of white space, 'tab', formfeed, etc
040422 GIL function to replace // by / in file names

DESCRIPTION:
fixDoubleSlash() modifies an input string, replacing // with / in the string
*/
#include "stdio.h"
#include "string.h"
#include <ctype.h>
#include "STDDEFS.H"

char * fixDoubleSlash( char * fileName) 
{ long i = 0, j = 0, n = strlen( fileName);

  for (i = 0; i < n; i++) {
    if (isspace(fileName[i])) {    /* skip internal blanks */
      /* do nothing */
    }
    else if (fileName[i] != '/') { /* if not a slash, just copy */
      fileName[j] = fileName[i];
      j++;
    }
    else if (i < n - 1) {          /* is a slash, if not at end of string? */
      if (fileName[i+1] != '/') {  /* then if next not a slash, copy */
	fileName[j] = fileName[i];
	j++;
      }                            /* else two // in a row, do not copy first*/
    }
    else {                         /* copy last character no matter what */
      fileName[j] = fileName[i];
      j++;
    } 
  } /* end for all characters */
  fileName[j] = EOS;               /* terminate string */
  return (NULL);
} /* end of fixDoubleSlash() */
