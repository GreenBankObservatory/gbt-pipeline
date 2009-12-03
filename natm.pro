; natm.pro estimates the number of atmospheres along the line of site
; at an input elevation
; This comes from a model reported by Ron Maddale
; HISTORY
; 08DEC18 GIL initial version
;
;1) A = 1/sin(elev) is a good approximation down to about 15 deg but
;starts to get pretty poor below that.  Here's a quick-to-calculate,
;better approximation that I determined from multiple years worth of
;weather data and which is good down to elev = 1 deg:
;
;     if (elev LT 39) then begin
;        A = -0.023437  + 1.0140 / sin( (!pi/180.)*(elev + 5.1774 / (elev
;+ 3.3543) ) )
;     else begin
;        A = sin(!pi*elev/180.)
;     endif 
;


pro natm, elDeg, nAtmos

  on_error,2
  if (not keyword_set(elDeg)) then begin
    print,'nAtm: compute number of atmospheres at elevation (deg)'
    print,'usage: nAtm, elDeg, nAtmos'
    print,'where: elDeg  - input elevation in degrees'
    print,'where: nAtmos - output number of atmospheres'
    print,'natm model is provided by Ron Maddalena'
    print,'Procedure written by Glen Langston, 2008 December 18'
    return
  endif 

  DEGREE = !pi/180.

  if (elDeg LT 39.) then begin
    A =-0.023437 + ( 1.0140 / sin( DEGREE*(elDeg + 5.1774 / (elDeg + 3.3543))))
  endif else begin 
    A =1./sin(DEGREE*elDeg)
  endelse
;
  if (not keyword_set(nAtmos)) then $\
    print,'Model Number of Atmospheres: ', A, ' at elevation ',elDeg

  nAtmos = A
return
end


