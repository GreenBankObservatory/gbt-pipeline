; IDL proceedure to compile GBTIDL scripts for use in the pipeline process
; HISTORY
; 09Oct23 GIL initial version taken from map3c48

;Functions MUST be compiled first!!!
; Ron's weather scripts
.compile getTau.pro
.compile dateToMjd.pro

;Weather model when date is before 04 May 01
.compile humidityToTDew.pro
.compile partialPressureWater.pro
.compile densityWater.pro
.compile opacityO2.pro
.compile liebeTau.pro

;Now compile proceedures
.compile etaGBT.pro
.compile opacity.pro
.compile natm.pro
.compile tatm.pro
.compile refbeamposition.pro
.compile tsysair.pro
.compile getRef.pro
.compile setTSky.pro
.compile aveDcs.pro
.compile scaleRef.pro
.compile scaleInts.pro
.compile scaleIntsRef.pro
.compile nameDc.pro
.compile saveDc.pro
.compile nameMap.pro

; calBand and calBandRef are the two main calibration routines, which
; call other procedures.
.compile calBand.pro
.compile calBandRef.pro

