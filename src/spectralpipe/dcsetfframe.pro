;+
; Procedure to reset the frequency reference frame of the supplied data
; container(s) to the indicated frame.
;
; The frequency axis reference frame is given by the frequency_type
; header value.  Normally this remains "TOPO", the topocentric frame
; in which the data were originally taken.  The default GBTIDL display
; routines use the reference frame found in the velocity_definition
; header value.  This procedure can be used to set the frequency axis
; values to that frame (or any other valid reference frame).  This can
; be useful when exporting the data to an environment that
; doesn't know about anything except the frequency information.
;
; This routine will not change the displayed frequency axis.
;
; <p> If the frame is not set, the one implied by the data header
; velocity_definition is used. 
;
; <p> This routine adjusts the following header values:
; reference_frequency, frequency_interval, frequency_type and
; center_frequency.  When written to an SDFITS table, the first three
; of these four values correspond to CRVAL1, CDELT1, and CTYPE1, in that
; order.
;
; <p> Nothing is changed if the frame is already set to the desired
; frame.
;
; <p> Nothing is changed if the frame is unrecognized.
;
; @param dc {in}{required}{type=spectrum} The data container(s) to be adjusted.
;
; @keyword toframe {in}{optional}{type=string}  The reference frame to
; use.  If not supplied, the value implied by the last 4 characters of
; the velocity_definition the data container.   See <a href="frame_velocity.html">frame_velocity</a> for a 
; full list of supported reference frames.
;
; @version $Id$
;-

pro dcsetfframe, dc, toframe=toframe
  compile_opt idl2

  ; sanity checks on dc here
  if n_elements(dc) eq 0 then begin
     message,'No data container(s) given.',/info
  endif


  if size(dc,/type) ne 8 then begin
     message,'dc must be a data container or array of data containers',/info
  endif

  if tag_names(dc,/structure_name) ne 'SPECTRUM_STRUCT' then begin
     message,'dc must be a spectrum data container',/info
  endif

  ; this could be vectorized, but doing it this way allows for less
  ; code duplication since the non-vectorized functions already exist

  for i=0,n_elements(dc)-1 do begin
     if n_elements(toframe) eq 0 then begin
        ; default to frame in velocity definition
        if not decode_veldef(dc[i].velocity_definition, vdef, thisFrame) then return
     endif else begin
        thisFrame = toframe
     endelse
         
     if thisFrame ne dc[i].frequency_type then begin
        ; can convert everything in one shot
        newFreqs = freqtofreq(dc[i], [dc[i].reference_frequency, dc[i].frequency_interval, dc[i].center_frequency], thisFrame, dc[i].frequency_type)
        dc[i].reference_frequency = newFreqs[0]
        dc[i].frequency_interval = newFreqs[1]
        dc[i].center_frequency = newFreqs[2]
        dc[i].frequency_type = thisFrame
     endif
  endfor
end
