import numpy as np
import fitsio
import sys
import pylab as pl
from scipy import constants

def freq_axis(data,verbose=0):
    """ frequency axis to return for plotting

    Keyword arguments:
    data
    
    Returns:
    A frequency axis vector for the scan.
    """
    
    # apply sampler filter
    crpix1 = data['CRPIX1']
    cdelt1 = data['CDELT1']
    crval1 = data['CRVAL1']

    faxis = np.zeros(len(data['DATA']))
    for chan,ee in enumerate(data['DATA']):
        faxis[chan] = (chan-crpix1) * cdelt1 + crval1

    return faxis

# Convert frequency to velocity (m/s) using the given rest
# frequency and velocity definition.  The units (Hz, MHz, GHz, etc)
# of the frequencies to convert must match that of the rest frequency 
# argument.
#
# @param freq {in}{required} Frequency. Units must be the same as 
# the units of restfreq.
# @param restfreq {in}{required} Rest frequency.  Units must be the
# same as those of freq.
# @keyword veldef {in}{optional}{type=string} The velocity definition
# which must be one of OPTICAL, RADIO, or TRUE.  Defaults to RADIO.
#
# @returns velocity in m/s
def freqtovel(freq, restfreq, veldef='RADIO'):

    LIGHT_SPEED = constants.c/1e3 # km/s
    freq = float(freq)
    restfreq = float(restfreq)
    
    #print '[{vd}]'.format(vd=veldef)
    if veldef.startswith('RADI'):
        result = LIGHT_SPEED * ((restfreq - freq) / restfreq)
    elif veldef.startswith('OPTI'):
        result = LIGHT_SPEED * (restfreq / (freq - restfreq))
    elif veldef.startswith('RELA'):
        gg = (freq / restfreq)**2
        result = LIGHT_SPEED * ((restfreq - gg) / (restfreq + gg))
    else:
        print 'unrecognized velocity definition'

    return result

if __name__ == '__main__':

    ff = fitsio.FITS(sys.argv[1])

    fignum = 0
    for ext in range(len(ff)):
	if 'nrows' in ff[ext].info:
            tdata = ff[ext].read()
	    for row in range(len(tdata)):
		if not np.all(np.isnan(tdata['DATA'][row])):
		    target_name = tdata['OBJECT'][row].strip()
		    bandwidth = tdata['BANDWID'][row]/1e6
		    procname = tdata['OBSMODE'][row].strip().split(':')[0]
		    coord1name = tdata['CTYPE2'][row].strip()
		    coord1val = tdata['CRVAL2'][row]
		    coord2name = tdata['CTYPE3'][row].strip()
		    coord2val = tdata['CRVAL3'][row]
		    fsky = tdata['CRVAL1'][row]/1e9
		    azimuth = tdata['AZIMUTH'][row]
		    elevation = tdata['ELEVATIO'][row]
		    lst = tdata['LST'][row]/1e9
		    tsys = tdata['TSYS'][row]
		    date = tdata['DATE-OBS'][row]
		    
		    titlestring = (
		    'Bandwidth: {bw:.2f} MHz\n'
		    'Procedure: {pn}\n'
		    'Sky Frequency {fs:.3f} GHz\n'
		    'Date {date}\n'
		    '{cn1}:{cv1:.1f}  {cn2}:{cv2:.1f}\n'
		    'AZ: {az:.1f}   EL: {el:.1f}\n'
		    'Tsys {tsys:.2f}').format(
			bw=bandwidth, pn=procname, fs=fsky, cn1=coord1name,
			cv1=coord1val, cn2=coord2name, cv2=coord2val,
			az=azimuth, el=elevation, tsys=tsys, date=date)
		    
		    fig = pl.figure(fignum)

		    ax = pl.subplot(212)
		   
		    freq = freq_axis(tdata[row])
		    restfreq = tdata['RESTFREQ'][row]
		    veldef = tdata['VELDEF'][row]
		    velo = np.array([freqtovel(fidx,restfreq) for fidx in freq])
		    
		    data = tdata['DATA'][row]
		    pl.plot(velo,data)
		    
		    pl.title(target_name)
		    pl.ylabel('Jy')
		    pl.xlabel('km/s')

		    # create a subplot with no border or tickmarks
		    ax = pl.subplot(211, frame_on=False, navigate=False, axisbelow=False)
		    ax.xaxis.set_ticklabels([None])
		    ax.yaxis.set_ticklabels([None])
		    ax.xaxis.set_ticks([None])
		    ax.yaxis.set_ticks([None])                
		    pl.text(0,.1,titlestring,size=10)
		    
		    pl.savefig(sys.argv[1]+'_'+str(fignum)+'.png')
		    fignum += 1

    ff.close()
