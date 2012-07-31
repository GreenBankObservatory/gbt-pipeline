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
import sys

if __name__ == '__main__':
    
    # create instance of CommandLine object to parse input, then
    # parse all the input parameters and store them as attributes in param structure
    cl = commandline.CommandLine()
    cl_params = cl.read(sys)

    pipe = MappingPipeline(cl_params)
    
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

    feed=0
    window=0
    pol=0
    beam_scaling=1

    # -------------- reference 1
    scan=13
    refSpectrum1, refTsys1, refTimestamp1, refTambient1, refElevation1 = \
        pipe.getReference(scan, feed, window, pol)
    
    # -------------- reference 2
    scan=26
    refSpectrum2, refTsys2, refTimestamp2, refTambient2, refElevation2 = \
        pipe.getReference(scan, feed, window, pol)

    # -------------- calibrate signal scans
    mapscans = (14,15,16,17,18,19,20)
    #mapscans = (14,18)
    #mapscans = (14,)
        
    pipe.CalibrateSdfitsIntegrations( mapscans, feed, window, pol, \
            refSpectrum1, refTsys1, refTimestamp1, refTambient1, refElevation1, \
            refSpectrum2, refTsys2, refTimestamp2, refTambient2, refElevation2, \
            beam_scaling, units='ta' )
