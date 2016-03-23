# Copyright (C) 2007 Associated Universities, Inc. Washington DC, USA.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Correspondence concerning GBT software should be addressed as follows:
#       GBT Operations
#       National Radio Astronomy Observatory
#       P. O. Box 2
#       Green Bank, WV 24944-0002 USA

# $Id$

import numpy as np


class Pipeutils:

    def __init__(self, log=None):

        self.log = log

    def _gregorian_to_julian_date(self, day, month, year, hour, minute, second):
        """Converts a gregorian date to julian date.

        Keyword arguments:
        day -- 2 digit day string
        month -- 2 digit month string
        year -- 4 digit year string
        hour -- 2 digit hour string
        minute -- 2 digit minute string
        second -- N digit second string

        Returns:
        a floating point value which is the julian date
        """

        dd = int(day)
        mm = int(month)
        yyyy = int(year)
        hh = float(hour)
        minute = float(minute)
        sec = float(second)

        UT = hh+minute/60+sec/3600

        if (100 * yyyy + mm - 190002.5) > 0:
            sig = 1
        else:
            sig = -1

        JD = (367 * yyyy - int(7 * (yyyy + int((mm + 9) / 12)) / 4) +
              int(275 * mm / 9) + dd + 1721013.5 + UT / 24 - 0.5 * sig + 0.5)

        return JD

    def dateToMjd(self, dateString):
        """Convert a FITS DATE string to Modified Julian Date

        Keyword arguments:
        dateString -- a FITS format date string, ie. '2009-02-10T21:09:00.08'

        Returns:
        floating point Modified Julian Date

        """

        year = dateString[:4]
        month = dateString[5:7]
        day = dateString[8:10]
        hour = dateString[11:13]
        minute = dateString[14:16]
        second = dateString[17:]

        # now convert from julian day to mjd
        jd = self._gregorian_to_julian_date(day, month, year, hour, minute, second)
        mjd = jd - 2400000.5
        return mjd

    def _hz2wavelength(self, f):
        """Simple frequency (Hz) to wavelength conversion

        Keywords:
        f -- input frequency in Hz

        Returns:
        wavelength in meters

        >>> pu = Pipeutils()
        >>> round(pu._hz2wavelength(23e9), 6)
        0.013034

        """
        c = 299792458.  # speed of light in m/s
        return (c/f)

    def masked_array(self, array):
        """Mask nans in an array

        Keywords:
        array -- (numpy nd array)

        Returns:
        numpy masked array with nans masked out

        """
        return np.ma.masked_array(array, np.isnan(array))
