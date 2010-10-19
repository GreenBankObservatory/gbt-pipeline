/*  @(#)str2rad.c  version 1.7  created 95/11/24 08:17:21
    %% function to convert a string (degree/hour,min,sec) to radians
    LANGUAGE: C
    ENVIRONMENT: Any
*/

/* includes */
#include "ctype.h"
#include "string.h"
#include "MATHCNST.H"
#include "vlb.h"

/*******************************************************************************
*/
char *str2rad
    (
    char *pString,	/* input ascii string with '\0' terminator */
    double *pRadians	/* returned angle in radians */
    )
/*
 * RETURNS NULL if no error,
 *         otherwise pointer to error message (radians contents is undetermined)
 *
 * The null-terminated input string may have any of the following forms:
 *     <decimal #>     ** Direct input of radians **
 *     <decimal #><delimiter>
 *     <integer><delimiter><decimal # < 60>[<delimiter>]
 *     <int><delim><int < 60><delim><dec # < 60>[<delim>]
 *
 * Delimiters are from the set { D, d, ', ", H, h, M, m, S, s, : }.  They must 
 * be in descending order (e.g. minutes before seconds), and arc-measure must 
 * NOT be mixed with hour-angle measure.
 *
 * A sign (+ or -) may immediately preceed the first digit in the string.
 *
 * Leading blanks and tabs are ignored, but trailing ones are illegal.  The 
 * string must end with the '\0' terminator.
 *
 * The final delimiter is optional.  It defaults to the next smaller unit than 
 * the preceeding delimiter, in the same system of measure.
 *
 * EXAMPLES OF LEGAL INPUT --
 *	1.234		direct input of 1.234 radians
 *	57d17'44.8"	converts to 1.0 radians
 *	12d13.6"	minutes field omitted
 *	12d22.8'	seconds field omitted, note that minutes
 *				may be non-integer in this case
 *	123.45'		if only one unit is specified, it may be
 *				non-integer and any size
 *	-123.45"	minus sign is allowed
 *	-12H13m14.56S	hour-angle, cases may be mixed
 *	  12h13s	leading blanks are allowed
 *	75'15"		minutes may be greater than 60 if they are the
 *				first unit specified
 *	13h45.6		unspecified unit defaults to minutes (time)
 *	17'32.65	unspecified unit defaults to arc-seconds
 *
 * EXAMPLES OF ILLEGAL INPUT --	(returned radians is undetermined)
 *	12d-13'14"	sign must be first non-blank character
 *	12d13m14s	arc-measure may not be mixed with time-measure
 *	12d13"14'	units out of order
 *	12d75'14"	minutes and seconds must be less than 60 (except
 *				when they are the first unit specified)
 *	12h13m75s	ditto
 *	12h 13m 14s	embedded blanks not permitted
 *	- 12h13m14s	ditto
 *	12.3h13m14s	only the last unit may have a decimal point
 *	12h13.5m22s	ditto
 *	12h13m14.5se	string MUST terminate after third delimiter
 *	18s46.77	unspecified unit can't default to less than second
 */
{
    int sign;	      /* angle sign flag, 1=positive, 0=negative */
    int nparts;	      /* current index into ang_part[] */
    int ncolon = 0;   /* number of ':' delimiters encountered */
    double value;     /* current value */
    double power;     /* used to calc value fractional part */
    int i;

    /* one element of this array is filled 
       for each unit type in decending unit order during parse */
    struct {
	double value;	/* value */
	int val_type;	/* 0-integer, 1-floating point */
	int units;	/* 0-not specified, 1-seconds, 
			   60-minutes, 3600-degrees or hours */
	int measure;	/* 0-arc/degrees, 1-time/hours */
    } ang_part[3];

    /* skip over any leading white space */
    while (isspace (*pString))
	pString++;

    /* check for empty string */
    if (*pString == '\0')
	return ("empty string");

    /* set sign flag appropriately */
    sign = 1;		/* assume positive */
    if (*pString == '-')
	{
	sign = -1;
	pString++;
	}
    else if (*pString == '+')
	pString++;

    /* check remaining string for illegal character */
    {
    char *ptr = pString;

    while (*ptr != '\0' && strchr ("0123456789Dd'\"HhMmSs.:", *ptr))
	ptr++;
    if (*ptr != '\0')
	return ("bad character");
    }

    /* parse string into ang_part array, each time around for 
       loop parse through next delimiter filling one array element */
    for (nparts = 0; nparts < 3 && *pString != '\0'; nparts++)
	{
	/* check for delimiter without preceding value */
	if (!isdigit (*pString) && *pString != '.')
	    return ("delimiter without value");

	/* convert string (up to next non-digit) 
	   and use result to set array element value */
	value = power = 0.0;
	while (isdigit (*pString))
	    value = value * 10.0 + *pString++ - '0';
	if (*pString == '.')
	    {
	    pString++;
	    power = 1.0;
	    while (isdigit (*pString))
		{
		value = value * 10.0 + *pString++ - '0';
		power *= 10.0;
		}
	    value /= power;
	    }
	ang_part[nparts].value = value;		/* value */

	/* set array element value type flag, 0-integer, 1-floating pt. */
	ang_part[nparts].val_type = (power == 0.0) ? 0 : 1;

	/* set array element units type and measure type flags */
	if (*pString == '\0')    /* string end wo/ final delimiter */
	    {
	    ang_part[nparts].units = 0;         /* no delimiter */
	    continue;
	    }
	else if (*pString == 'D' || *pString == 'd')
	    {
	    ang_part[nparts].units = 3600;	/* degrees or hours */
	    ang_part[nparts].measure = 0;	/* arc */
	    }
	else if (*pString == 'H' || *pString == 'h')
	    {
	    ang_part[nparts].units = 3600;	/* degrees or hours */
	    ang_part[nparts].measure = 1;	/* time */
	    }
	else if (*pString == '\'')
	    {
	    ang_part[nparts].units = 60;	/* minutes */
	    ang_part[nparts].measure = 0;	/* arc */
	    }
	else if (*pString == 'M' || *pString == 'm')
	    {
	    ang_part[nparts].units = 60;	/* minutes */
	    ang_part[nparts].measure = 1;	/* time */
	    }
	else if (*pString == '"')
	    {
	    ang_part[nparts].units = 1;		/* seconds */
	    ang_part[nparts].measure = 0;	/* arc */
	    }
	else if (*pString == 'S' || *pString == 's')
	    {
	    ang_part[nparts].units = 1;		/* seconds */
	    ang_part[nparts].measure = 1;	/* time */
	    }
	else if (*pString == ':')
	    {
	    if (ncolon == 0)
		ang_part[nparts].units = 3600;  /* hours */
	    else if (ncolon == 1)
		ang_part[nparts].units = 60;	/* minutes */
	    else
		return ("too many colons");
	    ncolon++;
	    ang_part[nparts].measure = 1;	/* time */
	    }
	pString++;
	}

    /* check for too many delimiters */
    if (*pString != '\0')
	return ("too many delimiters");

    /* check for special case of radians entered directly */
    if (nparts == 1 && ang_part[0].units == 0)
	{
	*pRadians = ang_part[0].value;   /* units already radians */
        /* correct sign for negative input */
        if (sign == -1)
	  *pRadians = -*pRadians;
	return (NULL);
	}

    /* if string has no final delimiter 
       set final part units to next smaller ones and measure to same */
    if (ang_part[nparts - 1].units == 0)
	{
	if (ang_part[nparts - 2].units <= 1)
	    return ("bad default units");
	ang_part[nparts - 1].units = ang_part[nparts - 2].units / 60;
	ang_part[nparts - 1].measure = ang_part[nparts - 2].measure;
	}

    /* check for proper units order (smaller unit may not preceed larger) */
    for (i = 1; i < nparts; i++)
	if (ang_part[i].units >= ang_part[i - 1].units)
	    return ("delimiters out of order");

    /* check for consistent measure system (all time or arc) */
    for (i = 1; i < nparts; i++)
	if (ang_part[i].measure != ang_part[i - 1].measure)
	    return ("mixed time and arc delimiters");

    /* check for minutes and seconds in proper range */
    for (i = 1; i < nparts; i++)
	if (ang_part[i].value >= 60.0)
	    return ("minute or second too big");

    /* check for floating point number in wrong place */
    for (i = 0; i < nparts - 1; i++)
      if (ang_part[i].val_type != 0)
	  return ("bad decimal point");

    /* convert values in array to arc-seconds (assume arc/degrees measure) */
    value = 0.0;
    for (i = 0; i < nparts; i++)
        value = value + ang_part[i].units * ang_part[i].value;

    /* if measure is time/hours multiply by 15 to get arc-seconds */
    if (ang_part[0].measure == 1)
	value *= 15.0;

    /* convert arc-seconds to radians */
    *pRadians = value * ARCSEC;

    /* correct sign for negative input */
    if (sign == -1)
	*pRadians = -*pRadians;

    return (NULL);
}
