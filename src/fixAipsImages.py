# Copyright (C) 2013 Associated Universities, Inc. Washington DC, USA.
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


# Routine to fix AIPS images so that they can be correctly processed by AIPS
# By default, this leaves RESTFREQ alone and adjusts the FREQ axis, which
# is expected to be axis 3 to match either the value implied by the SDFITS
# VELDEF value found in the HISTORY or the VELREF keyword if there is no
# SDFITS VELDEF history value.
#
# RESTFREQ and the FREQ reference frame can be optionally supplied by the
# user (useful to correct images before the RESTFREQ bug was fixed).
#
# If the 3rd axis is not FREQ* then this aborts without changing anything.
#
# If the user has not supplied a reference frame and there is no VELDEF
# value found in the history and the VELREF implies "OBS", then a warning
# message is printed that the frequency axis may not be correct.
#
# Recognized user-supplied frames are "TOP", "LSR", "BAR", "HEL", "LSD",
# "GEO", "GAL", "LGR", and "COB" (those are the ones used by the GBT).
# In the case of "LGR" and "COB" the VELDEF and ALTRPIX keywords will be
# removed as there is no corresponding VELDEF code for those cases.
# Any other type is an error.  "HEL" and "BAR" are treated as the same
# frame. "OBS" can be used in place of "TOP".

import pyfits
import os
import sys
import string


def fixAipsImages(fitsFiles, refFrame=None, restFreq=None):

    kwWarning = False
    for fitsFile in fitsFiles:
        if not os.path.exists(fitsFile):
            print "fixAipsImages could not find %s" % fitsFile
            continue

        try:
            f = pyfits.open(fitsFile, mode='update', memmap=True)
        except:
            print "fixAipsImages could not open %s" % fitsFile
            continue

        if refFrame is None:
            hists = f[0].header.get_history()
            veldefs = [x for x in hists if 'VELDEF' in x]
            if len(veldefs) > 0:
                veldefHist = veldefs[0].split()
                if len(veldefHist) == 4 and veldefHist[0] == 'SDFITS':
                    # looks OK to use
                    veldefVal = veldefHist[3][1:-1]
                    refFrame = veldefVal[5:8]

        if refFrame is None:
            # could not find a valid SDFITS VELDEF history
            if 'VELREF' in f[0].header:
                vref = f[0].header['velref']
                if vref > 255:
                    vref = vref-256

                if vref == 1:
                    refFrame = 'LSR'
                elif vref == 2:
                    refFrame = 'HEL'
                elif vref == 3:
                    refFrame = 'OBS'

                if refFrame is None:
                    print 'fixAipsImages unable to find a default frequency reference frame in %s' % fitsFile
                if refFrame == 'OBS':
                    print "fixAipsImages default reference frame is topocentric from the VELREF keyword."
                    print "   That may be incorrect.  %s " % fitsFile

        # time to set things
        if refFrame is not None:
            if 'CTYPE3' not in f[0].header or f[0].header['CTYPE3'][0:4] != 'FREQ':
                print "fixAipsImages: the 3rd axis does not exist or is not a frequency axis in %s" % fitsFile
            else:
                refCode = None
                if refFrame == "LSR":
                    refCode = 1
                elif refFrame == "BAR" or refFrame == "HEL":
                    refFrame = "HEL"
                    refCode = 2
                elif refFrame == "TOP" or refFrame == "OBS":
                    refCode = 3
                    refFrame = "TOP"
                elif refFrame == "LSD":
                    refCode = 4
                elif refFrame == "GEO":
                    refCode = 5
                elif refFrame == "GAL":
                    refCode = 7
                elif refFrame == "LGR" or refFrame == "COB":
                    refCode = -1

                # refCode = 6 is the SOURCE frame which is not available at the GBT
                # LGR and COB have no refCode but are valid GBT frames
                if refCode is None:
                    print "fixAipsImages: unrecognized reference frame.  See -h for help. %s" % refFrame
                    return

                f[0].header['CTYPE3'] = 'FREQ-'+refFrame

                if 'VELREF' in f[0].header:
                    # make sure they agree
                    if refCode > 0:
                        if f[0].header['VELREF'] > 256:
                            refCode += 256
                        f[0].header['VELREF'] = refCode
                    else:
                        if not kwWarning:
                            print "fixAipsImages: reference frame incompatible with VELREF, ALRPIX.  Removing those keywords."
                            kwWarning = True
                        del f[0].header['VELREF']
                        del f[0].header['ALTRPIX']

        if restFreq is not None:
            f[0].header['RESTFREQ'] = restFreq

        f.close()


def usage():
    print """usage:
    fixAipsImages [OPTIONS] FITS_FILES[s]

fixAipsImages resets the reference frame part of the frequency axis
(CTYPE3) and optionally the RESTFREQ value in FITS image cubes made
by AIPS as part of the gbtpipeline.

Previous FITS cubes produced by the gbtpipeline are missing any
reference frame information for the frequency axis.  Consumers of
those cubes may incorrectly assume a topocentric reference frame.
Additionally, the recorded RESTFREQ (rest frequency) may be incorrect
for the line (baseline subtracted) and cont (continuum) images.

FITS_FILE[s] is a list of FITS files to attempt to fix. These are
fixed in place so copies should be made if you wish to preserve them
in their unfixed state.

OPTIONS
   -refframe=FRAME
        The 3-letter code for the desired reference frame (e.g. "LSR").
        Valid codes are LSR, BAR, HEL, TOP, OBS, LSD, GEO, GAL, LGR, and COB.
        BAR and HEL are treated as equivalent.  TOP and OBS are the same frame.
        LGR and COB can not be represented using the AIPS VELREF and ALTRPIX
        syntax and so in that case those keywords will be deleted by this
        routine.
        If not supplied the HISTORY will be searched for SDFITS VELDEF
        values and the first such match will be used.  If there are no
        SDFITS VELDEF values found then the VELREF keyword will be used.
        Note that VELREF can only have 3 values (+256 for RADIO velocities):
        corresponding to LSR, HEL and OBS frames.  The frequency
        information for other frames was correctly handled by the gbtpipeline
        but will be incorrectly labelled in VELREF as type 3, OBS (topocentric).
        A warning message will be printed if VELREF is used and it implies
        the OBS frame.

   -restfreq=RESTFREQ
        The desired rest frequency, in Hz.
        If not supplied, RESTFREQ will be unchanged.

   -h
        This information.
   """


def doFixAipsImages():

    aipsImages = []
    restFreq = None
    refFrame = None

    for arg in sys.argv[1:]:
        if arg == "-h":
            usage()
            return

        if arg[0] == "-":
            if '=' not in arg:
                print "Unrecognized option '%s'.  Use -h for help" % arg
                return

            k, v = string.split(arg, '=')
            if k == "-refframe":
                if len(v) != 3:
                    print "refframe must have 3 letters: %s" % v
                    return
                refFrame = v
            elif k == "-restfreq":
                restFreq = float(v)
            else:
                print "Unrecognized option '%s'  Use -h for help." % k
                return

        else:
            aipsImages.append(arg)

    if len(aipsImages) == 0:
        usage()
        return

    fixAipsImages(aipsImages, refFrame=refFrame, restFreq=restFreq)

if __name__ == "__main__":
    doFixAipsImages()
