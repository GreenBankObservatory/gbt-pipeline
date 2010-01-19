;IDL Procedure to fully name and name a data container (dc)
;HISTORY
; 09NOV17 GIL initial version

pro nameDc, myDc, fileName, type

   if (not keyword_set( fileName)) then begin
      print, 'nameDc: name a data container, with observing details'
      print, 'usage: nameDc, myDc, fileName, type'
      print, 'where myDc data container to save'
      print, '  filename file name for this data container'
      print, '      type pre-pended file type or identifier string (optional)'
      print, ''
      print, '----- Glen Langston, 2009 November 17; glangsto@nrao.edu'
      return
   endif

   if (not keyword_set (type)) then type = '' 
   
   ; construct integer frequency MHz   
   doppler = 1.0+(myDc.source_velocity/299792458.)
   iFreq = round( doppler*myDc.reference_frequency * 1.E-6)
   sfreq = strtrim(string( iFreq,'(f7.0)'),2)
   ; source and scan numbers
   src=strtrim(string(myDc.source),2)
   sscn=strtrim(string(myDc.scan_number,format='(I6)'),2)
   pol=strtrim(myDc.polarization,2)
   iFeed=strtrim(string(myDc.feed,format='(I3)'),2)
   fileName=type + myDc.projid + '_' + src + '_' $\
     + pol + '_' + iFeed + '_' + sscn + '_' + sfreq + 'dc'

   return
end


