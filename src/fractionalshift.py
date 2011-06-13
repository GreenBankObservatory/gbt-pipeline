import pylab
import numpy as np
import sys
import pdb
import time

def doshift(spectra,delta_f):
    
    N_CHANNELS_start = spectra.shape[-1]
    N_CHANNELS_doubled = N_CHANNELS_start*2

    # double the size of the array
    spectra = np.append(spectra, np.zeros(shape=spectra.shape),axis=1)

    # shift the spectra to the center, with zeros padding either end
    ROLLDISTANCE = N_CHANNELS_start/2
    spectra = np.roll(np.array(spectra),ROLLDISTANCE)

    # pad out spectrum on both sides with end values
    for idx,row in enumerate(spectra):
        spectra[idx][:ROLLDISTANCE] = spectra[idx][ROLLDISTANCE]
        spectra[idx][-ROLLDISTANCE:] = spectra[idx][-ROLLDISTANCE-1]

    # inverse fft of spetrum, 0
    ifft = np.fft.ifft(spectra)
    real = ifft.real
    imag = ifft.imag

    # eqn. 9
    delta_p = 2.0 * np.pi * delta_f / N_CHANNELS_doubled
    
    # eqn. 7
    amplitude = np.sqrt(real**2 + imag**2)
   
    # eqn. 8
    phase = np.arctan2(imag,real)
    
    # eqn. 10
    kk = [np.mod(ii,N_CHANNELS_doubled/2) for ii in range(N_CHANNELS_doubled)]
    kk = np.array(kk,dtype=float)
    
    ## eqn. 11
    amplitude = amplitude * (1 - (kk/N_CHANNELS_doubled)**2)
    
    ## eqn. 12
    phase = phase + delta_p * kk
    
    # eqn. 13
    real = amplitude * np.cos(phase)
    
    # eqn. 14
    imag = amplitude * np.sin(phase)
   
    # finally fft to get back to spectra
    shifted = np.fft.fft(real+imag*1j)

    shifted = np.roll(shifted,-ROLLDISTANCE)
    shifted = shifted[:,:N_CHANNELS_start]
    
    return abs(shifted)
    
if __name__ == "__main__":

    # ----------------------------------------------- create some spectra
    SIZEOFSPEC = 1024*4
    NUM_OF_SPECS = 10
    # create a 1d array of noise; a "spectrum"
    spectrum = np.random.random(SIZEOFSPEC)
    
    # put a 1 channel line in the noise
    spectrum[len(spectrum)/2] = 10
    
    spectra = np.array([spectrum]*NUM_OF_SPECS)
   
    # ----------------------------------------------- do the shift
    
    # shift the spectrum
    delta = .6
    
    # --------------------------- one at a time
    t = time.time()
    for spectrum in spectra:
        sspec = doshift(np.reshape(spectrum,(1,spectrum.shape[0])),delta)
    print time.time() - t,'seconds'

    # --------------------------- as a group all at once
    t = time.time()
    vsspec = doshift(spectra,delta)
    print time.time() - t,'seconds'
    
    # --------------------------- compare the last shift of each
    print sspec - vsspec[-1]

    # plot the results
    pylab.subplot(311)
    pylab.plot(spectrum,'r-')
    pylab.subplot(312)
    pylab.plot(vsspec[-1],'g-')
    pylab.subplot(313)
    pylab.plot(spectrum-vsspec[-1],'b-')
    pylab.show()
