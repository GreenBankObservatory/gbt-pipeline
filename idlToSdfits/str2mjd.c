/*  @(#)str2mjd.c  version 1.3  created 95/11/24 08:11:30
    %% function to convert string (yymmmdd) to Modified Julian Date
    LANGUAGE: C
    ENVIRONMENT: Any
*/

/* includes */
#include "vlb.h"

/*******************************************************************************
*/
char *str2mjd		/* convert date string to MJD */
    (
    char *string,	/* input ascii string pointer with '\0' terminator */
    long *mjd		/* returned MJD */
    )
/*
 * RETURNS NULL if no errors, 
 *         otherwise pointer to error message (mjd contents undetermined)
 *
 * STR2MJD decodes the given date string <string> and returns the equivalent 
 * Modified Julian Date.  Leading blanks and tabs are ignored.  The string is 
 * terminated by first unreconized character.
 *
 * If the year is less than 100, years 0 to 49 are converted to 2000 to 2049, 
 * while years 50-99 are converted to 1950 to 1999.  Months need not be three 
 * characters - they may be as much as the full month name or as little as 
 * needed to ensure uniqueness.  If they are not unique, ERROR is returned.  
 * The year and month are required, but the day is optional (0 is assumed).  
 * If the string cannot be decoded correctly ERROR is returned.  
 *
 *       date-string   returned MJD
 *       -----------   ------------
 * EXAMPLES OF LEGAL INPUT --
 * 	85may03		46188 (year assumed 1985)
 *	11may03		55684 (year assumed 2011)
 *	00may03		51667 (year assumed 2000)
 *	2000may03	51667 (same)
 *	85f1		46097 (1985feb01)
 *	85feb		46096 (MJD for feb 0 = jan 31)
 *	85november	46369 (MJD for nov 0 = oct 31)
 *
 * EXAMPLES OF ILLEGAL INPUT --
 *	1985    (month is required -- use 1985jan to get 1985jan0)
 *	85ma03  ('ma' is not unique -- could be mar or may)
 *	may03   (year is required)  
 */
{
/* 2,400,000 (difference between Julian Date and Modified Julian Date) 
   minus # days from jan 1, 4713 BC (beginning of Julian calendar) */
#define AD 678576

    static int monlen[] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };
    static char monlist[] = "\
  JANUARY FEBRUARY    MARCH    APRIL      MAY     JUNE\
     JULY   AUGUSTSEPTEMBER  OCTOBER NOVEMBER DECEMBER";
#define ITEMLEN 9	/* length of each item in monlist[] */

    char monstr[20];
    char *monptr;
    int iyr;
    int iday;
    int imon;
    int leap;
    long jd;
    int i;

    /* skip over any leading white space */
    while (iswhite (*string))
        string++;

    /* check for empty string */
    if (*string == '\0')
	return ("empty string");

    /* get year from string setting iyr = integer year */
    if (!isdigit (*string))          /* year is required */
	return ("year missing");
    iyr = 0;
    while (isdigit (*string))
        iyr = iyr * 10 + *string++ - '0';

    /* if year < 100 add its implied prefix */
    if (iyr < 50)
        iyr += 2000;
    if (iyr < 100)
        iyr += 1900;

    /* set leap = 1 if current year is leapyear, otherwise = 0 */
    leap = (iyr % 4 == 0) ? 1 : 0;
    if (iyr % 100 == 0)
        leap = 0;
    if (iyr % 400 == 0)
        leap = 1;

    /* get month from string setting monstr = month string */
    monptr = monstr;
    while (isalpha (*string))
        *monptr++ = *string++;
    if (monptr == monstr)       /* month is required */
	return ("month missing");

    /* convert month name to integer (jan=0) using srclist() to do min-match */
    *monptr = '\0';
    cvrtuc (monstr);		/* convert to upper-case */
    if ((imon = srclist (monstr, monlist, ITEMLEN)) == -1)
	return ("bad month");

    /* get day from string setting iday = integer day */
    iday = 0;
    while (isdigit (*string))
        iday = iday * 10 + *string++ - '0';

    /* check for day > month allows */
    if (imon != 1 && iday > monlen[imon] 
      || imon == 1 && iday > monlen[1] + leap)
	return ("day too big");
 
    /* calculate number of days from Julian calendar start to year start */
    iyr--;
    jd = iyr * 365L + iyr / 4 - iyr / 100 + iyr / 400;

    /* add number of days to month start */
    for (i = 0; i < imon; i++)
        jd += monlen[i];
    if (imon >= 2)
        jd += leap;

    /* add number of days in month, subtract Julian/MJD difference */
    *mjd = jd + iday - AD;
    return (NULL);
}
