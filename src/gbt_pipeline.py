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

PARALLEL = True # useful to turn off when debugging

import commandline
from MappingPipeline import MappingPipeline
from SdFitsIO import SdFits

import fitsio
from blessings import Terminal

import multiprocessing
import sys
import pprint

def calibrateWindowFeedPol(cl_params, window, feed, pol, pipe, printOffset):

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
            beam_scaling, printOffset )
    
def printTableHeader(term, start):
    print term.clear()
    for xx in range(term.height):
        print

    with term.location(x=0, y=start+0):
        print '{t.bold}progress by scan number{t.normal}'.format(t=term),
    with term.location(x=0, y=start+2):
        print '{t.bold}window |{t.normal} {t.bold}feed{t.normal}'.format(t=term),
    with term.location(x=0, y=start+3):
        print '{t.bold}{!s}{t.normal}'.format('-'*90,t=term)
    sys.stdout.flush()

    
def runPipeline(term, start):

    #printTableHeader(term, start)

    # create instance of CommandLine object to parse input, then
    # parse all the input parameters and store them as attributes in param structure
    cl = commandline.CommandLine()
    cl_params = cl.read(sys)
    
    with term.location(0,0):
	print cl_params

    with term.location(0,term.height-1):
        raw_input('{t.bold}Press enter to continue.{t.normal}'.format(t=term))
	print term.clear()
    
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
    
    pids = []
    pipe = []
    
    for window in windows:
        for feed in feeds:
            for pol in pols:
                try:
                    mp = MappingPipeline(cl_params, rowList, feed, window, pol, term, start)
                except KeyError:
                    continue
                pipe.append( (mp, window, feed, pol) )
    
    for ww in windows:
        with term.location(0, start + ww*(len(feeds)+1)):
            print '{t.bold}window {window:2d}{t.normal}'.format(window=ww,t=term),

    for idx, pp in enumerate(pipe):
        
        window = pp[1]
        feed = pp[2]
        pol = pp[3]
        
        #with term.location(x=14+feed*10, y=start+2):
        #    print '{feed:4d}'.format(feed=feed),
        #with term.location(x=0, y=start+4+window):
        #    print '{:<7d}{t.bold}|{t.normal}'.format(window,t=term),
                
        #sys.stdout.flush()
        
        # pipe output will be printed in order of window, feed
        if PARALLEL:
            p = multiprocessing.Process(target=calibrateWindowFeedPol, args=(cl_params, window, feed, pol, pp[0], idx,))
            pids.append(p)

        else:
                calibrateWindowFeedPol(cl_params, window, feed, pol, pp[0], idx)

    if PARALLEL:
        for pp in pids:
	    pp.start()
    
        for pp in pids:
            pp.join()

    with term.location(0,term.height-2):
        print 'calibration all done, start imaging'

if __name__ == '__main__':

    term = Terminal()
    start = 0
    
    with term.fullscreen():
        runPipeline(term,start)
	with term.location(0,term.height-1):
	    raw_input( '{t.bold}Press enter to exit.{t.normal}'.format(t=term) )
