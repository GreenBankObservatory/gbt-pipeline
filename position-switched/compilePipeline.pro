; IDL proceedure to compile GBTIDL scripts for use in the pipeline process
; HISTORY
; 10Jan22 GIL add produres for finding lines
; 09Oct23 GIL initial version taken from map3c48

;Functions MUST be compiled first!!!
; Ron's weather scripts
.compile getTau.pro
;Weather model when date is before 04 May 01
.compile opacityO2.pro
.compile liebeTau.pro
;Now compile proceedures
.compile opacity.pro
.compile natm.pro
.compile tatm.pro
.compile smoothCal.pro
.compile refbeamposition.pro
; .compile tsysair.pro  ; currently not used
.compile getRef.pro
.compile setTSky.pro
.compile scaleRef.pro
.compile scaleIntsRef.pro
; .compile nameDc.pro
; .compile saveDc.pro
.compile nameMap.pro
; calBandRef is the main calibration routine, which
; calls other procedures.
.compile calBandRef.pro
; add procedures to find lines
.compile moleculeinrange.pro
.compile freqchan.pro
.compile toaips.pro
