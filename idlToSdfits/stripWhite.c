/*  @(#)stripWhite.c  version 1.4  created 95/11/24 08:12:50
    %%  function that removes whitespace from both ends of a string
    LANGUAGE: C
    ENVIRONMENT: Any
*/

/* includes */
#include <ctype.h>
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
{
    char *End;  /* pointer to the last non-\0 character in strng */

    /* strip off any leading whitespace */
    while (isspace (*strng) != 0)
	strcpy (strng, strng + 1);

    /* strip off any trailing whitespace
       scan through strng back to front, if not beyond beginning of strng 
       and character whitespace, turn character into terminator */
    End = strng + strlen (strng) - 1;
    while (End >= strng && isspace (*End) != 0)
	{
	*End = '\0';
	End--;
	}

    return (strng);
}
