#! /usr/bin/env python

"""Check for the existance of the SDFITS input file.

If the SDFITS input file exists, then use it.  Otherwise, recreate it from
the project directory, if it is provided.

"""

import sys
import os.path
import subprocess

def check_for_sdfits_file( infile, sdfitsdir, beginscan, endscan,\
                           refscan1, refscan2, VERBOSE ):

    # if the SDFITS input file doesn't exist, generate it
    if (not os.path.isfile(infile) and os.path.isdir(sdfitsdir) and \
        beginscan < endscan):
        if VERBOSE > 0:
            print "SDFITS input file does not exist; trying to generate it from",\
                  "sdfits-dir input parameter directory and user-provided",\
                  "begin and end scan numbers."

        if not os.path.exists('/opt/local/bin/sdfits'):
            print "ERROR: input sdfits file does not exist and we can not"
            print "    regenerate it using the 'sdfits' filler program in"
            print "    Green Bank. (/opt/local/bin/sdfits).  Exiting"
            sys.exit(2)
            
        if refscan1 < beginscan:
            minscan = refscan1
        else:
            minscan = beginscan

        if refscan2 > endscan:
            maxscan = refscan2
        else:
            maxscan = endscan

        sdfitsstr = '/opt/local/bin/sdfits -fixbadlags -backends=acs' + \
                    ' -scans=' + str(minscan) + ':' + str(maxscan) + ' ' + \
                    sdfitsdir

        if VERBOSE > 0:
            print sdfitsstr

        try:
            retcode = subprocess.call(sdfitsstr, shell=True)
            if retcode < 0:
                print >>sys.stderr, "Child was terminated by signal", -retcode
            else:
                print >>sys.stderr, "Child returned", retcode
        except OSError, e:
            print >>sys.stderr, "Execution failed:", e

        infile = os.path.basename(sdfitsdir) + ".raw.acs.fits"

        # if the SDFITS input file exists, then use it to create the map
        if os.path.isfile(infile):
            if VERBOSE > 2:
                print "infile OK"
        else:
            print "infile not OK"

    return infile

if __name__ == "__main__":
    outfilename = "newinfile.txt"
    newinfile= check_for_sdfits_file( str(sys.argv[1]), str(sys.argv[2]),\
                                 int(sys.argv[3]), int(sys.argv[4]),\
                                 int(sys.argv[5]), int(sys.argv[6]),\
                                 int(sys.argv[7]) )
    outfile = open(outfilename,'w')
    outfile.write(str(newinfile))
    outfile.close()
    sys.exit(0)
