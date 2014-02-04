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

from Pipeutils import Pipeutils

import numpy as np


class Integration:

    def __init__(self, row):
        self.pu = Pipeutils()
        self.data = row

    def __getitem__(self, key):
        if key == 'DATA':
            return self.pu.masked_array(self.data[key][0])
        else:
            # strip leading and trailing whitespace
            return_val = self.data[key][0]
            if isinstance(return_val, str) or type(return_val) == np.string_:
                return return_val.strip()
            else:
                return return_val

    def __setitem__(self, key, value):
        self.data[key] = value
