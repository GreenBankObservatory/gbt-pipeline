import pyfits
import numpy as np
import pylab
from matplotlib.font_manager import FontProperties
from mpl_toolkits.axes_grid.anchored_artists import AnchoredText
import scipy
from scipy import constants
from scipy import signal

import sys
from collections import OrderedDict
import os
import argparse

ONEPLOT = False
DEBUG = False

from pylab import *

POL ={ -1:'RR', -2:'LL',
       -3:'RL', -4:'LR',
       -5:'XX', -6:'YY', -7:'XY', -8:'YX',
        1:'I',   2:'Q',   3:'U',   4:'V' }
    
def polnum2char(num):
    return POL[num]

def flag_rfi(spectrum, niter, nsigma, medfilt_size):
    """
    flag channels with narrow band RFI
    
    nsigma  # number of standard deviations
    niter   # number of iterations
    medfilt_size # median filter window
    
    """
    
    sig = np.ma.array(spectrum)
    sig_smoothed = signal.medfilt(sig, medfilt_size)

    while niter>0:

        sd = (sig-sig_smoothed).std()
        spikes = abs(sig-sig_smoothed)
        mask = (spikes > (nsigma*sd)).data 
        sig.mask = np.logical_or( sig.mask, mask)
        niter-=1
    
    return sig.mask

def freq_axis(data, verbose=0):
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
    
    for chan, ee in enumerate(data['DATA']):
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
def freqtovel(freq, restfreq, veldef="RADIO"):

    LIGHT_SPEED = constants.c/1e3 # km/s
    freq = float(freq)
    restfreq = float(restfreq)
    
    if veldef == 'RADIO':
        result = LIGHT_SPEED * ((restfreq - freq) / restfreq)
    elif veldef == 'OPTICAL':
        result = LIGHT_SPEED * (restfreq / (freq - restfreq))
    elif veldef == 'TRUE':
        gg = (freq / restfreq)**2
        result = LIGHT_SPEED * ((restfreq - gg) / (restfreq + gg))
    else:
        print 'unrecognized velocity definition'

    return result

def fit_baseline(ydata, order):
    
    oldmask = ydata.mask.copy()
    
    datalen = len(ydata)
    xdata = np.linspace(0, datalen, datalen)
    
    ydata.mask[:.1*datalen]=True
    ydata.mask[.9*datalen:]=True
    ydata.mask[.4*datalen:.6*datalen]=True
        
    xdata = np.ma.array(xdata)
    xdata.mask = ydata.mask
    
    polycoeffs = np.ma.polyfit(xdata, ydata, 3)
    yfit = scipy.polyval(polycoeffs, xdata)
    yfit = np.ma.array(yfit)
    
    # reset the mask on ydata
    ydata.mask = oldmask
    
    return yfit

def rebin_1d(data, binsize):
    rebinned = (data.reshape(len(data)/binsize, binsize)).mean(1)
    return rebinned

def smooth_hanning(data, window_len):
    kernel = signal.hanning(window_len)/2.
    if data.ndim == 2:
        smoothed_data = np.convolve(kernel, data[0], mode='same')
        for spectrum in data[1:]:
            smoothed = np.convolve(kernel, spectrum, mode='same')
            smoothed_data = np.vstack((smoothed_data, spectrum))
    elif data.ndim == 1:
        smoothed_data = np.convolve(kernel, data, mode='same')
    else:
        print 'number of dimensions', data.ndim, 'not supported by hanning'
    return smoothed_data
    
def median(data, window_len):
    return signal.medfilt(data, window_len)

def boxcar(data, window_len):
    kernel = signal.boxcar(window_len)/float(window_len)
    smoothed_data = np.convolve(kernel, data, mode='same')
    return smoothed_data

def mask_data(data, args):
    """
    Return the masked data
    
    """
    return data[ mask(data, args) ]

def mask(data, args):
    """
    Return the mask based on the arguments
    
    """
    # initialize a mask list the size of args
    each_mask = {}
    fullmask = None

    for key in args.iterkeys():
       
        thismask = ( data[key] == args[key] )
        
        if fullmask != None:
            fullmask = np.logical_and( fullmask, thismask )
        else:
            fullmask = thismask

    return fullmask


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run the spectral pipeline')
    parser.add_argument('FILENAME', help='input file name')
    parser.add_argument('--rfi-iterations', dest="niter", metavar='N',
                        default=10,
                        help='number of iterations for narrow-band RFI '
                             'smoothing')
    parser.add_argument('--rfi-spike-threshold', dest='nsigma', default=3,
                        help='number of sigma threshold for narrow RFI spikes')
    parser.add_argument('--median-filter-size', dest='medfilt_size', default=15,
                       help='median filter window size for narrow-band rfi '
                            'flagging')
    parser.add_argument('--hanning-window-size', dest='hanning_win', default=5,
                       help='hanning window size for smoothing ')
    parser.add_argument('--aperture-efficiency', dest='eta_a', default=.71,
                        help='aperture efficiency')
    parser.add_argument('--etal-correction', dest='eta_l', default=.99,
                        help='correction factor for rear spillover, ohmic '
                             'loss and blockage efficiency')
    parser.add_argument('--atmospheric-opacity', dest='tau', default=.008,
                        help='atmospheric opacity')
    #parser.add_argument('--baseline-region', dest='baseline_reg',
    #                    help='baseline region')
    
    args = parser.parse_args()

    raw = pyfits.open(args.FILENAME)

    targets = {}
    for target_name in set(raw[1].data['OBJECT']):
        targets[target_name] = mask_data(raw[1].data, {'OBJECT':target_name })

    num = 1
    
    targets = OrderedDict(sorted(targets.items(), key=lambda t: t[0]))

    primary = pyfits.PrimaryHDU()
    primary.header = raw[0].header

    outcols = raw[1].columns
    for xx in outcols:
        if xx.name == 'DATA':
            xx.format = '1024E'

    sdfits = pyfits.new_table(pyfits.ColDefs(outcols), 
                              nrows=len(targets), fill=1)


    # for each target
    for target_id in targets.keys():

        print 'target', target_id, len(targets[target_id]), 'integrations'
                
        target_data = targets[target_id]

        obsmodes = {}
        
        # for each scan on the target, collect obsmodes
        for scan in set(target_data['SCAN']):
            obsmodes[str(scan)] = \
                target_data['OBSMODE'][target_data['SCAN']==scan][0]

        obsmodes = OrderedDict(sorted(obsmodes.items(), key=lambda t: t[0]))
     
        # for each scan on the target, make pairs
        scan_pairs = []
        for scan in obsmodes.keys():
            #!!!!!!!!!!!!!!!!!!! look for onoff in obsmode
            
            scanmask = mask(target_data, { 'SCAN':int(scan) } )
            # check procsize and procseqn
            if (target_data['PROCSIZE'][scanmask][0]) == 2 and \
               (target_data['PROCSEQN'][scanmask][0]) == 1:
            
               
                   scan_pairs.append( (int(scan), int(scan)+1) )
            
        print 'scans for target', target_id, scan_pairs

        final_spectrum = None
        for pair in scan_pairs:
            
            if 'OnOff' in obsmodes[str(pair[0])]:
                TargScanNum = pair[0]
                RefScanNum = pair[1]
            elif 'OffOn' in obsmodes[str(pair[0])]:
                TargScanNum = pair[1]
                RefScanNum = pair[0]
            else:
                print 'Error: Unknown OBSMODE'
                continue
        
            # L(ON) - L(OFF) / L(OFF)
            TargDataPols = mask_data(raw[1].data, {'SCAN':TargScanNum})
            RefDataPols = mask_data(raw[1].data, {'SCAN':RefScanNum})
            
            polarizations = set(TargDataPols['CRVAL4'])

            for pol in polarizations:
                print 'polarization', polnum2char(pol)

                # pyfits data object for Target and Reference scans
                TargData = mask_data(TargDataPols, {'CRVAL4':pol})
                RefData = mask_data(RefDataPols, {'CRVAL4':pol})
                
                # pyfits data object for 
                # cal_on and cal_off sets os integrations for Target
                TargOn = mask_data(TargData, { 'CAL':'T' })
                TargOff = mask_data(TargData, { 'CAL':'F' })
                # spectrum for each integration averaged cal_on and cal_off
                # for Target
                TargOnData = smooth_hanning(TargOn['DATA'], args.hanning_win)
                TargOffData = smooth_hanning(TargOff['DATA'], args.hanning_win)
                Targ = (TargOnData+TargOffData)/2.

                # pyfits data object for 
                # cal_on and cal_off sets os integrations for Reference
                RefOn = mask_data(RefData, { 'CAL':'T' })
                RefOff = mask_data(RefData, { 'CAL':'F' })
                # spectrum for each integration averaged cal_on and cal_off
                # for Reference
                RefOnData = smooth_hanning(RefOn['DATA'], args.hanning_win)
                RefOffData = smooth_hanning(RefOff['DATA'], args.hanning_win)
                Ref = (RefOnData+RefOffData)/2.
                
                # flag channels with narrow band RFI
                # This produces a single RFI mask, to be applied later
                targ_rfi_mask = flag_rfi(Targ.mean(0), args.niter, args.nsigma,
                                         args.medfilt_size)
                ref_rfi_mask = flag_rfi(Ref.mean(0), args.niter, args.nsigma,
                                        args.medfilt_size)
                rfi_mask = np.logical_or(targ_rfi_mask, ref_rfi_mask)
                
                Tcal = RefData['TCAL'].mean()
                AveRefOff = RefOffData.mean(0)
                AveRefOn = RefOnData.mean(0)
                mid80off = AveRefOff[.1*len(AveRefOff):.9*len(AveRefOff)]
                mid80on = AveRefOn[.1*len(AveRefOn):.9*len(AveRefOn)]
                
                Tsys = Tcal * ( mid80off / (mid80on-mid80off) ) + Tcal / 2.
                Tsys = Tsys.mean()
                
                # if Targ and Ref have different numbers of integrations,
                #   use the lesser number of the two so that each has a
                #   match and ignore the others
                maxIntegrations = np.min( (len(Targ), len(Ref)) )
                Targ = Targ[:maxIntegrations]
                Ref = Ref[:maxIntegrations]
                
                Ta = Tsys * ( (Targ - Ref) / Ref )
                
                elevation = TargData['ELEVATIO'].mean()
                eta_a = args.eta_a
                eta_l = args.eta_l
                tau = args.tau
                Jy = Ta/2.85 * (np.e**(tau/np.sin(elevation)))/(eta_a*eta_l)
                
                cal = Jy
                
                cal = np.ma.array(cal)

                freq = freq_axis(TargOn[0])
                restfreq = TargOn['RESTFREQ'][0]
                velo = np.array([freqtovel(ff, restfreq) for ff in freq])

                # turn cal into a masked array
                specvelmask = np.logical_and( velo>-300, velo<300 )

                velocity_mask = np.array([specvelmask] * len(cal))
                rfimask = np.array([rfi_mask] * len(cal))
                total_mask = np.logical_or(rfimask, velocity_mask)

                cal_masked = np.ma.masked_array(cal, mask= total_mask)
                
                print 'processing scans', pair
                
                # check baselines of each integration
                for idx, spec in enumerate(cal_masked):
                    fullfft = np.abs(np.fft.fft(spec[.05*len(spec):]))
                    
                    # top 10% of fft
                    myfft = fullfft[-(.1*len(fullfft)):]
                
                    # check if all fft vals are within X sigma
                    print 'checking integration:', idx

                    if myfft.max()>20*Tsys:
                        print 'FLAGGING INTEGRATION', idx
                        cal_masked[idx].mask = True
                        
                    if DEBUG:
                        print 'fft.max()', myfft.max()

                #!!!!!!!!!!!!!!!!!!!!!!!  don't assume binsize!!
                binsize = len(cal_masked.mean(0)) / 1024.
                rebinned = rebin_1d(cal_masked.mean(0), binsize=binsize)
                # reshape the velocity axis as well
                vel = rebin_1d(velo, binsize=binsize)
                rebinned.mask = flag_rfi(rebinned, args.niter, args.nsigma,
                                         args.medfilt_size)
                
                #!!!!!!!!!!!!!!!!!!!!!!!  don't assume order
                yfit = fit_baseline(rebinned, order=3)
                yfit.mask = rebinned.mask

                baseline_removed = rebinned-yfit

                if final_spectrum != None:
                    final_spectrum =\
                        np.ma.vstack((final_spectrum, baseline_removed))
                else:
                    final_spectrum = baseline_removed
                
        if final_spectrum != None and final_spectrum.ndim > 1:
            final_spectrum = final_spectrum.mean(0)

        final_spectrum = final_spectrum.filled(fill_value=float('nan'))
        
        final_spectrum[:.05*len(final_spectrum)] = float('nan')
        final_spectrum[-.05*len(final_spectrum):] = float('nan')
        
        freereg=final_spectrum[:.35*len(final_spectrum)]
        freereg = np.ma.masked_array(freereg, np.isnan(freereg))
        rms = np.ma.sqrt((freereg**2).mean())
        
        # -------------------------------- one figure for all spectra
        if ONEPLOT:
            ax = pylab.subplot(len(targets), 1, num)
            at = AnchoredText(target_id, loc=2, frameon=False)
            ax.add_artist(at)
            ax.plot(vel, final_spectrum, label=target_id)
        
        # --------------------------------- one figure per spectrum
        else:
            figure(figsize=(15, 5))
            ax = pylab.subplot(1, 1, 1)
            at = AnchoredText(target_id, loc=2, frameon=False,
                              prop=dict(size=22))
            ax.add_artist(at)
            title(args.FILENAME+ '\n' + target_id)
            xlabel('velocity (km/s)')
            ylabel('Jy')
            tick_params(labelsize=22)
            fs=final_spectrum[.2*len(final_spectrum):.8*len(final_spectrum)] 
            vs=vel[.2*len(vel):.8*len(vel)] 
            plot(vs, fs, label=target_id)

            savefig(target_id+'.png')
        
        for name in raw[1].columns.names:
            if name != 'DATA':
                sdfits.data[num-1][name] = TargData[0][name]
        sdfits.data[num-1]['DATA'] = final_spectrum            
        
        num += 1
    
    # -------------------------------------- one figure for all spectra
    if ONEPLOT:
        pylab.suptitle(args.FILENAME)
        pylab.figtext(.5, .02, 'velocity (km/s)')
        pylab.figtext(.02, .5, 'Jy', rotation='vertical')
        pylab.savefig(os.path.basename(args.FILENAME)+'.svg')
 
    hdulist = pyfits.HDUList([primary, sdfits])
    hdulist.writeto(os.path.basename(args.FILENAME)+'.reduced.fits',
                                     clobber=True)
    hdulist.close()
    del hdulist

    raw.close()
