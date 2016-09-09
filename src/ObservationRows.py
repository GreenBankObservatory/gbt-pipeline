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

from ordereddict import OrderedDict
from collections import namedtuple


class ObservationRows:
    """Store index file information.

       The ObserservationRows class defines a structure to get specific
       information about the spectra out of the index file which was
       produced by the sdfits filler program.

       This is essientially a table of the raw SDFITS file rows, organized
       with a lookup key of scan/feed/window/polarization.

       When rows are added to this object (addRow), the FITS extension,
       row of the FITS table and scan type are stored.

       A list of rows for each scan/feed/window/polarization can be
       retrieved with the 'get' method.

    """
    def __init__(self):
        self.rows = OrderedDict()
        self.Key = namedtuple('key', 'scan, feed, window, polarization')

    def __repr__(self):
        return ('Scans: {0}\nFeeds: {1}\nWindows: {2}\nPols: {3}'.format(self.scans(),
                                                                         self.feeds(),
                                                                         self.windows(),
                                                                         self.pols()))

    def addRow(self, scan, feed, window, polarization,
               fitsExtension, rowOfFitsFile, obsid,
               procname, procscan, nchans):
        """Add rows to the ObservationRows object.

           When rows are added to this object (addRow), the FITS extension,
           row of the FITS table and scan type are stored.

        """

        key = self.Key(scan, feed, window, polarization)

        if key in self.rows:
            self.rows[key]['ROW'].append(rowOfFitsFile)
        else:
            self.rows[key] = {'EXTENSION': fitsExtension,
                              'ROW': [rowOfFitsFile],
                              'OBSID': obsid,
                              'PROCNAME': procname,
                              'PROCSCAN': procscan,
                              'NCHANS': nchans}

    def get(self, scan, feed, window, polarization):
        """Retreive a list of rows for scan/feed/win/pol.

        """
        try:
            key = (scan, feed, window, polarization)
            return self.rows[key]
        except(KeyError):
            raise

    def scans(self):
        """Return a list of scans in the observation.

        """
        return sorted(list(set([xx.scan for xx in self.rows.keys()])))

    def feeds(self):
        """Return a list of feeds in the observation.

        """
        return list(set([xx.feed for xx in self.rows.keys()]))

    def windows(self):
        """Return a list of windows in the observation.

        """
        return list(set([xx.window for xx in self.rows.keys()]))

    def pols(self):
        """Return a list of polarizations in the observation.

        """
        return list(set([xx.polarization for xx in self.rows.keys()]))
