/*  @(#)stripWhite.c  version 1.4  created 95/11/24 08:12:50
    %%  function that removes whitespace from both ends of a string
    LANGUAGE: C
    ENVIRONMENT: Any
HISTORY
121015 GIL strcpy formally does not allow copy in the same string

DESCRIPTION:
stripWhite() removes blanks from both ends of a string
*/

/* includes */
#include <ctype.h>
#include <string.h>
#include "vlb.h"

/******************************************************************************
*/
char *stripWhite	/* remove white space from both ends of string */
    (
    char *strng		/* input and output string */
    )
/*
 * RETURNS original input string pointer
 */
{   char *Begin = strng, *Start = strng;
    char *End;  /* pointer to the last non-\0 character in strng */

    /* strip off any leading whitespace */
    while (isspace (*Begin) != 0)
      Begin++;

    /* strip off any trailing whitespace
       scan through strng back to front, if not beyond beginning of strng 
       and character whitespace, turn character into terminator */
    End = Begin + strlen (Begin) - 1;
    while (End >= strng && isspace (*End) != 0)
	{
	End--;
	}

    while (Begin <= End) {
      *Start = *Begin;
      Start++;
      Begin++;
    }
    *Start = '\0';

    return (strng);
} // end of stripWhite()
