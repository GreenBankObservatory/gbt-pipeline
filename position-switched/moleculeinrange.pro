;+
; Return molecules within frequency range of an input dc
;
; <p>Initial version contributed by Glen Langston, glangsto\@nrao.edu
;
; @keyword doPrint {in}{optional}{type=boolean}{default=0} optionally print
; the line frequencies.  The printed frequencies are the line
; frequencies in the frame being displayed on the plotter.
;
; @version $Id$
;-
pro moleculeinrange, inDc, nMolecule, nuRestGHzs, moleculeLabels, doPrint=doPrint

    compile_opt idl2
    on_error,2

    if (not keyword_set( inDc)) then begin
      print,'moleculeinrange: list molecules with the frequency range of an observation described by a data container'
      print,'Usage: moleculeinrange, inDc, nMolecule, nuRestGHzs, moleculeLabels, doPrint'
      print,'Where'
      print,'input  inDc       Data container describing the observation'
      print,'output nMolecule  Number of molecules in the frequency range'
      print,'       nuRestGHzs Array of frequencies of molecules in range'
      print,'       moleculeLabes Array of labels of molecules in range'
      print,'Notes: the source velocity is used in determining molecules in range'
      print,'Only the central 90% of the observing band is searched for molecules'
      print,'----- Glen Langston, 2010 January 22; glangsto@nrao.edu'
      return
    endif

    ; will always reset number of molecules to zero, but turn on printing
    if (not keyword_set(nMolecule)) then doPrint = 1
    if (not keyword_set(nuRestGHzs)) then nuRestGHzs = [ 0.D0]
    if (not keyword_set(moleculeLabels)) then moleculeLabels = ['None']
    if n_elements(doPrint) eq 0 then doPrint = 0

    nMolecule = 0

    ; compute doppler factor for rest frame of source
    dopplerFactor = 1.D0 + (inDc.source_velocity / 29979245.8D0)
    delChan = double(inDc.frequency_interval)
    refChan = double(inDc.reference_channel)
    nChan   = double(n_elements( *inDc.data_ptr))
    print, dopplerFactor, delChan, refChan, nChan
    beginFreqGHz = (inDc.observed_frequency + (0.D0 - refChan)*delChan)*1.E-9
    endFreqGHz = (inDc.observed_frequency + (nChan - refChan)*delChan)*1.E-9
    if (beginFreqGHz gt endFreqGHz) then begin
      temp = beginFreqGHz & beginFreqGHz = endFreqGHz & endFreqGHz = temp
    endif
    rangeGHz = endFreqGHz - beginFreqGHz
    centerGHz = (beginFreqGHz + endFreqGHz)/2.D0
    ; now recompute excluding end 5 % 
    beginFreqGHz = (centerGHz - (rangeGHz*.5D0*.95))*dopplerFactor
    endFreqGHz = (centerGHz + (rangeGHz*.5D0*.95))*dopplerFactor    

    print, 'Searching for molecular lines in frequency range ',beginFreqGHz, $\
           ' to ',endFreqGHz,' GHz'
    moleculeread

    ;For all known molecular lines
    for i = 0,(!g.nmol-1) do begin

        ; convert frequency MHz to GHz
        xf = !g.molecules[i].freq * 1.E-3;

        ; if line is in the plotted range
        if ((xf gt beginFreqGHz) and (xf lt endFreqGHz)) then begin
            moleculeLabel  = 'U'
            if (!g.molecules[i].type ne 'U') then begin
              moleculeLabel = strtrim(string( !g.molecules[i].formula))
            endif
            nuRestGHz = xf;
            if (nMolecule eq 0) then begin
              moleculeLabels = [ moleculeLabel] 
              nuRestGHzs = [ nuRestGHz] 
            endif else begin
              moleculeLabels = [moleculeLabels, moleculeLabel] 
              nuRestGHzs = [ nuRestGHzs, nuRestGHz]
            endelse
            nMolecule = nMolecule + 1   ; count lines found
            if (doPrint) then print, !g.molecules[i].formula,' nu = ', xf, ' GHz'
        endif ; end if molecule is between min and max values
    endfor ; end for all molecules in list

    if (nMolecule gt 1) then print,'More than 1 molecule in frequency range'
    return
end ; end of moleculeinrange
