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

