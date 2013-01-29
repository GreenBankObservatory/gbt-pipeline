import numpy as np
import fitsio
import sys
import pylab as pl
import os

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

# from http://www.bdnyc.org/2012/10/15/decimal-deg-to-hms/
# convert decimal degrees to HMS format
def deg2HMS(ra='', dec='', round=False):
  RA, DEC, rs, ds = '', '', '', ''
  if dec:
    if str(dec)[0] == '-':
      ds, dec = '-', abs(dec)
    deg = int(dec)
    decM = abs(int((dec-deg)*60))
    if round:
      decS = int((abs((dec-deg)*60)-decM)*60)
    else:
      decS = (abs((dec-deg)*60)-decM)*60
    DEC = '{0}{1} {2} {3}'.format(ds, deg, decM, decS)
  
  if ra:
    if str(ra)[0] == '-':
      rs, ra = '-', abs(ra)
    raH = int(ra/15)
    raM = int(((ra/15)-raH)*60)
    if round:
      raS = int(((((ra/15)-raH)*60)-raM)*60)
    else:
      raS = ((((ra/15)-raH)*60)-raM)*60
    RA = '{0}{1} {2} {3}'.format(rs, raH, raM, raS)
  
  if ra and dec:
    return (RA, DEC)
  else:
    return RA or DEC

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

    LIGHT_SPEED = 299792458.0/1e3 # speed of light in a vacuum (km/s)
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

    infile = sys.argv[1]

    ff = fitsio.FITS(infile)
    hdr = fitsio.read_header(infile, 1)

    fignum = 0
    for ext in range(len(ff)):
	if 'nrows' in ff[ext].info:
            tdata = ff[ext].read()
	    for row in range(len(tdata)):
		if not np.all(np.isnan(tdata['DATA'][row])):
		    target_name = tdata['OBJECT'][row].strip()
                    projid = tdata['PROJID'][row].strip()
		    coord1name = tdata['CTYPE2'][row].strip()
		    coord1val = tdata['CRVAL2'][row]
		    coord2name = tdata['CTYPE3'][row].strip()
		    coord2val = tdata['CRVAL3'][row]
                    cv1,cv2 = deg2HMS(ra=coord1val, dec=coord2val, round=True)
		    fsky = tdata['CRVAL1'][row]/1e9
		    azimuth = tdata['AZIMUTH'][row]
		    elevation = tdata['ELEVATIO'][row]
		    lst = tdata['LST'][row]/1e9
		    tsys = tdata['TSYS'][row]
		    date = tdata['TIMESTAMP'][row]
                    restfreq = tdata['RESTFREQ'][row]/1e9
                    velocity = int(tdata['VELOCITY'][row]/1e3)
                    velframe = tdata['VELDEF'][row]

                    exposure = tdata['EXPOSURE'][row]
                    integ_h = int(exposure/3600.)
                    exposure -=  integ_h*3600
                    integ_m = int(exposure/60)
                    integ_s = exposure-integ_m*60
		    
                    scans = hdr['SCANLIST']

		    titlestring = (
                    'SCANS  {scans}\n'
                    'Project ID {pid}\n'
		    'Sky Frequency {fs:.3f} GHz\n'
                    'Rest Frequency {rf:.3f} GHz\n'
                    'Velocity {vel:d} km/s\n'
                    'Velocity reference frame {vframe}\n'
		    'Date {date}\n'
		    '{cn1}:{cv1}  {cn2}:{cv2}\n'
		    'AZ: {az:.1f}   EL: {el:.1f}\n'
                    'Integration time {hh:d} {mm:d} {ss:.1f}\n'
		    'Tsys {tsys:.2f}').format(
			pid=projid, fs=fsky, rf=restfreq, cn1=coord1name,
			cv1=cv1, cn2=coord2name, cv2=cv2, vel=velocity,
                        vframe=velframe, hh=integ_h, mm=integ_m, ss=integ_s,
			az=azimuth, el=elevation, tsys=tsys, date=date,
                        ex=exposure, scans=scans)
		    
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
		    
		    pl.savefig(os.path.splitext(sys.argv[1])[0]+'.png')
		    fignum += 1

    ff.close()
