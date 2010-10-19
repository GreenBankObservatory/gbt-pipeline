; ***************************
  PRO b2_reduce_1, unit
; ***************************
; Program to reduce GBT frequency switched OTF map data
; First must calibrate EACH INDIVIDUAL INTEGRATION
; Use frequency switch track calibration model
; MUST use GBTIDL - either install locally or log in to thales.gb.nrao.edu
; Edited for use on April 10 data
; This program takes a LONG time on otter
; June 26, 2006 - updated to return data in Jy/beam

; Semester 06A data information
; IFs: (0) - CCS (1) - NH3(1,1) (2) - NH3(2,2) (3) - HC5N (just for fun)
; Aperture efficiency from calibration observations of 3C286
  apeff=0.59

; Set reference scan
  sclear
  filein,'b1.10.extract.fits'
  print,'B1 reference scan read'
  get,scan=108,plnum=0,int=0
  ref = dcextract(!g.s[0],0,755)

; Read in data (assume has been converted to sdfits already)
  filein,'AGBT06A_065_01.raw.acs.fits'
  print,'File read'

; Create an output file to 'keep' to
; First night data
  fileout,'b2.1.fits'

; nfit = 4 might better fit baseline
  nfit=4

  tau_np = 0.0437
  basekeep_b2,17,21,tau_np,nfit, unit, apeff, ref

  tau_np = 0.0437
  basekeep_b2,22,59,tau_np,nfit, unit, apeff, ref

  tau_np = 0.0420
  basekeep_b2,65,102,tau_np,nfit, unit, apeff, ref

  tau_np = 0.0410
  basekeep_b2,110,147,tau_np,nfit, unit, apeff, ref

  END



