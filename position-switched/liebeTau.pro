; procedure to compute the atmospheric opacity from a model
; This procedure will be used when weather data computed by Ron
; Maddalena's models is un-available.
; The procedures were written in Tcl by Ron Maddallena and translated
; to idl by Glen Langston.   The model includes the water line, and
; O2, but not hydrosols (water droplets in clouds and rain).
; HISTORY
; 09DEC03 GIL add interpolated O2 from Lehto Thesis
; 09DEC02 GIL initial version

pro liebeTau, pressureMBar, tempC, dewPtC, freqGHz, tauZenith, doPrint

   if (not keyword_set( pressureMBar)) then begin
      print,'liebeTau: compute zenith opacity based on Liebe 1985 model'
      print,'Uses Lehto approximations for H2O and O2 opacities but '
      print,'does not handle hydrosols'
      print,'usage:  pressureMBar, tempC, dewPtC, freqGHz'
      print,'Where pressureMBar   Atmospheric pressure mBar'
      print,'        tempC        Air Temperature in C'
      print,'        dewPtC       Dew Point Temperature in C'
      print,'        freqGHz      Observing frequency in GHz'
      print,'return tauZenith     Zenith Opacity'
      print,'       doPrint       Optionally print results'
      print,'From the PhD thesis of Harry Lehto (1989)  '
      print,'High Sensitivity Searches for Short Timescale Variability in'
      print,'     Extragalactic Objects'
      print,'R. Maddalena and G. Langston, 2009 December 3'
      return
   endif

   if (freqGHz gt 50.) then begin
      print, 'liebeTau: Frequency above maximum 50GHz'
      zenithTau = 1.0
      return
   endif           

   if (not keyword_set( doPrint)) then doPrint = 0

   waterFreqGHz = 22.23508
   delFreq = waterFreqGHz - freqGHz
   delFreq2 = 2. * delFreq
   if (delFreq lt 0.) then delFreq2 = -2. * delFreq
   delFreq = waterFreqGHz - freqGHz
   sumFreq = waterFreqGHz + freqGHz
   freqSqr = freqGHz * freqGHz
   eta = 1.0
    spawn,'python /home/sandboxes/kfpa_pipeline/partialPressureWater.py ' + pressureMBar +' '+ dewPtC
    readcol,'partialpressure.txt',F='F',eta,/SILENT
    file_delete,'partialpressure.txt'
    presDry = pressureMBar - eta
    tempK = tempC + 273.15
    theta = 300./tempK
    rho = 1.0
    spawn,'python /home/sandboxes/kfpa_pipeline/densityWater.py '+ pressureMBar +' '+ tempC +' '+ dewPtC
    readcol,'waterdensity.txt',F='F',rho,/SILENT
    file_delete,'waterdensity.txt'

    gamma = 2.784e-3 * ((presDry * (theta^0.8)) + (4.80*eta*theta))

    kapa = 1.439e-9 * ((presDry^2) * (theta^2.8) * $\
                      (1. + (1.1*eta/presDry))) / (1. + ((freqGHz/60.)^2))
;    H2OCont = presDry * ( 1. + 38.64*eta*(theta^3)/presDry ) * $\
;      eta * (theta^2.5) * 5.860e-10 * freqSqr

    heightFactor = 1.07 ; = exp(height/11 km) = exp(.8/11)
    H2OCont = 8.120E-7 * (eta/1000.)*(theta^1.5)*freqSqr*heightFactor * rho
;      eta * (theta^2.5) * 5.860e-10 * freqSqr
;   Now compute the opacity per  km at our elevation    
    H2OKappa = rho * gamma / ((delFreq^2) + (gamma^2)) * $\
		6.322e-4 * (freqSqr/waterFreqGHz) * $\
                  ( 1. + (delFreq/sumFreq)^2)
    heightFactor = 0.9181 ;  = exp( - elevation / 9.36 km) = exp ( - .8/9.36)
;   assume that the water vapor extends a few Km in elevation.    
;   The factor 4.0 was chosen to allow approximate matching of model with
;   weather data on 2009 December 3  -- Glen Langston
    H2OLine = 4.0 * heightFactor * H2OKappa

;    H2OLine = 5.049E-3 * (1000./pressureMBar) * (theta^(-.8)) * $\
;                  ( 1. + (delFreq2/freqGHz)) * heightFactor * rho

    dry = 0.00777 * ((presDry/1000.)^2) * (theta^2.8) * $\
                      (1. + (.40*eta/presDry)) / (1. + ((freqGHz/60.)^2))

    tauO2 = 1.0
    ; compute sea level O2 opacity
    opacityO2, freqGHz, tauO2
    heightFactor = 0.9697 ;  = exp( - elevation / 26 km) = exp ( - .8/26)
    tauO2 = tauO2 * (presDry/1000.)^2 * (273./tempK)^3.3 * heightFactor
    tauZenith = dry + H2OCont + H2OLine + tauO2
    if (doPrint gt 0) then print, 'freq, dry, H2OCont, H2OLine, O2, total:', $\
      freqGHz, dry, H2OCont, H2OLine, tauO2, tauZenith
 return
 end




