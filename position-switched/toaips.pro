;IDL Procedure to calibrate map scans
;HISTORY
; 10JAN22 GIL narrow the median baseline in idlToSdfits
; 10JAN21 GIL process Ku band dual beam scans for RaLong Map scan
; 10JAN19 GIL process Ku band dual beam scans for a map
; 09DEC16 GIL break up sdfits call for clarity
; 09DEC15 GIL revised for tmc map
; 09DEC02 GIL revised for a 2x2 degree map
; 09NOV30 GIL initial version


pro toaips, myDc, vSource, vSourceWidth, vSourceBegin, vSourceEnd, userParms

  if (not keyword_set(myDc)) then begin
    print, 'toaips: convert a keep file to an AIPS format input file'
    print, 'Selected channels are selected by arguments to program idlToSdfits'
    print, 'usage:'
    print, 'toaips, myDc, vSource, vSourceWidth, vSourceBegin, vSourceEnd, userParms'
    print, 'where'
    print, 'input myDc    Data container describing the calibrated observation'
    print, ' vSource      Velocity of the source (km/sec)'
    print, ' vSourceWidth Velocity of the source (km/sec)'
    print, ' vSourceBegin Beginning of Velocity to select for output (km/sec)'
    print, ' vSourceEnd   Endding of Velocity to select for output (km/sec)'
    print, ' userParms    additional observer specified arguments to idlToSdfits'
    print, 'Output is to an AIPS format (.sdf) output file, plus graphs'
    print, '----- Glen Langston, 2010 January 22; glangsto@nrao.edu'
    return
  endif

  if (not keyword_set(userParms)) then userParms = ' '
  if (not keyword_set(vSource))   then vSource = 0.0
  if (not keyword_set(vSourceWidth)) then vSourceWidth = 1.0
  if (not keyword_set(vSourceBegin)) then vSourceBegin = -10.0
  if (not keyword_set(vSourceEnd)) then vSourceEnd = 10.0

  cLight = 299792.458D0; km/sec

  ;prepare to find molecular lines 
  nMolecule = 1
  nuRestGHzs = [ 0.D0, 0.D0, 0.D0, 0.D0, 0.D0, 0.D0]
  moleculeLabels = [ '  ', '   ', '   ', '  ', '   ', '   ']
  ;find the line in this frequency range 
  moleculeinrange, myDc, nMolecule, nuRestGHzs, moleculeLabels, doPrint=1
  restFreqHz = nuRestGHzs[0]*1.D9
  dopplerFactor = (1.D0 - (vSource/cLight))
  channelKmSec = cLight*abs(myDc.frequency_interval/dopplerFactor)/restFreqHz
  width = round((vSourceWidth/channelKmSec)*8.D0)

  vFrame = 1.D-3 * myDc.frame_velocity
  vBegin = vSourceBegin + vFrame
  vEnd   = vSourceEnd + vFrame
  vLine  = vSource + vFrame
; now compute range of channels to select for mapping
  beginFreqHz = restFreqHz * (1.D0 - (vBegin/cLight))
  endFreqHz   = restFreqHz * (1.D0 - (vEnd/cLight))
  sourceFreqHz= restFreqHz * (1.D0 - (vLine/cLight))

  beginChan = 1 & endChan = 1
;get channels to select 
  freqchan, myDc, beginFreqHz, beginChan
  freqchan, myDc, endFreqHz, endChan
  freqchan, myDc, sourceFreqHz, sourceChan

; the channels kept must be at least twice the filter width
  if ((endChan - beginChan) lt 2*width) then begin $\
    beginChan = sourceChan - round(width) & $\
    endChan   = sourceChan + round(width) & endif

; keep channels in range of the spectra
  if (beginChan lt 0) then beginChan = 0
  nChan = n_elements( *myDc.data_ptr)
  if (endChan ge (nChan-1)) then endChan = nChan-1

; median filter baseline half width channels
  widthParameter = '-w ' + strtrim(string(width), 2) + ' '
; select channels for output
  channelParameter = '-c ' + strtrim(string(round(beginChan)),2) + ':' + $\
                  strtrim(string(round(endChan)), 2) + ' '

; use current keep file name to form output name used by idlToSdfits
; expect name of form Cal_<source>_<feed-scan_range-etc>.fits
; Strip off Cal_ and trailing .fits
  if strmatch(!g.line_fileout_name,'Cal_*.fits') then begin
     ; this appears to be what we'd expect
     
     outFile = strtrim(strmid(!g.line_fileout_name,4,strlen(!g.line_fileout_name)-9),2) + '.sdf'
     outFileParameter = '-o ' + outFile + ' '
  endif else begin
     ; perhaps a warning should happen here?
     ; just rely on the idlToSdfits default name
     outFileParameter =''
  endelse

  parameters = channelParameter + widthParameter + outFileParameter + ' ' + userParms + ' '

;define path for program to convert to AIPS format
  idlToSdfitsPath = '/users/glangsto/linux/idlToSdfits/idlToSdfits '
;convert the file to aips input file format
  idlToSdfitsCmd = idlToSdfitsPath + parameters + ' ' + !g.line_fileout_name
  print, idlToSdfitsCmd
;convert calibrated data for input to AIPS
  spawn, idlToSdfitsCmd

return
end ; end of toaips.pro

