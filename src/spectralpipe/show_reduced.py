import numpy as np
import fitsio
import sys
import pylab as pl
import os

# from http://www.bdnyc.org/2012/10/15/decimal-deg-to-hms/
# convert decimal degrees to HMS format
def deg2hms(ra='', dec='', doRound=False):
    RA, DEC, rs, ds = '', '', '', ''
    if dec:
        if str(dec)[0] == '-':
            ds, dec = '-', abs(dec)
    else:
        ds = '+'
    deg = int(dec)
    decM = abs(int((dec-deg)*60))
    if doRound:
        decS = int((abs((dec-deg)*60)-decM)*60)
    else:
        decS = (abs((dec-deg)*60)-decM)*60
    DEC = '{0}{1:02d} {2:02d} {3:02d}'.format(ds, deg, decM, decS)
  
    if ra:
        if str(ra)[0] == '-':
            rs, ra = '-', abs(ra)
        raH = int(ra/15)
        raM = int(((ra/15)-raH)*60)
        if doRound:
            raS = int(((((ra/15)-raH)*60)-raM)*60)
        else:
            raS = ((((ra/15)-raH)*60)-raM)*60
        RA = '{0}{1:02d} {2:02d} {3:02.1f}'.format(rs, raH, raM, raS)
  
    if ra and dec:
        return (RA, DEC)
    else:
        return RA or DEC

if __name__ == '__main__':

    infile = sys.argv[1]

    ff = fitsio.FITS(infile)
    hdr = fitsio.read_header(infile, 1)

    tdata = ff[1].read()

    target_name = tdata['OBJECT'][0].strip()
    projid = tdata['PROJID'][0].strip()
    scans = hdr['SCANLIST']

    # if the data is not blank
    if not np.all(np.isnan(tdata['DATA'][0])):
        coord1name = tdata['CTYPE2'][0].strip()
        coord1val = tdata['CRVAL2'][0]
        coord2name = tdata['CTYPE3'][0].strip()
        coord2val = tdata['CRVAL3'][0]
        cv1, cv2 = deg2hms(ra=coord1val, dec=coord2val, doRound=True)
        fsky = tdata['CRVAL1'][0]/1e9
        azimuth = tdata['AZIMUTH'][0]
        elevation = tdata['ELEVATIO'][0]
        lst = tdata['LST'][0]/1e9
        tsys = tdata['TSYS'][0]
        date = tdata['TIMESTAMP'][0].strip().replace('_', '-', 2).replace('_', ' ') + ' UT'
        restfreq = tdata['RESTFREQ'][0]/1e9
        velocity = int(tdata['VELOCITY'][0]/1e3)
        veldef = tdata['VELDEF'][0]

        exposure = tdata['EXPOSURE'][0]
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
        cn1=coord1name, cv1=cv1, cn2=coord2name, cv2=cv2,
        date=date,
        az=azimuth, el=elevation, tsys=tsys,
        scans=scans)
        
        pl.figure(figsize=(8, 4))
        ax = pl.subplot(212)
       
        vdatafile = os.path.splitext(sys.argv[1])[0]+'.vdata'
        veldata = np.loadtxt(vdatafile, skiprows=3)
        os.unlink(vdatafile)
        velo = veldata[:, 0]
        data = veldata[:, 1]

        # Scale the y-axis to mJy if the peak is < 100 mJy, and to Jy if
        #  it is > 100 mJy
        if np.ma.masked_invalid(data).max() <= .1:
            pl.plot(velo, data*1000)
            pl.ylabel('Flux Density (mJy)')
        else:
            pl.plot(velo, data)
            pl.ylabel('Flux Density (Jy)')
        
        pl.title(target_name+'\n')

        vdef, refframe = veldef.split('-')
        vdefs = {'RADI':'Radio', 'OPTI':'Optical', 'RELA':'Relativistic'}
        pl.xlabel('\n' + refframe.title() + ' ' + vdefs[vdef] +
                  ' Velocity (km/s)')

        # create a subplot with no border or tickmarks
        ax = pl.subplot(221, frame_on=False, navigate=False, axisbelow=False)
        ax.xaxis.set_ticklabels([None])
        ax.yaxis.set_ticklabels([None])
        ax.xaxis.set_ticks([None])
        ax.yaxis.set_ticks([None])                
        pl.text(.1, .05, titlestring1, size=10, family='monospace')

        # create a subplot with no border or tickmarks
        ax = pl.subplot(222, frame_on=False, navigate=False, axisbelow=False)
        ax.xaxis.set_ticklabels([None])
        ax.yaxis.set_ticklabels([None])
        ax.xaxis.set_ticks([None])
        ax.yaxis.set_ticks([None])                
        pl.text(.1, .05, titlestring2, size=10, family='monospace')

    else:
    # if the data is blank

        pl.figure(figsize=(8, 4))
        pl.subplot(212)
        ax = pl.subplot(211, frame_on=False, navigate=False, axisbelow=False)
        ax.xaxis.set_ticklabels([None])
        ax.yaxis.set_ticklabels([None])
        ax.xaxis.set_ticks([None])
        ax.yaxis.set_ticks([None])
        errorstring = ( '\nData not calibrated because scans pairs were bad\n '
                        'or all integrations were flagged.' )
        pl.text(0, 0, '\n'.join((target_name, projid, scans, errorstring)), size=10)

    pl.subplots_adjust(top=1.2, bottom=.15)
    pl.savefig(os.path.splitext(sys.argv[1])[0]+'.png')

    ff.close()
