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

# parsel-tongue script that performs only the default processing
#HISTORY
#10DEC19 GIL inital version to clean up aips directory


from AIPS import *
from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import *
from AIPSData import AIPSUVData, AIPSImage
from Wizardry.AIPSData import AIPSUVData as WizAIPSUVData
from Wizardry.AIPSData import AIPSImage as WizAIPSImage

import sys
import os
import math

argc = len(sys.argv)
if argc < 2:
    print ''
    print 'clean: Removal all AIPS catalog entries'
    print 'usage: doImage clean.py <aipsNumber>'
    print 'where <aipsNumber>     Your *PIPELINE* AIPS number (should always be the same)'
    print ''
    quit()
        
AIPS.userno=int(sys.argv[1])    # retrieve AIPS pipeline user number
mydisk=2                        # choose a good default work disk
baddisk=1                       # list a disk to avoid (0==no avoidance)

catalog = AIPSCat()[mydisk]
catalog_size = len(catalog)

print 'catalog_size',catalog_size

for xx in range(catalog_size):

    aname = AIPSCat()[mydisk][xx].name
    aclass = AIPSCat()[mydisk][xx].klass
    aseq = AIPSCat()[mydisk][xx].seq

    spectra = AIPSUVData( aname, aclass, mydisk, aseq)
    image = AIPSImage( aname, aclass, mydisk, aseq)

    if spectra.exists():
        spectra.clrstat()
    elif image.exists():
        image.clrstat()

AIPSCat().zap()                 # empty the catalog

