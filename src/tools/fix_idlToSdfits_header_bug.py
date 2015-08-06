import os
import sys
import pyfits
import argparse

parser = argparse.ArgumentParser(description="""
This is a tool to correct FITS cubes that have a systematic offset of
channel frequencies, after averaging, which was introduced by the
idlToSdfits program prior to May 8, 2015 (i.e. prior to v8.6).

The correction is applied to the header keywords 'CRVAL3' and
'ALTRPIX'.

Please make sure you know and supply the channel width used for
averaging when creating the cube or the correction will be inaccurate.
""")

# if no options are set, print help
if len(sys.argv) == 1:
    sys.argv.append('-h')

parser.add_argument('cube', type=str, help='The filename of the image cube that needs to be fixed.')
parser.add_argument('chan_width', type=int, help='The number of channels averaged with idlToSdfits when creating the image cube.')
args = parser.parse_args()

print ''
print 'Input cube name:', args.cube
print 'Channel width used for averaging:', args.chan_width
print ''

fd = pyfits.open(args.cube, mode='update', memmap=True)

nchan = fd[0].header['naxis3']
history = fd[0].header['HISTORY']

scriptname = os.path.basename(__file__)

alreadyFixed = False
for hh in history:
    if scriptname in hh:
        alreadyFixed = True
        break

if alreadyFixed:
    print 'ERROR: It appears that this cube was already fixed using this tool.'
    sys.exit(3)

found_writeSdfits = False
for hh in history:
    if 'writeSdfits' in hh:
        found_writeSdfits = True
        break

if not found_writeSdfits:
    print 'ERROR: It appears that this cube was not created with the old version of idlToSdfits'
    print '       because the writeSdfits history card was not found in the header.'
    sys.exit(1)

if not (1 < args.chan_width < nchan):
    print 'ERROR: Please supply a channel width between 1 and the number of channels in the cube.'
    sys.exit(2)

pixOffset = 0.5 - 0.5/args.chan_width
offset = fd[0].header['CDELT3'] * pixOffset

crval3 = fd[0].header['CRVAL3']
fd[0].header['CRVAL3'] = fd[0].header['CRVAL3'] - offset
history_message = '{tool} CRVAL3: {old} to {new}'.format(tool=scriptname, old=crval3, new=fd[0].header['CRVAL3'])
print 'Updating {key} from {old} to {new}'.format(key='CRVAL3', old=crval3, new=fd[0].header['CRVAL3'])
fd[0].header.add_history(history_message)

altrpix = fd[0].header['ALTRPIX']
fd[0].header['ALTRPIX'] = fd[0].header['ALTRPIX'] + pixOffset
history_message = '{tool} ALTRPIX: {old} to {new}'.format(tool=scriptname, old=altrpix, new=fd[0].header['ALTRPIX'])
print 'Updating {key} from {old} to {new}'.format(key='ALTRPIX', old=altrpix, new=fd[0].header['ALTRPIX'])
fd[0].header.add_history(history_message)

fd.close()
