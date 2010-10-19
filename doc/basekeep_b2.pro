; *********************************************************
  PRO basekeep_b2,scan1,scan2, tau_np, nfit, unit, apeff, ref
; *********************************************************
; April 12, 2006 - Program to run through individual rows in GBT OTF
;                  data from scan1 to scan2. Shifts velocities due to
;                  Doppler tracking errors (telescope Doppler tracks
;                  correctly on the first LO only) and performs
;                  polynomial baseline subtraction. Main program must
;                  have a fileout command. Remember numbering starts
;                  at zero. Will need to apply an opacity correction
;                  in getfs. 
;                  From script originally by Jay Lockman @ NRAO.
; getfs - Calibrates the frequency switched data, folds the data, and
;         stores the result in the primary data container (PDC).
; LongMaps made with width 300" (B2), scan rate 4"/s, dump every 3s
; Baseline fitting region set using April 9, 2006 averaged scans #22-59
; June 26, 2006 - added unit parameter to set units of Jy/beam or K as 
; desired.
; June 29, 2006 - added code to extract positive spectrum channels
; Oct. 31, 2006 - edited code to accept a reference spectrum to align all 
;                 spectra in final file.

; Freeze command suppresses plotting
  freeze

; set up windows for baselining
  nregion,[500,2400,2525,2580,2865,2925,3025,3095,3190,3260,3535,3610,3700,3780,3860,3930,4210,4280,4400,6500]

; Loop through scan, integration, polarization
  FOR c=scan1,scan2 DO BEGIN
      s=scan_info(c)
      n=s.n_integrations
      print,c
      FOR d=0,n-1 DO BEGIN
	FOR i=0,1 DO BEGIN
	      IF unit EQ 'Ta*' THEN BEGIN
		getfs,c,ifnum=1,intnum=d,plnum=i,tau=tau_np,units=unit,/quiet
	      ENDIF ELSE BEGIN
	      	getfs,c,ifnum=1,intnum=d,plnum=i,tau=tau_np,units=unit,$
		      ap_eff=apeff,/quiet
	      ENDELSE
; Insert rest frequency (Hz) for the NH3(1,1) line
              !g.s[0].line_rest_frequency = 23.6945060e+9
; baseline subtracts polynomial from PCD spectrum
              baseline,nfit=nfit
; extract channels with positive signal (avoid fs-negative spectra)
              x = dcextract(!g.s[0],3025,3780)
; Align frequency with ref scan
	      sclear
	      set_data_container, ref
	      accum
	      set_data_container, x
              fs = fshift()
              gshift,fs,/wrap
; Save to new file
	      keep,!g.s[0]
	END
      END
  END
  unfreeze

  END
