function getTau, mjd, freqMHz

    ; getTau: Retrieves archived tau prediction for date and frequency
    ; 
    ;
    ; Usage:    getTau(mjd, freqMHz)
    ; where  mjd       Modified Julian Date of observations (ie 54881 etc)
    ;        freqMHz   Frequency in MHz of observations
    ;
    ; Returns computed opacity value at zenith (range 0 to > 1)
    ;
    ; Uses getForecastValues, written by Ron Maddalena
    ; Function returns string like : Opacity(22.2350,54873.381) = 0.17310
    ; getTau() parses the string and returns the zenith opacity
    ; '
    ; Glen Langston, 2009 February 19
    ; Modified by RJM, April, 2009

    if (n_params() lt 2) then begin
        message, 'Usage: getTau(MJD, FreqMHz)'
    endif

    ; if date before 2004 May 01 == mjd 53126 or low freq, use liebeTau.pro
    if ((mjd lt 53126) or (freqMHz le 2000.)) then begin
       tempC = !g.s[0].tambient - 273.15
       humidity = !g.s[0].humidity
       dewPtC = tempC
       humidityToTDew, humidity, tempC, dewPtC
       freqGHz = freqMHz*.001
       pressureMBar = !g.s[0].pressure*0.01
       tauZenith = 1.0
       liebeTau, pressureMBar, tempC, dewPtC, freqGHz, tauZenith
;       print, 'LiebeTau: p, T, DT, F, tau:',pressureMBar, tempC, dewPtC, freqGHz, tauZenith
       return, tauZenith
    endif 

    spawn, '/users/rmaddale/bin/getForecastValues -timeList ' + string(mjd) + ' -freqList ' + string( freqMHz/1000.), result
    n = strpos(result,'=')
    if (n le 0) then begin
	message, 'Error: Cannot read results from getForecastValues'
    endif
    tau = float(strmid(result,n+1))
    if (tau lt 0) then begin
	message, 'Error: getForecastValues cannot determine opacity.  Date must be > May 1, 2004, frequency > 2000 and < 1160000 MHz'
    endif
    return, tau
end
