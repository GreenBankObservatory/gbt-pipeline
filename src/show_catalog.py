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
import argparse

from aips_utils import Catalog

cat = Catalog()   # initialize a catalog object
parser = argparse.ArgumentParser()
parser.add_argument('aipsid', type=int,
                    help=("The AIPS catalog number to use.  This is typically "
                          "your system id, which you can find by typing "
                          "'id -u' at the command line."))
args = parser.parse_args()
DISK_ID = 1                        # choose a good default work disk
cat.config(args.aipsid, DISK_ID)  # configure the catalog object
cat.show()
