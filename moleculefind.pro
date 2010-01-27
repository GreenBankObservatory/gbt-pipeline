;+
; Return molecules within frequency range
; molecular lines stored in !g.molecule on the currently displayed
; plot at the appropriate location given the current x-axis.
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
pro moleculefind, beginFreqGHz, endFreqGHz, nMolecule, nuRestGHzs, moleculeLabels,doPrint=doPrint
    compile_opt idl2
    on_error,2

    if (not keyword_set(beginFreqGHz)) then begin 
      beginFreqGHz = 0.D0
      doPrint = 1
    endif
    if (not keyword_set(endFreqGHz)) then endFreqGHz = 115.D0
    if (not keyword_set(nMolecule)) then nMolecule = 0
    if (not keyword_set(nuRestGHzs)) then nuRestGHzs = [0.D0] 
    if (not keyword_set(moleculeLabels)) then moleculeLabels = ['None']
    if n_elements(doPrint) eq 0 then doPrint = 0

    moleculeRead          ; read in molecule frequencies
                          ; will not duplicate any effort if already read

    if (beginFreqGHz gt endFreqGHz) then begin
      temp = beginFreqGHz & beginFreqGHz = endFreqGHz & endFreqGHz = temp
    endif

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
end ; end of moleculefind
