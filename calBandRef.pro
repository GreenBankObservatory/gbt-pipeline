;IDL Procedure to test cal noise diode based calibration
;HISTORY
; 09NOV19 GIL replace pair of polarization processes with loop
; 09NOV18 GIL fix indexing of polarizations
; 09NOV13 GIL use getTau() to get the predicted tau for this date
; 09NOV12 GIL use only the on-off 3C48 scans to define the cal reference
; 09NOV11 GIL initial test of gainScanInt2
; 09NOV10 GIL use ratioScanInt2.pro 


pro calBandRef, allscans, refScans, iBand, nFeed, nPol, doWait

   if (not keyword_set( allscans)) then begin
      print, 'calBandRef: calibrates all obs of a band GBT scans.'
      print, 'usage: cal, allScans, refScans, feedInN, bandInN, polN'
      print, '   allScans  all scans to include in the map'
      print, '   refScans  begin and end reference scans'
      print, '    bandInN  single observation band number, range 0 to n-1'
      print, '      nFeed  number of feeds to process range 1 to n'
      print, '       nPol  number of polarizations to process 1 to n'
      print, '     doWait  optionally wait for user input to continue cal'
      print, 'Output is to a log file and keep files'
      print, '----- Glen Langston, 2009 November 19; glangsto@nrao.edu'
      return
   endif

   doShow = 1
   if (not keyword_set(nPol)) then nPol = 2
   if (not keyword_set(nFeed)) then nFeed = 2
   if (not keyword_set(doWait)) then doWait=0

   for iFeed = 0, (nFeed-1) do begin 
      print, '************ Band ', iBand, ' Feed ',iFeed,' **************'
      for iPol = 0, (nPol-1) do begin 
         ; pol, beginning reference
         gettp, refscans[0], int=0, plnum=iPol, fdnum=iFeed, ifnum=iBand
         data_copy, !g.s[0], dcBRef0
         data_copy, !g.s[0], dcCal0
         data_copy, !g.s[0], dcRef0
         getRef, refscans[0], iPol, iBand, iFeed, dcBRef0, dcCal0, doShow
         ; pol, end reference
         gettp, refscans[1], int=0, plnum=0, fdnum=iFeed, ifnum=iBand
         ; prepare to create the output calibration file name
         mapName = !g.s[0].source
         mapType = 'Cal' 
         firstLast = [allscans[0], allscans[n_elements(allscans)-1]]
         nameMap, !g.s[0], mapName, firstLast, mapType
         data_copy, !g.s[0], dcERef0
         getRef, refscans[1], iPol, iBand, iFeed, dcERef0, dcCal0, doShow

         ; prepare to get tau for these obs
         obsDate = dcBRef0.timestamp
         obsMjd =  dateToMjd( obsDate)
         freqMHz = dcBRef0.observed_frequency  * 1.E-6
 ; get and report tau
         zenithTau = getTau( obsMjd, freqMHz)
         print,'Obs:',dcBRef0.projid,' ',obsDate, ' Freq:',freqMHz, $\
          ' (MHz) Tau: ',zenithTau

      ; compute the cal references from all scans
      ; get references for the beginning of the map
         getRef, allscans, iPol, iBand, iFeed, dcRef0, dcCal0, doshow

      ; show the before and after reference for both polarizations.
         show,dcBRef0
         oshow,dcERef0
         oshow,dcCal0
;        create containers for scaled cal values and references
         data_copy, dcCal0, dcSCal0
         data_copy, dcBRef0, dcSBRef0
         data_copy, dcERef0, dcSERef0

; compute the cal references from all scans
; do the pre-computations to save later calculations
         scaleRef, dcBRef0, dcCal0, dcSBRef0, dcSCal0
         scaleRef, dcERef0, dcCal0, dcSERef0, dcSCal0
      ;now save the reference spectra
         refname = 'bref'
         reftype = 'BRef_'
         saveDc, dcSBRef0, refname, reftype
         print, 'Saved: ', refname
         refname = 'eref'
         reftype = 'ERef_'
         saveDc, dcSERef0, refname, reftype
         print, 'Saved: ', refname
      ;next save the calibration spectra
         refname = 'scal'
         reftype = 'CRef_'
         saveDc, dcSCal0, refname, reftype
         print, 'Saved: ', refname
      ; reference scaled cals are approxmately tRx
         sety, -1, 50.
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
; about to create the valuable product, keep it!
         doKeep = 1 & sety,-1,8
   ; for all polarizations, process and keep the data
         scaleIntsRef, allscans, iPol, iBand, iFeed, dcSBRef0, dcSERef0, $\
           dcSCal0, doKeep 

                                ; now clean up all accumulated memory   
         data_free, dcCal0 & data_free, dcSCal0
         data_free, dcBRef0 & data_free, dcSBRef0 & data_free, dcRef0 
         data_free, dcERef0 & data_free, dcSERef0

      endfor                   ; end for all polarizations
   endfor                      ; end for all feeds  

return
end                         ; end of calBand.pro
