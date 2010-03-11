"""Check for the existance of the SDFITS input file.

If the SDFITS input file exists, then use it.  Otherwise, recreate it from
the project directory, if it is provided.

"""

import sys
import os.path

def check_for_sdfits_file( infile, sdfitsdir, beginscan, endscan,\
                           refscan1, refscan2, VERBOSE ):
    # if the SDFITS input file doesn't exist, generate it
    if (not os.path.isfile(infile) and os.path.isdir(sdfitsdir) and \
        beginscan < endscan):
        if VERBOSE > 0:
            print "SDFITS input file does not exist; generating it from",\
                  "sdfits-dir input parameter directory and user-provided",\
                  "begin and end scan numbers."

        if refscan1 < beginscan:
            minscan = refscan1
        else:
            minscan = beginscan

        if refscan2 > endscan:
            maxscan = refscan2
        else:
            maxscan = endscan

        sdfitsstr = '/opt/local/bin/sdfits -fixbadlags -backends=acs' + \
                    ' -scans=' + minscan + ':' + maxscan + ' ' + sdfitsdir

        if VERBOSE > 0:
            print sdfitsstr

        os.system(sdfitsstr)

        infile = os.path.basename(sdfitsdir) + ".raw.acs.fits"

    # if the SDFITS input file exists, then use it to create the map
    if os.path.isfile(infile):
        if VERBOSE > 2:
            print "infile OK"
    else:
        print "infile not OK"

if __name__ == "__main__":
    check_for_sdfits_file( sys.argv[1], sys.argv[2], sys.argv[3],\
                           sys.argv[4], sys.argv[5], sys.argv[6],\
                           sys.argv[7] )
    sys.exit(0)
