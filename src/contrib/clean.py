# Copyright (C) 2011  National Radio Astronomy Observatory
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
import pyfits

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

#AIPSCat().zap()                 # empty the catalog

kount = 100
for i in range(2,kount):
    aname = AIPSCat()[mydisk][-1].name
    aclass = AIPSCat()[mydisk][-1].klass
    aseq = AIPSCat()[mydisk][-1].seq
    # print i, j, aname, aclass, aseq
    spectra = AIPSUVData( aname, aclass, mydisk, aseq)
    if spectra.exists():
        spectra.clrstat()
        spectra.zap()
    else:
        image = AIPSImage( aname, aclass, mydisk, aseq)
        if image.exists():
            image.clrstat()
            image.zap()
        else:
            exit()

