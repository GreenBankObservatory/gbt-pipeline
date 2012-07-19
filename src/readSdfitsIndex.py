#! /usr/bin/env python2.7

import sys
if sys.version_info[0] != 2 or sys.version_info[1] < 7:
    ver = '.'.join((str(sys.version_info[0]),str(sys.version_info[1])))
    print 'ERROR: Your version of python ['+ver+'] must be >= 2.7',\
        'to run this program. Please try again.'
    sys.exit()

import argparse
from SdFitsIO import SdFitsIO


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=\
        'Summarize a SDFITS index file by scan.')
    parser.add_argument("infile", default='', help="SDFITS index file name",
        metavar='FILENAME')
    args = parser.parse_args()
    
    if not args.infile.endswith('.index'):
        print 'ERROR: Input file name does not end with \'.index\''
        print '    Please make sure you are using an index file'
        sys.exit(1)
    
    sdf = SdFitsIO()
    rowList = sdf.parseSdfitsIndex(args.infile)
    
    scan=13
    feed=1
    window=0
    pol='LL'
    filteredRows = rowList.get(scan, feed, window, pol)
    print 'scan',scan, '(feed',feed, 'window',window, 'pol',pol,')', \
        'extension',filteredRows['EXTENSION'],\
        'nRows', filteredRows['ROW']

    #scan=13
    #feed=4
    #window=0
    #pol='LL'
    #filteredRows = integrationList.get(scan, feed, window, pol)
    #print 'scan',scan, '(feed',feed, 'window',window, 'pol',pol,')', \
    #    'extension',filteredRows['EXTENSION'],\
    #    'nRows', len(filteredRows['ROW']),\
    #    'type',filteredRows['TYPE']
