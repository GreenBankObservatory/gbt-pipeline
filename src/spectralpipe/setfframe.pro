;+
; Procedure to reset the frequency reference frame of the indicated
; buffer (defaults to the primary data container, buffer 0)
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
; @param buffer {in}{required}{type=spectrum} The data container to be
; adjusted.  Defaults to the primary data container (0).
;
; @keyword toframe {in}{optional}{type=string}  The reference frame to
; use.  If not supplied, the value implied by the last 4 characters of
; the velocity_definition the data container.   See <a href="frame_velocity.html">frame_velocity</a> for a 
; full list of supported reference frames.
;
; @uses <a href="../toolbox/dcsetfframe.html">dcsetfframe</a>
;
; @version $Id$
;-

pro setfframe, buffer, toframe=toframe
  compile_opt idl2

  if n_elements(buffer) eq 0 then buffer=0

  if (buffer lt 0 or buffer ge n_elements(!g.s)) then begin
     message,string(n_elements(!g.s),format='("buffer must be >= 0 and < ",i2)'),/info
     return
  endif

  ; can't pass in array element, but a simple copy works here
  ; since aren't adjusting the data array
  tmp = !g.s[buffer]
  dcsetfframe,tmp,toframe=toframe
  !g.s[buffer] = tmp

end
