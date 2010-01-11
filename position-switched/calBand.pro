;IDL Procedure to test cal noise diode based calibration
;HISTORY
; 09DEC01 GIL use refScans
; 09NOV19 GIL replace pair of polarization processes with loop
; 09NOV19 GIL replace pair of polarization processes with loop
; 09NOV18 GIL fix indexing of polarizations
; 09NOV13 GIL use getTau() to get the predicted tau for this date
; 09NOV12 GIL use only the on-off 3C48 scans to define the cal reference
; 09NOV11 GIL initial test of gainScanInt2
; 09NOV10 GIL use ratioScanInt2.pro 


pro calBand, allScans, refScans, iBand, nFeed, nPol, doWait, bChan, eChan

   if (not keyword_set( allScans)) then begin
      print, 'calBand: calibrates all obs of a band for GBT scans.'
      print, 'values must be pre-computed and scaled with scaleRef()'
      print, 'usage: cal, allScans, refScans, feedInN, bandInN, polN'
      print, '   allScans  all scans to include in the map'
      print, '   refScans  reference scans for average Cal Signal'
      print, '    bandInN  single observation band number, range 0 to n-1'
      print, '      nFeed  number of feeds to process range 1 to n'
      print, '       nPol  number of polarizations to process 1 to n'
      print, '     doWait  optionally wait for user input to continue cal'
      print, 'Output is to a log file and keep files'
      print, '----- Glen Langston, 2009 November 13; glangsto@nrao.edu'
      return
   endif

   doShow = 1
   if (not keyword_set(nPol)) then nPol = 2
   if (not keyword_set(nFeed)) then nFeed = 2
   if (not keyword_set(doWait)) then doWait=0

   gettp, allScans[0], int=0, plnum=0, fdnum=0, ifnum=iBand
   nChan = n_elements( *!g.s[0].data_ptr)
   ; trim a small part of ends of spectrum (rouns to even 1000s of channels)
   if (not keyword_set(bChan)) then bChan = (12 * round( nChan/1024)) + 100
   if (not keyword_set(eChan)) then eChan = nChan - (bChan + 1)

   for iFeed = 0, (nFeed-1) do begin 
      print, '************ Band ', iBand, ' Feed ',iFeed,' **************'
      for iPol = 0, (nPol-1) do begin 
                  ; pol, beginning reference
         gettp, allScans[0], int=0, plnum=iPol, fdnum=iFeed, ifnum=iBand
         data_copy, !g.s[0], dcRef0
         data_copy, !g.s[0], dcCal0
         mapName = !g.s[0].source
         mapType = 'TCal' 
         firstLast = [allScans[0], allScans[n_elements(allScans)-1]]
         nameMap, !g.s[0], mapName, firstLast, mapType
         ; prepare to get tau for these obs
         obsDate = dcRef0.timestamp
         obsMjd =  dateToMjd( obsDate)
         freqMHz = dcRef0.observed_frequency  * 1.E-6
 ; get and report tau
         zenithTau = getTau( obsMjd, freqMHz)
         print,'Obs:',dcRef0.projid,' ',obsDate, ' Freq:',freqMHz, $\
          ' (MHz) Tau: ',zenithTau

      ; compute the cal references from all scans
      ; get references for the beginning of the map
         getRef, refScans, iPol, iBand, iFeed, dcRef0, dcCal0, doshow

      ; show the before and after reference for both polarizations.
         show,dcRef0

;        create containers for scaled cal values and references
         data_copy, dcCal0, dcSCal0
         data_copy, dcRef0, dcSRef0

; compute the cal references from all scans
; do the pre-computations to save later calculations
         scaleRef, dcRef0, dcCal0, dcSRef0, dcSCal0
      ;next save the calibration spectra
         refname = 'scal'
         reftype = 'TRef_'
         saveDc, dcSCal0, refname, reftype
         print, 'Saved: ', refname
      ; reference scaled cals are approxmately tRx
         show, dcSCal0
         if (doWait gt 0) then begin 
            print,'Enter X to continue (Pol ',dcSCal0.polarization,' :'
            read,x
         endif

; clean up any old keep files and prepare to create new
         if (iPol eq 0) then begin
           file_delete, mapName, /ALLOW_NONEXISTENT
           fileout, mapName
         endif
; for this polarization, process and keep the data
         scaleInts, allScans, iPol, iBand, iFeed, dcSCal0, bChan, eChan 

                                ; now clean up all accumulated memory   
         data_free, dcCal0 & data_free, dcSCal0 
         data_free, dcRef0 & data_free, dcSRef0 

      endfor                   ; end for all polarizations
   endfor                      ; end for all feeds  

return
end                         ; end of calBand.pro
