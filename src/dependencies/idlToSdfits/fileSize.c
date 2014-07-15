/* File fileSize.c, version 1.1, released  03/09/11 at 11:03:50 
   retrieved by SCCS 14/04/23 at 15:50:56     

%% utility to return a file size in bytes
:: file utility

HISTORY
030911 GIL initial version to return a file size in bytes

DESCRIPTON
fileSize() returns the file size in bytes
*/

#include "stdio.h"
#include "string.h"
#include "sys/stat.h"
#include "unistd.h"
#include "STDDEFS.H"

/* externals */
/* internals */

char * fileSize ( char * fileName, long * fileLength )
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* fileSize() takes a file name (null terminated) and gets the file size in  */
/* bytes.  Returns 0 and error message if file not present, etc.             */
{ struct stat statStruct;

  *fileLength = 0;
  if (fileName == NULL) 
    return("NULL input file name");

  if (strlen( fileName) < 1) 
    return("File Name error, name too short");

  stat ( fileName, &statStruct);
  *fileLength = statStruct.st_size;    
  return(NULL);
} /* end of fileSize() */
