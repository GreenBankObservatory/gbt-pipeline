/* File inIntList.c, version 1.3, released  05/04/14 at 09:22:57 
   retrieved by SCCS 14/04/23 at 15:51:03     

%% program to select GBT fits data to an IDL structure
:: spectrometer export program

HISTORY
050414 GIL add makeIntList() to fill an array with integers
040416 GIL initial version

DESCRIPTION:
inIntList() returns true if an integer is in an ascii list
of format:
"1,2,5"
"1,2:5,10"
"1:3,5,9:12" etc
*/
#include "stdio.h"
#include "stdlib.h"
#include "string.h"
#include "STDDEFS.H"
/* externals */
extern char * stripWhite( char *);

/* inIntList() parses a string and matches integers */
/* note the input list is modified! */
long inIntList( long inInt, char * intList) 
{ long iStart = 0, iEnd = 0, iItem = 0, i = 0, j = 0, n = 0, inRange=FALSE;
  char tempString[512] = "";

  /* valid lists:  *;  1,2,5  1:10,22  2:5,8:12,37 */
  stripWhite( intList);
  n = strlen( intList);
  if (n < 1)          /* null list means no elements */
    return FALSE;
  if (n == 1) {
    if (intList[0] == '*')
      return TRUE;
  }

  j = 0;
  /* read through all characters in the string */
  for (i = 0; i < n; i++) {
    if (intList[i] == ',' || intList[i]==':') {
      tempString[j] = EOS;
      sscanf( tempString,"%ld", &iItem);
      j = 0;

      if (inInt == iItem)
	return TRUE;

      if (intList[i]==':') {  /* if termianted by a semi-colon */
	iStart = iItem;
	inRange = TRUE;
      }
      else { /* else found , */
	if (inRange) {
	  iEnd = iItem;
	  /* else found end range */
	  if (inInt >= iStart && inInt <= iEnd) 
	    return TRUE;
	}
	inRange = FALSE;     /* no longer in range if , found */
      } /* end else found , */
    }
    else {
      tempString[j] = intList[i];
      j++;
    }
  } /* end for all characters */

  tempString[j] = EOS;

  if (strlen( tempString) > 0) {   /* end list might be terminated by a null */
    sscanf( tempString, "%ld", &iItem);
    if (iItem == inInt)
      return TRUE;
    else { 
      if (inRange) {
	iEnd = iItem;
	/* else found end range */
	if (inInt >= iStart && inInt <= iEnd) 
	  return TRUE;
      } /* end if in a 'x:y' range */
    } /* end else item did not match last */
  } /* if some characters left */

  return FALSE;
} /* end of inIntList */

char *makeIntList( long maxInt, long list[], long * nInList, char * intList) 
/* makeIntList() generates a list of integers matching the criteria in      */
/* the input string intList.   list[] values run from 0 to maxInt-1         */
{ long i = 0, count = 0;

  for (i = 0; i < maxInt; i++) {
    if (inIntList( i, intList)) {
      list[count] = i;
      count++;
    }
  } /* for all possible integers in the list */

  *nInList = count;
  return(NULL);
}  /* end of makeIntList() */
     
