from AIPS import *
from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import *
from AIPSData import AIPSUVData, AIPSImage

import pipeutils

class Image:
    """
    
    """
    def __init__(self):
        AIPS.userno=11111
        # create a log file
        AIPS.log    = open('./AIPS.log','a')
        # empty the catalog
        AIPSCat().zap()

    def make_image(self,infiles,freq=23000):
        """
        
        """
        uvlod=AIPSTask('uvlod')
        sdgrd=AIPSTask('sdgrd')
        fittp=AIPSTask('fittp')
        dbcon=AIPSTask('dbcon')
        
        gbtbeamsize = pipeutils.gbtbeamsize(freq) # arc seconds

        for thisFile in infiles:
            print thisFile
            uvlod.datain='PWD:'+thisFile
            print uvlod.datain
            uvlod.go()
    
        for idx,myfile in enumerate(infiles):

            print myfile
            
            uvlod.datain='PWD:'+myfile
            print uvlod.datain
            uvlod.go()
            
            sdgrd.indisk=1
            sdgrd.inname=AIPSCat()[1][idx].name
            sdgrd.inclass=AIPSCat()[1][idx].klass
            sdgrd.inseq=AIPSCat()[1][idx].seq
            sdgrd.optype='-GLS'
            sdgrd.xtype=-12
            sdgrd.ytype=-12
            sdgrd.cellsize[1] = 5
            sdgrd.cellsize[2] = 5
            sdgrd.imsize[1] = 600
            sdgrd.imsize[2] = 600
            
            # l-band
            #sdgrd.cellsize[1] = 180
            #sdgrd.cellsize[2] = 180
            #sdgrd.imsize[1] = 90
            #sdgrd.imsize[2] = 90
            
            sdgrd.bchan=1000
            sdgrd.echan=1001
            sdgrd.go()
            
            fittp.indisk=1
            fittp.inname=AIPSCat()[1][idx].name
            fittp.inclass='SDGRD'
            fittp.inseq=AIPSCat()[1][idx].seq
            outimage = os.path.splitext(myfile)[0]+'_image.fits'
            fittp.dataout='PWD:'+outimage
            fittp.go()
            
            os.system('/home/jmasters/local/bin/ds9 '+outimage+'&')
            
            print 'Wrote',outimage
            
        print AIPSCat()
