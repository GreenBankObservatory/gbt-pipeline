import os
import sys
import subprocess

if __name__ == '__main__':
    loadfile = os.path.dirname(os.path.realpath(__file__)) + '/../load.py'
    loadfile = os.path.normpath(loadfile)
    print "WARNING:   dbcon.py is being replaced by load.py"
    print ""
    print "           In fact, this script is calling load.py"
    print "           with a slightly reformatted command line."
    print "           To see usage for the new script, type"
    print ""
    print "           aipspy " + loadfile
    print ""
    print "           Beginning with the next release, only "
    print "           the new name will be available."
    print ""
    
    argc = len(sys.argv)
    if argc < 3:
        print ''
        print 'dbcon: Combine all observations into a single dish fits file'
        print 'usage: doImage dbcon <aipsNumber> <spectra File 1> [<spectra File n>]'
        print 'where <aipsNumber>     Your *PIPELINE* AIPS number (should always be the same)'
        print '      <spectra File 1> One or more calibrated spectra files (*.aips.fits)'
        print '      Combined spectra are placed in catalog slot 1'
        print ''
        sys.exit()

    sys.argv.append('--empty-catalog')

    aipspy = os.path.dirname(os.path.realpath(__file__)) + '/../tools/aipspy'
    aipspy = os.path.normpath(aipspy)

    params = ' '.join(sys.argv[1:])
    cmd = ' '.join((aipspy, loadfile, params))

    print "Invoking:  " + cmd
    subprocess.call(cmd, shell=True)
    
