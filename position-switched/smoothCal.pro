; Smooth the calibration signal to achieve the science goal
; This procedure will be re-defines for different type of experiments
; This version is tuned for broad lines
; HISTORY
; 09JAN22 GIL another attempt at fix small glitch in averaging
; 09JAN20 GIL fix small glitch in averaging
; 09DEC17 GIL initial version based on Katies HI obs
;

pro smoothCal, myDc, calMin, nSavGol, nTrim

  if (not keyword_set(myDc)) then begin
     print,'smoothCal: smooth calibration signal for broad line searches'
     print,'usage: smoothCal, myDc, calMin, nSmooth, nTrim'
     print,'Where   nyDc    input/output smoothed data container containing cal values'
     print,'        calMin  minimum Calibration signal value'
     print,'        nSavGol width of first Savolisky Gol fitler'
     print,'        nTrim   minimum width the replace'
     print,'  ===  Glen Langston, December 17, 2009'
     return
   endif

   if (not keyword_set( calMin)) then calMin = 0.001
   if (not keyword_set( nTrim)) then nTrim = 5
   nChan = n_elements( *myDc.data_ptr)

   if (not keyword_set( nSavGol)) then nSavGol = round(nchan/16)

; median to remove Narrow RFI
; perform minimum test to avoid divide by zero.
for i = nTrim, (nChan-(nTrim+1)) do begin $\
   (*myDc.data_ptr)[i] = median((*myDc.data_ptr)[(i-2):(i+2)]) & $\
   if ((*myDc.data_ptr)[i] lt calMin) then $\
     (*myDc.data_ptr)[i]=calMin & endfor 

;now transfer edge values 
for i = 0, nTrim do begin $\
   (*myDc.data_ptr)[i] = (*myDc.data_ptr)[nTrim] & endfor

for i = (nChan-nTrim), (nChan-1) do begin $\
   (*myDc.data_ptr)[i] = (*myDc.data_ptr)[nChan-(nTrim+1)] & endfor

data_copy, myDc, mySg
data_copy, myDc, myEdge

;use a high order filter to allow using more values
savgolFilter = SAVGOL(nSavGol, nSavGol, 0, 4) 
; savgolFilter = SAVGOL(199, 199, 0, 1) 
*mySg.data_ptr = CONVOL(*myDc.data_ptr, savgolFilter, /EDGE_TRUNCATE)

; The band edge shape is more complex, so must use fewer values
nSavGol2 = round(nSavGol / 4)
savgolFilter2 = SAVGOL(nSavGol2, nSavGol2, 0, 3) 
*myEdge.data_ptr = CONVOL(*myDc.data_ptr, savgolFilter2, /EDGE_TRUNCATE)

; prepare to interplate between the two filtered values
nSav2 = 7*nSavGol2
nSav3 = (9*nSavGol2) - 1
range = 1.0/(nSav3 - nSav2)
a = 1.0D & b = 1.0D

data_copy, myEdge, myDc

;in middle range, interpolate between filtered values
for i = nSav2, nSav3 do begin $\
   a = range*(i-nSav2) & b = range*(nSav3-i) & $\
   (*myDc.data_ptr)[i] = ((*mySg.data_ptr)[i]*a) + $\
                         ((*myEdge.data_ptr)[i]*b) & endfor

;data_copy, myEdge, myDc
print,'Edge Smooth: '+strtrim(string(nSav2),2)+'-'+$\
      strtrim(string(nSav3),2)+' '+strtrim(string(nSavGol),2)+'/'+ $\
      strtrim(string(nChan),2)


;not interoplate other end
;when i = nChan-nSav2, then we want the middle filter
n2 = nChan - (nSav3)
;now transfer the middle values
(*myDc.data_ptr)[nSav3:n2] = (*mySg.data_ptr)[nSav3:n2] 

;now transfer the interpolated values
n3 = nChan - (nSav2+1)
range = 1.0/double(n3 - n2)
for i = n2, n3 do begin $\
   a = range * double(n3-i) & b = range*double(i-n2) & $\
   (*myDc.data_ptr)[i] = ((*mySg.data_ptr)[i]*a) + $\
                         ((*myEdge.data_ptr)[i]*b) & endfor


; finally smooth the joints
(*myDc.data_ptr) = smooth( (*myDc.data_ptr), 3)
; free up the data containers
data_free, myEdge
data_free, mySg
return
end
