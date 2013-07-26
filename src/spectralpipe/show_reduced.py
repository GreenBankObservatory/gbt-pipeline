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
            ds, dec = '+', abs(dec)
    deg = int(dec)
    decM = abs(int((dec-deg)*60))
    if doRound:
        decS = int((abs((dec-deg)*60)-decM)*60)
    else:
        decS = (abs((dec-deg)*60)-decM)*60
    DEC = '{0}{1:02d}:{2:02d}:{3:02d}'.format(ds, deg, decM, decS)
  
    if ra:
        if str(ra)[0] == '-':
            rs, ra = '-', abs(ra)
        raH = int(ra/15)
        raM = int(((ra/15)-raH)*60)
        if doRound:
            raS = int(((((ra/15)-raH)*60)-raM)*60)
        else:
            raS = ((((ra/15)-raH)*60)-raM)*60
        RA = '{0}{1:02d}:{2:02d}:{3:02.1f}'.format(rs, raH, raM, raS)
  
    if ra and dec:
        return (RA, DEC)
    else:
        return RA or DEC

if __name__ == '__main__':

    # grab the SDFITS output spectrum file name
    infile = sys.argv[1]

    # the velocity axis file is inferred from the SDFITS file name
    vdatafile = os.path.splitext(infile)[0]+'.vdata'

    ff = fitsio.FITS(infile)  # open the SDFITS file
    hdr = fitsio.read_header(infile, 1)  # grab the header structure

    tdata = ff[1].read()  # read the table data (only 1 row)

    # get some metadata from a couple of table fields
    #  to add to the plot header
    target_name = tdata['OBJECT'][0].strip()
    projid = tdata['PROJID'][0].strip()
    scans = hdr['SCANLIST'] # this key was added by the pipeline

    # if the data is not blank
    if not np.all(np.isnan(tdata['DATA'][0])):

        # get a lot more info for the plot header
        # note that all of this data is coming from the table fields
        # and not the SDFITS header.  it doesn't really matter that
        # it's coming from the table.  it just happens that what we
        # we want on the plot is in the table.
        coord1name = tdata['CTYPE2'][0].strip()
        coord1val = tdata['CRVAL2'][0]
        coord2name = tdata['CTYPE3'][0].strip()
        coord2val = tdata['CRVAL3'][0]
        # convert coordinates from degrees to hms notation
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
        # get the exposure time and display it as hms
        exposure = tdata['EXPOSURE'][0]
        integ_h = int(exposure/3600.)
        exposure -=  integ_h*3600
        integ_m = int(exposure/60)
        integ_s = exposure-integ_m*60
        
        # now put all of that data into strings for the plot header

        titlestring1 = (  # left side of the plot header
        'Project ID: {pid}\n'
        'Scans: {scans}\n'
        'Date: {date}\n'\
        'Eff Int Time: {hh:d}h {mm:d}m {ss:.1f}s\n'
        'Tsys: {tsys:.2f} K').format(
        pid=projid,
        scans=scans, 
        date=date,
        hh=integ_h, mm=integ_m, ss=integ_s, 
        tsys=tsys )

        titlestring2 = (  # right side of the plot header
        '{cv1} {cv2} J2000\n'
        'AZ: {az:.1f}, EL: {el:.1f}\n'
        'Rest Frequency: {rf:7.3f} GHz\n'
        'Sky Frequency:  {fs:7.3f} GHz\n'
        'Velocity: {vel:d} km/s {vframe}\n'
        ).format(
        cv1=cv1, cv2=cv2,
        az=azimuth, el=elevation,
        fs=fsky,
        rf=restfreq,
        vel=velocity, vframe=veldef)
        
        
        pl.figure(figsize=(8, 4))
        ax = pl.subplot(212)
       
        veldata = np.loadtxt(vdatafile, skiprows=3)
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

        # retrieve the git commit hash for the plot
        dir = os.path.dirname(__file__) + '/'
        verfile = open(dir + 'VERSION')

        version = verfile.readline().strip('\n').strip()
        verfile.close()
        pl.figtext(.15, .05, "version " + version, alpha=0.7, size=8)
        
        pl.figtext(.7, .05, "Processed by the GBT pipeline.", 
                   color="red", alpha=0.7, size=8)
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
    pl.savefig(os.path.splitext(infile)[0]+'.png')

    try:
        os.unlink(vdatafile)
    except:
        pass  # just continue on if the file isn't there

    ff.close()

