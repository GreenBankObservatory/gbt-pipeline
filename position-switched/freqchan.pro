;+
; Return channel corresponding to an input frequency (no velocity correction)
;
; <p>Initial version contributed by Glen Langston, glangsto\@nrao.edu
;
; @keyword doPrint {in}{optional}{type=boolean}{default=0} optionally print
; the line frequencies.  The printed frequencies are the line
; frequencies in the frame being displayed on the plotter.
;
; @uses <a href="../../devel/guide/moleculeread.html">moleculeread</a>
; @uses <a href="freq.html">freq</a>
; @uses <a href="../toolbox/veltovel.html">veltovel</a>
; @uses <a href="../toolbox/shiftvel.html">shiftvel</a>
; @uses <a href="../toolbox/shiftfreq.html">shiftfreq</a>
; @uses <a href="../toolbox/decode_veldef.html">decode_veldef</a>
; @uses <a href="../plotter/show.html">show</a>
; @uses <a href="../plotter/vline.html">vline</a>
; @uses <a href="../plotter/getstate.html#_getxrange">getxrange</a>
; @uses <a href="../plotter/getstate.html#_getyrange">getyrange</a>
; @uses <a href="../plotter/getstate.html#_getxvoffset">getxvoffset</a>
; @uses <a href="../plotter/getstate.html#_getxunits">getxunits</a>
; @uses <a href="../plotter/getstate.html#_getxoffset">getxoffset</a>
; @uses <a href="../plotter/getstate.html#_getplotterdc">getplotterdc</a>
; @uses textoidl
; 
; @version $Id: moleculefind.pro,v 1.8 2007/05/01 19:57:12 bgarwood Exp $
;-
pro freqchan, inDc, inFreqHz, outChan

    compile_opt idl2
    on_error,2

    if (not keyword_set( inDc)) then begin
      print,'freqchan: converts an input frequency to a channel number'
      print,'Usage: freqchan, inDc, inFreqHz, outChan'
      print,'Where'
      print,'input  inDc       Data container describing the observation'
      print,'input  inFreqHz   Frequency to be converted to channel'
      print,'output outChan    Output channel; range 0 to n-1'
      print,'----- Glen Langston, 2010 January 22; glangsto@nrao.edu'
      return
    endif

    nChan   = double(n_elements( *inDc.data_ptr))
    ; if no input frequency, just return central channel
    if (not keyword_set(inFreqHz)) then begin
      outChan = nChan/2
      return
    endif

    delChan = double(inDc.frequency_interval)
    refChan = double(inDc.reference_channel)
    dFreq = inFreqHz - inDc.center_frequency
    dChan = dFreq/delChan
    outChan = dChan + refChan 
    if (outChan lt 0.) then outChan = 0
    if (outChan ge nChan) then outChan = nChan - 1
    return
end ; end of freqchan
