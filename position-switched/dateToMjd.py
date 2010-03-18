#! /usr/bin/env python

"""Procedure to convert at FITS date string to MJD

"""

import sys
import string

def gd2jd(day,month,year,hour,minute,second):
    """Converts a gregorian date to julian date.

    Keyword arguments:
    day -- 2 digit day string
    month -- 2 digit month string
    year -- 4 digit year string
    hour -- 2 digit hour string
    minute -- 2 digit minute string
    second -- N digit second string

    """

    dd=int(day)
    mm=int(month)
    yyyy=int(year)
    hh=float(hour)
    min=float(minute)
    sec=float(second)

    UT=hh+min/60+sec/3600

    total_seconds=hh*3600+min*60+sec

    if (100*yyyy+mm-190002.5)>0:
        sig=1
    else:
        sig=-1

    JD = 367*yyyy - int(7*(yyyy+int((mm+9)/12))/4) + int(275*mm/9) + dd + 1721013.5 + UT/24 - 0.5*sig +0.5

    return JD

def dateToMjd(dateString):
    """Convert a FITS date string to Modified Julian Date

    Keyword arguments:
    dateString -- a FITS format date string, ie. '2009-02-10T21:09:00.08'

    Returns:
    floating point Modified Julian Date

    """

    year  = dateString[:4]
    month = dateString[5:7]
    day   = dateString[8:10]
    hour  = dateString[11:13]
    minute= dateString[14:16]
    second= dateString[17:]

    # now convert from julian day to mjd
    jd = gd2jd(day,month,year,hour,minute,second)
    mjd = jd - 2400000.5
    return mjd

if __name__ == "__main__":
    # write Modified Julian Date to a file named 'mjd.txt'
    # then, in IDL open file with time and read value into a variable
    mjd = dateToMjd(sys.argv[1])
    outfile = open("mjd.txt",'w')
    outfile.write(str(mjd))
    outfile.close()
    sys.exit(0)
