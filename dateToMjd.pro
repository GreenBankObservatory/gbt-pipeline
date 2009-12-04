;IDL procedure to convert at FITS date string to MJD
;HISTORY 
; 09FEB19 GIL select out date parameters to compute MJD
;Omissions
;This script does very limited (no) error checking.
;Any format change will break it.
function dateToMjd, dateString

  ; dateToMjd: Convert a FITS date string to MJD'
  ; dateToMjd: Usage'
  ; dateToMjd, dateStr, mjd'
  ; where dateStr string containing the data'
  ;               ie. 2009-02-10T21:09:00.08'
  ; Returns   mjd  floating point Modified Julian Date'
  ;
  ; Glen Langston, 2009 February 19'
  ; Modified by RJM, May 2009

    if (n_params() lt 1) then begin
        message, 'Usage: dateToMjd(dateStr) where dateStr string is of the form 2009-02-10T21:09:00.08'
    endif

    year  = strmid(dateString,0,4)
    month = strmid(dateString,5,2)
    day   = strmid(dateString,8,2)
    hour  = strmid(dateString,11,2)
    minute= strmid(dateString,14,2)
    second= strmid(dateString,17)

    ;now convert from julian day to mjd
    return, julday(month, day, year, hour, minute, second) - 2400000.5d0
end

