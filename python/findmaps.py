import sys
import os.path

DEBUG = 1

if len(sys.argv) > 1:
	infile = open(sys.argv[1])  # open an index file
	if not file:
		print "Check input file"

RAMAP = 'RALongMap'
DECMAP = 'DecLatMap'

# create a temporary file for output
outfile = open('./tmp' + os.path.basename(sys.argv[1]) + '-maps.txt', 'w')

while 1:

  # read a line from the index file
  line = infile.readline()
  if not line:
	break
  line = line.split(' ')
  line = [a for a in line if a.isalnum()]
  
  # find the start of the maps
  if line.count(RAMAP) > 0:
	maptype = RAMAP
  elif line.count(DECMAP) > 0:
	maptype = DECMAP
  else:
    maptype = "None"
    continue

  sequence_number = int(line[7])
  last_sequence_number = sequence_number - 1
  lastscan = 0

  beginscan = line[8]
  while 1:
	if int(line[7]) > last_sequence_number+1:
		break
	elif int(line[7]) < last_sequence_number:
		break
	last_sequence_number = int(line[7])
	lastscan = int(line[8])
	line = infile.readline()
	if not line:
		break
	line = line.split(' ')
	line = [a for a in line if a.isalnum()]

  print  beginscan + ',' + str(lastscan)


infile.close()
