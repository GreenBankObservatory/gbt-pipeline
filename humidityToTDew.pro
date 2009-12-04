; humidityToTDew utility function

pro humidityToTDew, humidity, tempC, tDewC

   if (not keyword_set( humidity)) then begin
      print, 'humidityToTDew: converts from relative humidity to dew point'
      print, 'usage: humidityToTDew, humidity, tempC, tDewC'
      print, 'where humidity    relative humidity, range 0 to 1'
      print, '       tempC      Air temperature (C)'
      print, 'return tDewC      Dew point temperature (C)'
      print, ' Glen Langston 2009 Dec 3'
      return
   endif


   if ((humidity gt 1) or (humidity lt 0)) then begin
      print,'humidityToTDew: humidity range is 0 to 1: ',$\
          humidity, ' is out of range'
      tDewC = tempC
      return
   endif


   a = 17.27
   b = 237.7  ; Celsius
   alpha = ((a*tempC)/(b+tempC)) + alog( humidity)

   tDewC = (b * alpha)/ (a - alpha)
return
end
