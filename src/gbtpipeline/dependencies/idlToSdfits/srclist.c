/* File srclist.c, version 1.1, released  97/12/05 at 16:25:03 
   retrieved by SCCS 14/04/23 at 15:51:01     

%% function to search list for minimum match of string

:: string utility 
HISTORY:
971205 GIL initial version based on @(#)srclist.c  
           version 1.3  created 95/11/24 08:10:52; initialized match to false
*/

/* includes */
#include "ctype.h"
#include "string.h"

/*******************************************************************************
*/
int srclist		/* search list for string */
    (
    char *pstring,	/* search for this string in list 
			   ('\0' or ' ' terminated) */
    char *list,		/* list to be searched ('\0' terminated) */
    int strsize		/* number of characters in each list element */
    )
/*
 * RETURNS matching string displacement in list, or -1 if no match found
 *
 * Minimum match means that matching is done to the end of the string to be
 * matched only.  Any further characters in the list element are ignored.  
 * For example, "EX" minimum matches with "EXIT", "EXACT", and "EXPLAIN" 
 * (making this minimum match ambiguous).  Matching "EX" with "EX" is an 
 * exact match.
 *
 * 'list' is a character array composed of string elements to be matched, 
 * each 'strsize' long.  Strings should be right justified within each 
 * element (leading blanks are ignored).  Leading and trailing blanks in 
 * 'string' are ignored.
 *
 * If a single minimum match or an exact match is found the matching 
 * element displacement is returned (0 to number of elements in list - 1).  
 * If no match or multiple matches are found -1 is returned.
 */
{
    char *pelement;
    char *ptr;
    char *plist;
    int match = -1, matches = 0;

    /* skip over any leading white space */
    while (isspace (*pstring))
        pstring++;

    /* search through list an element at a time, always search entire 
    list for exact match (even though have multiple min matches) */
    for (pelement = list; *pelement; pelement += strsize)
	{
	/* plist points to first non-blank list element character */
	plist = pelement;
	while (*plist == ' ')
	    plist++;

	/* compare strings until terminator 
	    or non-matching characters are found */
	ptr = pstring;	       /* pointer to 1st non-blank in string */
	while (*ptr != '\0' && *ptr != ' ' && *ptr == *plist)
	    {
	    ptr++;
	    plist++;
	    }

	/* check for minimum match (has end of string been reached?) */
	if (*ptr == ' ' || *ptr == '\0')
	    {
	    /* save matching element displacement and bump match count */
	    match = (pelement - list) / strsize;
	    matches++;

	    /* check for exact match (has end of list element been reached?) */
	    if (plist - pelement == strsize)
		{
		matches = 1;
		break;
		}
	    }
	}

    /* if just one match then return matching element displacement */
    if (matches == 1)
	return (match); /* good return */
    return (-1);	/* bad return */
}
