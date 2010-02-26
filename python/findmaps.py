import sys
import pyfits
import numpy as np

ECHO=True

# create a temporary file in which to write mapping ranges
rangefile = open('/tmp/kfpa-mapping-scan-ranges', 'w')
if not rangefile:
	print "ERROR: could not create temporary file for output."
	sys.exit(1)

# open the SDFITS file that may contain mapping scans
sdfits= pyfits.open(sys.argv[1])
if not sdfits:
	print "ERROR: Could not open " + sys.argv[1]
	sys.exit(1)

# create a mask with for all integrations (rows) with RALongMap as the OBSMODE
ralongs = sdfits[1].data.field('OBSMODE').startswith("RALongMap")

# create a mask with for all integrations (rows) with DecLatMap as the OBSMODE
declats = sdfits[1].data.field('OBSMODE').startswith("DecLatMap")

# combine the masks
maprows = ralongs | declats

# select all SCAN values with mapping integrations
scans = sdfits[1].data.field('SCAN')[maprows]

# make the scan list unique
uniquescans = np.unique(scans)

# identify places in the list where scan numbers are non-sequential
breaks = np.diff(uniquescans) != 1

# record the number of the first mapping scan in the file
firstmapscan = uniquescans[0]

# identify the scan numbers at the beginning of each map,
#  excluding the first mapping scan
startscans = uniquescans[np.where((np.diff(uniquescans)!= 1)==True)[0]+1]

# identify the scan number at the beginning of each map
mapstarts = np.r_[firstmapscan,startscans]

# identify the scan number at the end of each map
mapstops  = np.r_[uniquescans[np.diff(uniquescans)!= 1],uniquescans[-1]]

# combine the beginning and end mapping scans into a paired list or ranges
mapranges = zip(mapstarts,mapstops)

if ECHO:
	print "Map scan ranges:"

# write these ranges to a temporary file
for x in range(len(mapranges)):
	rangestr = "".join(str(mapranges[x][0]) + ',' + str(mapranges[x][1]))
	if ECHO:
		print rangestr
	rangefile.write(rangestr + '\n')

# close the output file
rangefile.close()

# close the SDFITS input file
sdfits.close()


