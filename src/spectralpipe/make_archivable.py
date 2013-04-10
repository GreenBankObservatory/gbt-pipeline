"""Dump most of the contents of GBT Spectral Pipeline output for archive ingestion.

   This metadata is intended to be searchable with the Image Retreival Tool.  The
   metadata includes everyhthing except for the DATA column and some structural
   information about the table.

   The FITS output file consists only of some header keywords and a table with
   one row: a spectrum and some information about that spectrum.

"""
import fitsio
import sys
import numpy as np

def colval(tabledata, colname):
    """Print column=value information for a single column.
    """
    # SIG and CAL are stored as dtype(int8) and need to be
    #  converted to characters
    if colname in ('SIG','CAL'):
        value = chr(tabledata[0][colname])
    else: 
        value = tabledata[0][colname]

    return value

def hdrval(header, keyword):
    """Print keyword=value information for a single header keyword.
    """
    value = header.get(keyword)
    comment = header.get_comment(keyword)
    
    return value, comment

def openfile(filename, extension):
    """Get the header and data object for a given file and extension.
    """
    try:
        data, hdr = fitsio.read(filename, ext=extension, header=True)
    except Exception, e:
        print(e)
        sys.exit()

    return hdr, data

if __name__ == '__main__':

    FILENAME = sys.argv[1]  # grab the infile name

    # open the file and read the primary header w/data
    hdr, data = openfile(filename=FILENAME, extension=0)

    # get and print the header key(s) we care about
    for kw in ('DATE','ORIGIN','TELESCOP','GUIDEVER','FITSVER'):
        value, comment = hdrval(header=hdr, keyword=kw)
        print '{0} = {1} / {2}'.format(kw, value, comment)

    # open the file and read the 'SINGLE DISH' header w/data
    hdr, data = openfile(filename=FILENAME, extension='SINGLE DISH')

    # get and print the header key(s) we care about
    kw = 'SCANLIST'
    value, comment = hdrval(header=hdr, keyword=kw)
    print '{0} = {1} / {2}'.format(kw, value, comment)

    # get a list of the table column names
    cols_list = list(data.dtype.names)

    # remove the column(s) we don't want from the list.
    cols_list.remove('DATA')

    # get and pritn the value of each column
    for col in cols_list:
        value = colval( tabledata=data, colname=col) 
        print '{0} = {1}'.format(col, value)

