"""Convenience methods for controlling AIPS.

These classes and methods build upon the ParselTongue AIPS module.

"""
# Copyright (C) 2013 Associated Universities, Inc. Washington DC, USA.
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

import sys
import AIPS
from AIPSTask import AIPSTask
from AIPSData import AIPSUVData, AIPSCat
from Wizardry.AIPSData import AIPSImage as WizAIPSImage


class Task(object):
    """An object to represent an AIPS task.
    """

    def __init__(self, taskname, name, klass, seq):

        self.task = AIPSTask(taskname)
        self.task.name = name
        self.task.klass = klass
        self.task.seq = seq

    def __setitem__(self, key, value):
        self.task.key = value


class Catalog(object):
    """Utility class to operate on the AIPS catalog.
    """

    def __len__(self,):
        """Get the number of catalog entries."""
        return len(AIPSCat()[self.DISK_ID])

    def config(self, userno, disk_id):
        """Configure an AIPS catalog object.

        Args:
            userno: The AIPS user id.
            disk_id: The AIPS disk.

        """
        AIPS.userno = userno
        self.DISK_ID = disk_id

    def show(self,):
        """Print to screen the contents of the AIPS catalog.

        """
        msg = "AIPS Catalog"
        print ""
        print "-" * len(msg)
        print msg
        print "-" * len(msg)
        print ""
        print AIPSCat(self.DISK_ID)

    def last_entry(self,):
        """Retrieve the most recent AIPS catalog entry.

        Returns:
            Last AIPS catalog entry.

        """
        return self.get_entry(-1)

    def get_entry(self, n):
        """Return an AIPS catalog entry.

        Args:
            n(int): Catalog entry number.

        Returns:
            AIPS catalog entry.

        """
        return AIPSCat()[self.DISK_ID][n]

    def get_image(self, e):
        """Get a WizAIPSImage object form the AIPS entry.

        Args:
            e: A catalog entry, like what's returned from get_entry().

        Returns:
            AIPS image.

        """
        return WizAIPSImage(e.name, e.klass, self.DISK_ID, e.seq)

    def get_uv(self, e):
        """Get a AIPSUVData object form the AIPS entry.

        Args:
            e: A catalog entry, like what's returned from get_entry()

        Returns:
            AIPS UVData object.

        """
        return AIPSUVData(e.name, e.klass, self.DISK_ID, e.seq)

    def zap_entry(self, n):
        """Remove an entry from the AIPS catalog using python index

        Args:
            n(int): Catalog entry number.

        """

        entry = self.get_entry(n)
        try:
            data = self.get_uv(entry)
            data.zap()
        except:
            data = self.get_image(entry)
            data.zap()

    def empty(self, do_empty):
        """Empty the AIPS catalog.

        Args:
            do_empty(bool): If set, do not prompt user for confirmation.

        """
        if not do_empty:
            choice = raw_input('Is it OK to clear your AIPS '
                               'catalog (id={0})? [y/n] '.format(AIPS.userno))
            if choice.lower() == 'n':
                print "Can not continue without an empty catalog.  Exiting."
                sys.exit()
            elif choice.lower() == 'y':
                AIPSCat().zap()                 # empty the catalog
            else:
                self.empty(do_empty)  # if they didn't type 'y' or 'n', ask again.
        else:
            AIPSCat().zap()
