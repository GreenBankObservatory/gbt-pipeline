#! /usr/bin/env python

"""Procedure to test cal noise diode based calibration

"""

def calBandRef( allscans, refScans, iBand, nFeed=2, nPol=2, doWait=0):
"""Calibrates all obs of a band GBT scans

    Keyword arguments:
    
    allScans -- all scans to include in the map
    refScans -- begin and end reference scans
    bandInN -- single observation band number, range: 0 to n-1
    nFeed -- number of feeds to process range: 1 to n
    nPol -- number of polarizations to process: 1 to n
    doWait -- optionally wait for user input to continue cal

    Output is to a log file and keep files.

"""
   # for each beam or feed
   for iFeed in range(nFeed):
 
      print  '************ Band', str(iBand),' Feed ',str(iFeed),' **************'

      # for each polarization
      for iPol in range(nPol):

         #  pol, beginning reference
         getRef, refscans[0], iPol, iBand, iFeed, dcBRef0, dcCal0, doShow

         #  prepare to create the output calibration file name
         mapName = !g.s[0].source
         mapType = 'Cal' 

         firstLast = [allscans[0], allscans[n_elements(allscans)-1]]
         nameMap, !g.s[0], mapName, firstLast, mapType
         data_copy, !g.s[0], dcERef0

         #  pol, end reference
         getRef, refscans[1], iPol, iBand, iFeed, dcERef0, dcCal0, doShow

         #  prepare to get tau for these obs
         obsDate = dcBRef0.timestamp
         obsMjd =  dateToMjd( obsDate)
         freqMHz = dcBRef0.observed_frequency  * 1.E-6
         
         #  get and report tau
         zenithTau = getTau( obsMjd, freqMHz)
         print 'Obs:',dcBRef0.projid,' ',obsDate, ' Freq:',freqMHz, $\
          ' (MHz) Tau: ',zenithTau

      #  compute the cal references from all scans
      #  get references for the beginning of the map
         getRef, allscans, iPol, iBand, iFeed, dcRef0, dcCal0, doshow

#         create containers for scaled cal values and references
         data_copy, dcCal0, dcSCal0
         data_copy, dcBRef0, dcSBRef0
         data_copy, dcERef0, dcSERef0

#  compute the cal references from all scans
#  do the pre-computations to save later calculations
         scaleRef, dcBRef0, dcCal0, dcSBRef0, dcSCal0
         scaleRef, dcERef0, dcCal0, dcSERef0, dcSCal0
      # now save the reference spectra
         refname = 'bref'
         reftype = 'BRef_'
         saveDc, dcSBRef0, refname, reftype
         print  'Saved: ', refname
         refname = 'eref'
         reftype = 'ERef_'
         saveDc, dcSERef0, refname, reftype
         print  'Saved: ', refname
      # next save the calibration spectra
         refname = 'scal'
         reftype = 'CRef_'
         saveDc, dcSCal0, refname, reftype
         print  'Saved: ', refname
      #  reference scaled cals are approxmately tRx

#  clean up any old keep files and prepare to create new
         if (iPol eq 0) then begin
            file_delete, mapName, /ALLOW_NONEXISTENT
            fileout, mapName
         endif
#  about to create the valuable product, keep it!
         doKeep = 1
   #  for all polarizations, process and keep the data
         scaleIntsRef, allscans, iPol, iBand, iFeed, dcSBRef0, dcSERef0, $\
           dcSCal0, doKeep 

                                #  now clean up all accumulated memory   
         data_free, dcCal0 & data_free, dcSCal0
         data_free, dcBRef0 & data_free, dcSBRef0 & data_free, dcRef0 
         data_free, dcERef0 & data_free, dcSERef0

      endfor                   #  end for all polarizations
   endfor                      #  end for all feeds  

return
end                         #  end of calBand.pro
