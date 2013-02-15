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
    else:
      ds = '+'
    deg = int(dec)
    decM = abs(int((dec-deg)*60))
    if round:
      decS = int((abs((dec-deg)*60)-decM)*60)
    else:
      decS = (abs((dec-deg)*60)-decM)*60
    DEC = '{0}{1:02d} {2:02d} {3:02d}'.format(ds, deg, decM, decS)
  
  if ra:
    if str(ra)[0] == '-':
      rs, ra = '-', abs(ra)
    raH = int(ra/15)
    raM = int(((ra/15)-raH)*60)
    if round:
      raS = int(((((ra/15)-raH)*60)-raM)*60)
    else:
      raS = ((((ra/15)-raH)*60)-raM)*60
    RA = '{0}{1:02d} {2:02d} {3:02.1f}'.format(rs, raH, raM, raS)
  
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
#    case veldef of
#        'RADIO': result = !gc.light_speed * (1.0d - double(freq) / restfreq)
#        'OPTICAL': result = !gc.light_speed * (restfreq / double(freq) - 1.0d)
#        'TRUE': begin
#            g = (double(freq) / restfreq)^2
#            result = !gc.light_speed * (1.0d - g) / (1.0d + g)
#        end
#        else: message, 'unrecognized velocity definition'
#    endcase 

def freqtovel(freq, restfreq, veldef='RADIO'):
    LIGHT_SPEED = 299792458.0 / 1e3 # speed of light in a vacuum (km/s)
    freq = float(freq)
    restfreq = float(restfreq)

    if veldef.startswith('RADI'):
        result = LIGHT_SPEED * (1 - freq/restfreq)
    elif veldef.startswith('OPTI'):
        result = LIGHT_SPEED * (restfreq/freq - 1)
    elif veldef.startswith('RELA'):
        gg = (freq / restfreq)**2
        result = LIGHT_SPEED * (1 - gg) / (1 + gg)
    else:
        print 'unrecognized velocity definition'

    return result

if __name__ == '__main__':

    infile = sys.argv[1]

    ff = fitsio.FITS(infile)
    hdr = fitsio.read_header(infile, 1)

    for ext in range(len(ff)):
	if 'nrows' in ff[ext].info:
            tdata = ff[ext].read()
	    for row in range(len(tdata)):
		target_name = tdata['OBJECT'][row].strip()
                projid = tdata['PROJID'][row].strip()
                scans = hdr['SCANLIST']
		if not np.all(np.isnan(tdata['DATA'][row])):
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
		    date = tdata['TIMESTAMP'][row].strip().replace('_','-',2).replace('_',' ') + ' UT'
                    restfreq = tdata['RESTFREQ'][row]/1e9
                    velocity = int(tdata['VELOCITY'][row]/1e3)
		    veldef = tdata['VELDEF'][row]

                    exposure = tdata['EXPOSURE'][row]
                    integ_h = int(exposure/3600.)
                    exposure -=  integ_h*3600
                    integ_m = int(exposure/60)
                    integ_s = exposure-integ_m*60
		    

		    titlestring1 = (
                    'Project ID: {pid}\n'
		    'Sky Frequency:  {fs:7.3f} GHz\n'
                    'Rest Frequency: {rf:7.3f} GHz\n'
                    'Velocity: {vel:d} km/s {vframe}\n'
                    'Effective Tint: {hh:d}h {mm:d}m {ss:.1f}s').format(
			pid=projid, fs=fsky, rf=restfreq,
                        hh=integ_h, mm=integ_m, ss=integ_s, 
			vel=velocity, vframe=veldef)

		    titlestring2 = (
                    'Scans: {scans}\n'
                    'Date: {date}\n'\
                    '{cv1}, {cv2} J2000\n'
		    'AZ: {az:.1f}, EL: {el:.1f}\n'
		    'Tsys: {tsys:.2f} K').format(
			cn1=coord1name,	cv1=cv1, cn2=coord2name, cv2=cv2,
                        date=date,
			az=azimuth, el=elevation, tsys=tsys,
                        scans=scans)
		    
                    pl.figure(figsize=(8,4))
		    ax = pl.subplot(212)
		   
                    vdatafile = os.path.splitext(sys.argv[1])[0]+'.vdata'
                    veldata = np.loadtxt(vdatafile, skiprows=3)
                    os.unlink(vdatafile)
                    velo = veldata[:,0]
                    data = veldata[:,1]

                    # Scale the y-axis to mJy if the peak is < 100 mJy, and to Jy if it is > 100 mJy
                    if np.ma.masked_invalid(data).max() <= .1:
		        pl.plot(velo,data*1000)
	                pl.ylabel('Flux Density (mJy)')
                    else:
		        pl.plot(velo,data)
	                pl.ylabel('Flux Density (Jy)')
		    
		    pl.title(target_name+'\n')

                    vdef, refframe = veldef.split('-')
                    vdefs = {'RADI':'Radio', 'OPTI':'Optical', 'RELA':'Relativistic'}
		    pl.xlabel('\n' + refframe.title() + ' ' + vdefs[vdef] + ' Velocity (km/s)')

		    # create a subplot with no border or tickmarks
		    ax = pl.subplot(221, frame_on=False, navigate=False, axisbelow=False)
		    ax.xaxis.set_ticklabels([None])
		    ax.yaxis.set_ticklabels([None])
		    ax.xaxis.set_ticks([None])
		    ax.yaxis.set_ticks([None])                
		    pl.text(.1,.05,titlestring1, size=10, family='monospace')

		    # create a subplot with no border or tickmarks
		    ax = pl.subplot(222, frame_on=False, navigate=False, axisbelow=False)
		    ax.xaxis.set_ticklabels([None])
		    ax.yaxis.set_ticklabels([None])
		    ax.xaxis.set_ticks([None])
		    ax.yaxis.set_ticks([None])                
		    pl.text(.1,.05,titlestring2, size=10, family='monospace')
	    
                else:
                    pl.figure(figsize=(8,4))
                    pl.subplot(212)
                    ax = pl.subplot(211, frame_on=False, navigate=False, axisbelow=False)
		    ax.xaxis.set_ticklabels([None])
		    ax.yaxis.set_ticklabels([None])
		    ax.xaxis.set_ticks([None])
		    ax.yaxis.set_ticks([None])
                    errorstring = 'Data not calibrated because there were multiple \nscans with the same scanid when observing this target.'
                    pl.text(0, 0,'\n'.join((target_name, projid, scans, errorstring)), size=10)

                pl.subplots_adjust(top=1.2, bottom=.15)
                pl.savefig(os.path.splitext(sys.argv[1])[0]+'.png')
    ff.close()
