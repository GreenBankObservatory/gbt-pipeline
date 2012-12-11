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
                pl.figure(fignum)

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
                
                titlestring = ('{tn} {bw:.2f} MHz {pn} ' + \
                '{fs:.3f} GHz\n{cn1}:{cv1:.1f} {cn2}:{cv2:.1f} AZ: {az:.1f} '+\
                'EL: {el:.1f} Tsys {tsys:.2f}').format(tn=target_name,
                    bw=bandwidth, pn=procname, fs=fsky, cn1=coord1name,
                    cv1=coord1val, cn2=coord2name, cv2=coord2val,
                    az=azimuth, el=elevation, tsys=tsys)
                pl.title(titlestring)

                pl.plot(ff[ext]['DATA'][row])
                fignum += 1
                pl.savefig(sys.argv[1]+'_'+str(fignum)+'.svg')
ff.close()
