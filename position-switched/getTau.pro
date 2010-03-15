function getTau, mjd, freqMHz

    ; getTau: Retrieves archived tau prediction for date and frequency
    ; 
    ;
    ; Usage:    getTau(mjd, freqMHz)
    ; where  mjd       Modified Julian Date(s) of observations (ie 54881 etc)
    ;        freqMHz   Frequency(s) in MHz of observations
    ;
    ; Returns computed opacity value(s) at zenith (range 0 to > 1)
    ;
    ; Uses getForecastValues, written by Ron Maddalena
    ; Function returns string like : Opacity(22.2350,54873.381) = 0.17310
    ; getTau() parses the string and
    ;     returns the zenith opacity at each frequency at each mjd
    ;     i.e. you get all combinations of all supplied MJDs and frequencies
    ;  tauZenith[n_mjd, n_freq]
    ;  Note that if n_mjd == n_freq = 1, a single value will be returned.
    ;    And that if n_freq=1 and n_mjd != 1, a 1D vector will be returned
    ; 
    ; Glen Langston, 2009 February 19
    ; Modified by RJM, April, 2009
    ; Modified by RWG, Dec, 2009

    if (n_params() lt 2) then begin
        message, 'Usage: getTau(MJD, FreqMHz)'
    endif

    n_mjd = n_elements(mjd)
    n_freq = n_elements(freqMHz)
    tauZenith = dblarr(n_mjd, n_freq)

    ; if any date before 2004 May 01 == mjd 53126 or any 
    ; low freq, use liebeTau.pro
    ; could probably split up the work and watch for odd cases where  
    ; some dates are before the cut-off and others are after
    ; ditto for frequencies.  But that should be rare, if it ever occurs.
    if (total(mjd lt 53126) gt 0 or total(freqMHz le 2000.) gt 0) then begin
        ; note that this assumes
        ;   a) that what's currently in !g.s[0] is related to what's
        ;      being asked for here
        ;   b) that the temp, humidity, and pressure are the same for all values
        ;      being asked for here.  Since sdfits gets those values
        ;      from the Antenna FITS file and since those values are
        ;      written at the start of the scan and only once per scan
        ;      this assumption is safe so long as all values requested
        ;      here are going to be used on the scan associated with 
        ;      the data in !g.s[0]
       tempC = !g.s[0].tambient - 273.15
       humidity = !g.s[0].humidity
       dewPtC = tempC
       spawn,'python /home/sandboxes/kfpa_pipeline/humidityToTDew.py ' + humidity +' '+ tempC
       readcol,'dewpointtemp.txt',F='A',dewPtC
       file_delete,'dewpointtemp.txt'
       freqGHz = freqMHz*.001
       pressureMBar = !g.s[0].pressure*0.01
       tauZenith = 1.0
                                ; liebeTau is not quite vectorized yet
                                ; (print statements mostly I think)
       ; result is indep of mjd here - get and use taus for each freq
       for i=0,n_freq-1 do begin
           liebeTau, pressureMBar, tempC, dewPtC, freqGHz, thisTauZenith
;           print, 'LiebeTau: p, T, DT, F, tau:',pressureMBar, tempC, dewPtC, freqGHz, thisTauZenith
           if n_freq eq 1 then begin
               tauZenith[*] = thisTauZenith
           endif else begin
               tauZenith[*,i] = thisTauZenith
           endelse
       endfor
       return, tauZenith
    endif 

    ; compose the getForecastValues command line
    sMjdVec = strtrim(string(mjd,format='(f13.7)'),2)
    sMjd = strjoin(sMjdVec,' ')
    sFreqVec = strtrim(string(freqMHz/1000.,format='(f12.6)'),2)
    sFreq = strjoin(sFreqVec,' ')
    spawn, '/users/rmaddale/bin/getForecastValues -timeList ' + sMjd + ' -freqList ' + sFreq, result;       print, 'LiebeTau: p, T, DT, F, tau:',pressureMBar, tempC, dewPtC, freqGHz, tauZenith

    n = strpos(result,'=')
    ; n is potentially a vector, and all should be > 0
    if total(n gt 0) ne n_elements(n) then begin
	message, 'Error: Cannot read results from getForecastValues'
    endif
    ; need to parse each one and asign it accordingly
    for i = 0, n_elements(result)-1 do begin
        thisResult = result[i]
        thisTau = float(strmid(thisResult,n[i]+1))
        if (thisTau lt 0) then begin
            message, 'Error: getForecastValues cannot determine opacity.  Date must be > May 1, 2004, frequency > 2000 and < 1160000 MHz'
        endif
        leftParen = strpos(thisResult,'(')
        rightParen = strpos(thisResult,')')
        ; we want to do string comparisons
        values = strsplit(strmid(thisResult,leftParen+1,(rightParen-leftParen-1)),',',/extract)
        thisFreq = strtrim(values[0],2)
        thisMjd = strtrim(values[1],2)
        whichFreq = where(thisFreq eq sFreqVec, freqCount)
        whichMjd = where(thisMjd eq sMjdVec, mjdCount)
        if freqCount le 0 or mjdCount le 0 then begin
            message,'too many matching frequencies or mjds'
        endif
        ; can only subscript in one dimension at a time
        if freqCount gt mjdCount then begin
            for k=0,mjdCount-1 do begin
                tauZenith[whichMjd[k], whichFreq] = thisTau
            endfor
        endif else begin
            for k=0,freqCount-1 do begin
                tauZenith[whichMjd,whichFreq[k]] = thisTau
            endfor
        endelse
    endfor

    return, tauZenith
end
