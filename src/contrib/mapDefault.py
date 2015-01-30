import os
import sys
import subprocess

if __name__ == '__main__':
    imgfile = os.path.dirname(os.path.realpath(__file__)) + '/../image.py'
    imgfile = os.path.normpath(imgfile)
    print "WARNING:   mapDefault.py is being replaced by image.py"
    print ""
    print "           In fact, this script is calling image.py"
    print "           with a slightly reformatted command line."
    print ""
    print "           In image.py parameters are set with named"
    print "           arguments (.e.g. --average=3) vs the positional"
    print "           style currently used (.e.g. average is the value"
    print "           of the 2nd parameter at the command line). To see" 
    print "           usage for the new script, type"
    print ""
    print "           aipspy " + imgfile
    print ""
    print "           Beginning with the next release, only "
    print "           the new name will be available."
    print ""

    aipspy = os.path.dirname(os.path.realpath(__file__)) + '/../tools/aipspy'
    aipspy = os.path.normpath(aipspy)

    params = []
    
    argc = len(sys.argv)
    if argc < 2:
        print ''
        print 'mapDefault: Compute default images from calibrated spectra'
        print 'usage: doImage mapDefault.py <aipsNumber> [<nAverage>] [<mapRaDeg>] [<mapDecDeg>] [<imageXPixels>] [<imageYPixels>] [<refFreqMHz>]'
        print 'where <aipsNumber>     Your *PIPELINE* AIPS number (should always be the same)'
        print '     [<nAverage>]      Optional number of channels to average'
        print '     [<mapRaDeg>]      Optional map center RA (in Degrees)'
        print '     [<mapDecDeg>]     Optional map center Declination (in Degrees)'
        print '     [<imageXPixels>]  Optional image X pixel size'
        print '     [<imageYPixels>]  Optional image Y pixel size'
        print '     [<refFregMHz>]    Optional rest frequency MHz'
        print 'To enter later arguments, values for the previous must be provided' 
        print ''
        sys.exit()

    if argc > 1:
        params.append(sys.argv[1])    # retrieve AIPS pipeline user number
    if argc > 2:
        params.append('--average ' + sys.argv[2])
    if argc > 4:
        params.append('--center ' + sys.argv[3] + ',' + sys.argv[4])
    if argc > 6:
        params.append('--size ' + sys.argv[5] + ',' + sys.argv[6])
    if argc > 7:
        params.append('--restfreq ' + sys.argv[7])

    params = ' '.join(params)
    cmd = ' '.join((aipspy, imgfile, params))
   
    print 'Invoking: ', cmd
    subprocess.call(cmd, shell=True)
