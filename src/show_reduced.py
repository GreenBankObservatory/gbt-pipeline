import numpy as np
import spectral_pipeline as sp
import fitsio
import sys
import pylab as pl

ff = fitsio.FITS(sys.argv[1])

fignum = 0
for ext in range(len(ff)):
    if 'nrows' in ff[ext].info:
        for row in range(ff[ext].info['nrows']):
            if not np.all(np.isnan(ff[ext]['DATA'][row])):
                
                target_name = ff[ext]['OBJECT'][:][row].strip()
                bandwidth = ff[ext]['BANDWID'][:][row]/1e6
                procname = ff[ext]['OBSMODE'][:][row].strip().split(':')[0]
                coord1name = ff[ext]['CTYPE2'][:][row].strip()
                coord1val = ff[ext]['CRVAL2'][:][row]
                coord2name = ff[ext]['CTYPE3'][:][row].strip()
                coord2val = ff[ext]['CRVAL3'][:][row]
                fsky = ff[ext]['CRVAL1'][:][row]/1e9
                azimuth = ff[ext]['AZIMUTH'][:][row]
                elevation = ff[ext]['ELEVATIO'][:][row]
                lst = ff[ext]['LST'][:][row]/1e9
                tsys = ff[ext]['TSYS'][:][row]
                date = ff[ext]['DATE-OBS'][:][row]
                
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
               
                data = ff[ext]['DATA'][row]
                columns = ff[ext].colnames
                freq = sp.freq_axis(ff[ext][columns][row][0])
                restfreq = ff[ext]['RESTFREQ'][:][row]
                veldef = ff[ext]['VELDEF'][:][row]
                velo = np.array([sp.freqtovel(fidx,restfreq) for fidx in freq])
                
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
