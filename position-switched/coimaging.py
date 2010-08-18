from AIPS import *
from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import *
from AIPSData import AIPSUVData, AIPSImage

import pipeutils

AIPS.userno=11111
myfiles = sys.argv[1:]

# empty the catalog
#AIPSCat().zap()

uvlod=AIPSTask('uvlod')
sdgrd=AIPSTask('sdgrd')
fittp=AIPSTask('fittp')
dbcon=AIPSTask('dbcon')

for thisFile in myfiles:
    print thisFile
    uvlod.datain='PWD:'+thisFile
    print uvlod.datain
    uvlod.go()

nfiles = len(myfiles)
if nfiles > 1:
    # must DBCON

    # always do first 2
    dbcon.indisk=1
    dbcon.inname = AIPSCat()[1][-nfiles].name
    dbcon.inclass = AIPSCat()[1][-nfiles].klass
    dbcon.inseq = AIPSCat()[1][-nfiles].seq
    dbcon.in2name = AIPSCat()[1][-nfiles+1].name
    dbcon.in2class = AIPSCat()[1][-nfiles+1].klass
    dbcon.in2seq = AIPSCat()[1][-nfiles+1].seq
    dbcon.reweight[1] = 0
    dbcon.reweight[2] = 0
    dbcon.go()

    # and keep adding in one
    for ii in range(nfiles)[2:]:
        # end of cat is always most recent dbcon result
        dbcon.inname = AIPSCat()[1][-1].name
        dbcon.inclass = AIPSCat()[1][-1].klass
        dbcon.inseq = AIPSCat()[1][-1].seq
        dbcon.in2name = AIPSCat()[1][-nfiles+ii].name
        dbcon.in2class = AIPSCat()[1][-nfiles+ii].klass
        dbcon.in2seq = AIPSCat()[1][-nfiles+ii].seq
        dbcon.go()

# Now make an image using the last item in the catalog
sdgrd.indisk=1
sdgrd.inname=AIPSCat()[1][-1].name
sdgrd.inclass=AIPSCat()[1][-1].klass
sdgrd.inseq=AIPSCat()[1][-1].seq
sdgrd.optype='-GLS'
sdgrd.xtype=-12
sdgrd.ytype=-12
sdgrd.reweight[1] = 0
sdgrd.reweight[2] = 0.05
sdgrd.cellsize[1] = 15
sdgrd.cellsize[2] = 15
sdgrd.imsize[1] = 200
sdgrd.imsize[2] = 200
#sdgrd.cellsize[1] = 180
#sdgrd.cellsize[2] = 180
#sdgrd.imsize[1] = 90
#sdgrd.imsize[2] = 90

#sdgrd.bchan=1000
#sdgrd.echan=1000

sdgrd.go()

## and write the last thing now in the catalog to disk
fittp.indisk=1
fittp.inname=AIPSCat()[1][-1].name
fittp.inclass=AIPSCat()[1][-1].klass
fittp.inseq=AIPSCat()[1][-1].seq
outimage = os.path.splitext(myfiles[0])[0]+'_image.fits'
if os.path.exists(outimage):
    os.remove(outimage)
    print 'Removed existing file to make room for new one :',outimage

fittp.dataout='PWD:'+outimage
fittp.go()

print 'Wrote',outimage

print AIPSCat()
