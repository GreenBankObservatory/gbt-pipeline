# Copyright (C) 2007 Associated Universities, Inc. Washington DC, USA.
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# 
# Correspondence concerning GBT software should be addressed as follows:
#       GBT Operations
#       National Radio Astronomy Observatory
#       P. O. Box 2
#       Green Bank, WV 24944-0002 USA

# $Id$

import commandline
from MappingPipeline import MappingPipeline
from SdFitsIO import SdFits

import fitsio

import multiprocessing
import sys

def calibrateWindowFeedPol(cl_params, window, feed, pol, rowList):

    pipe = MappingPipeline(cl_params, rowList)
    
    refSpectrum1 = None
    refTsys1 = None
    refTimestamp1 = None
    refTambient1 = None
    refElevation1 = None
    refSpectrum2 = None
    refTsys2 = None
    refTimestamp2 = None
    refTambient2 = None
    refElevation2 = None
    
    # -------------- reference 1
    if cl_params.refscans:

        try:
            pipe.rowList.get(cl_params.refscans[0], feed, window, pol)
        except:
            print 'ERROR: missing 2nd reference scan #',cl_params.refscans[0],'for feed',feed,'window',window,'polarization',pol
            return
        
        refSpectrum1, refTsys1, refTimestamp1, refTambient1, refElevation1 = \
            pipe.getReference(cl_params.refscans[0], feed, window, pol)
        
        if len(cl_params.refscans)>1:
            # -------------- reference 2
            try:
                pipe.rowList.get(cl_params.refscans[1], feed, window, pol)
            except:
                print 'ERROR: missing 2nd reference scan #',cl_params.refscans[1],
                print 'for feed',feed,'window',window,'polarization',pol
                return
            
            refSpectrum2, refTsys2, refTimestamp2, refTambient2, refElevation2 = \
                pipe.getReference(cl_params.refscans[1], feed, window, pol)

    # -------------- calibrate signal scans
    if 1 != cl_params.gainfactors:
        try:
            beam_scaling = cl_params.gainfactors[feed+pol]
        except IndexError:
            print 'ERORR: can not get a gainfactor for feed and polarization.',feed
            print '  You need to supply a factor for each feed and'
            print '  polarization for the receiver.'
    else:
        beam_scaling = cl_params.gainfactors
    
    pipe.CalibrateSdfitsIntegrations( feed, window, pol,\
            refSpectrum1, refTsys1, refTimestamp1, refTambient1, refElevation1, \
            refSpectrum2, refTsys2, refTimestamp2, refTambient2, refElevation2, \
            beam_scaling )
    
def runPipeline():

    # create instance of CommandLine object to parse input, then
    # parse all the input parameters and store them as attributes in param structure
    cl = commandline.CommandLine()
    cl_params = cl.read(sys)

    
    feeds=cl_params.feed
    pols=cl_params.pol
    windows=cl_params.window
    
    sdf = SdFits()
    indexfile = sdf.nameIndexFile( cl_params.infilename )
    rowList = sdf.parseSdfitsIndex( indexfile )
    
    if not feeds:
        feeds = rowList.feeds()
    if not pols:
        pols = rowList.pols()
    if not windows:
        windows = rowList.windows()
    
    #print 'windows',', '.join([str(xx) for xx in windows])
    #print 'feeds',', '.join([str(xx) for xx in feeds])
    #print 'pols',', '.join([str(xx) for xx in pols])
    #if cl_params.refscans:
    #    print 'refscans',', '.join([str(xx) for xx in cl_params.refscans[:2]])
    
    for window in windows:
        for feed in feeds:
            for pol in pols:
                
                p = multiprocessing.Process(target=calibrateWindowFeedPol, args=(cl_params, window, feed, pol, rowList,))
                #calibrateWindowFeedPol(cl_params, pipe, window, feed, pol)
                p.start()
                #raw_input()

if __name__ == '__main__':
    
    runPipeline()
    