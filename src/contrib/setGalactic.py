# parsel-tongue script that performs only the default imaging
#HISTORY
#11JAN06 GIL replace the RA-- and DEC- coordinates with Galactic

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
import subprocess

argc = len(sys.argv)
if argc < 2:
    print ''
    print 'setGalactic: Replace FITS coordinate header keywords with Galactic'
    print 'usage: setGalactic <dataCubeName>'
    print 'where <dataCubeName>   Full FITS file name'
    print ''
    quit()

myImage = sys.argv[1]

#update rest frequency 
subprocess.call(['fthedit',myImage,'CTYPE1','add','GLON-GLS',\
    "comment='X-Coordinate Type: Galactic'"])
subprocess.call(['fthedit',myImage,'CTYPE2','add','GLAT-GLS',\
    "comment='X-Coordinate Type: Galactic'"])

