import sys
import os.path
import csv
import findmaps

ROOT='/home/sandboxes/jmasters/data/AGBT08B_040_03.raw.acs'
INDEXFILE = ROOT+'.index'
FITSFILE = ROOT+'.fits'
RANGEFILE = os.path.basename(ROOT)+'.index-all-map-ranges.txt'

findmaps.findmaps(INDEXFILE)

rangefile = open(RANGEFILE)
if not rangefile:
    print "ERROR: Problem opening rangefile:",RANGEFILE
    sys.exit(1)

rangelist = csv.reader(open( os.path.basename(ROOT)+'.index-all-map-ranges.txt'))

for row in rangelist:
    cmdstring = 'kfpa_pipeline --infile=' + FITSFILE + \
                ' --begin-scan=' + str(row[0]) + \
                ' --end-scan=' + str(row[1]) + \
                ' --vsource-center=5.8' + \
                ' --vsource-width=2.0' + \
                ' --vsource-begin=-.2' + \
                ' --vsource-end=11.8' + \
                ' --refscan1=15' + \
                ' --refscan2=51' + \
                ' --all-scans-as-ref=1' + \
                ' --verbose=3' 
    os.system(cmdstring)
