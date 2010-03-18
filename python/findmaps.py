#! /usr/bin/env python

"""Find the mapping procdures in an observation.

This module has routines to identify blocks of mapping procedures in an
SDFITS input file.

"""

import sys
import os.path

_ECHO = 0

# strings for map procedure names
_RAMAP = 'RALongMap'
_DECMAP = 'DecLatMap'

def _open_infile(indexfile):
    # open the index file
    if len(indexfile) > 1:
        infile = open(indexfile)
        if not file:
            print "Check input file"
    return infile

def _make_outfile(indexfile,map_types):
    outname = './' + os.path.basename(indexfile) + '-' + map_types + '-map-ranges.txt'
    outfile = open(outname, 'w')
    if not outfile:
        print "Could not create output file",outname
        sys.exit(1)
    return outfile

def _read_next_line(infile):
    # read a line from the index file
    line = infile.readline()
    if not line:  # usually end of file
        return False
    line = line.split(' ') # split on spaces
    line = [a for a in line if a.isalnum()] # reduce to only alhpanumerics
    return line

def _findrange(infile,outfile,line):
    # the sequence number should be monotonically increasing by 1
    sequence_number = int(line[7])
    last_sequence_number = sequence_number - 1
    lastscan = 0
    beginscan = line[8]
    while 1:
        # if the sequence number is > 1 more than the previous, stop
        if int(line[7]) > last_sequence_number+1:
            break
        # if the sequence number descreases, stop
        elif int(line[7]) < last_sequence_number:
            break
        last_sequence_number = int(line[7])
        lastscan = int(line[8])
        line = _read_next_line(infile)
        if False==line:  # usually end of file
            break
    range_string = beginscan + ',' + str(lastscan)
    outfile.write(range_string + '\n')
    if _ECHO:
        print  beginscan + ',' + str(lastscan)
  
def findmaps(indexfile):
    """Find all the mapping procdures in an observation.

    Look for an output file named
    i.e. AGBT07C_082_06.raw.acs.index-ralong-map-ranges.txt
    
    Keyword arguments:
    indexfile -- the GBTIDL-generated index file, for the
                 corresponding FITS file.

    """
    infile = _open_infile(indexfile)
    outfile = _make_outfile(indexfile,'all')

    while 1:
        line = _read_next_line(infile)
        if False==line:  # usually end of file
            break
    
        # find the start of the maps
        if line.count(_RAMAP) > 0:
            maptype = _RAMAP
        elif line.count(_DECMAP) > 0:
            maptype = _DECMAP
        else:
            maptype = "None"
            continue

        _findrange(infile,outfile,line)

    outfile.close()
    infile.close()

def find_ralong_maps(indexfile):
    """Find all the RA Long mapping procdures in an observation.

    Look for an output file named
    i.e. AGBT07C_082_06.raw.acs.index-ralong-map-ranges.txt

Keyword arguments:
    indexfile -- the GBTIDL-generated index file, for the
                 corresponding FITS file.

    """
    infile = _open_infile(indexfile)
    outfile = _make_outfile(indexfile,'ralong')

    while 1:
        line = _read_next_line(infile)
        if False==line:  # usually end of file
            break
    
        # find the start of the maps
        if line.count(_RAMAP) > 0:
            maptype = _RAMAP
        else:
            maptype = "None"
            continue

        _findrange(infile,outfile,line)

    outfile.close()
    infile.close()

def find_declat_maps(indexfile):
    """Find all the DEC Lat mapping procdures in an observation.

    Look for an output file named
    i.e. AGBT07C_082_06.raw.acs.index-declat-map-ranges.txt

Keyword arguments:
    indexfile -- the GBTIDL-generated index file, for the
                 corresponding FITS file.

    """
    infile = _open_infile(indexfile)
    outfile = _make_outfile(indexfile,'declat')

    while 1:
        line = _read_next_line(infile)
        if False==line:  # usually end of file
            break
    
        # find the start of the maps
        if line.count(_DECMAP) > 0:
            maptype = _DECMAP
        else:
            maptype = "None"
            continue

        _findrange(infile,outfile,line)

    outfile.close()
    infile.close()

if __name__ == "__main__":
    findmaps(sys.argv[1])
    find_ralong_maps(sys.argv[1])
    find_declat_maps(sys.argv[1])
    sys.exit(0)