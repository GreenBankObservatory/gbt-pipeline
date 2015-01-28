import os
import sys

if __name__ == '__main__':
    print "WARNING:   mapDefault.py is being renamed to image.py"
    print "           Beginning with the next release, only "
    print "           the new name will be available."
    imgfile = os.path.dirname(os.path.realpath(__file__)) + '/../image.py'
    imgfile = os.path.normpath(imgfile)

    aipspy = os.path.dirname(os.path.realpath(__file__)) + '/../tools/aipspy'
    aipspy = os.path.normpath(aipspy)

    params = []
    
    argc = len(sys.argv)
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
    os.system(cmd)
