;IDL Procedure to fully name and name a data container (dc)
;HISTORY
; 09NOV17 GIL initial version

pro nameMap, myDc, fileName, scans, type

   if (not keyword_set( fileName)) then begin
      print, 'nameMap: name calibrated map data, with observing details'
      print, 'usage: nameMap, myDc, fileName, scans, type'
      print, 'where myDc data container to save'
      print, '  filename file name for this map'
      print, '     scans list of scans identifying map (ie first and last)'
      print, '      type pre-pended file type or identifier string (optional)'
      print, ''
      print, '----- Glen Langston, 2009 November 17; glangsto@nrao.edu'
      return
   endif

   if (not keyword_set (type)) then type = '' 

   scanStr = ''

   if (keyword_set (scans)) then begin
      for i = 0, (n_elements( scans) - 1) do begin
         scanStr = scanStr + strtrim( string( scans[i]),2) + '_'
      endfor
   endif 

   ; construct integer frequency MHz   
   doppler = 1.0+(myDc.source_velocity/299792458.)
   iFreq = round( doppler*myDc.reference_frequency * 1.E-6)
   sfreq = strtrim(fstring( iFreq,'(f7.0)'),2)
   ; source and scan numbers
   src=strtrim(string(myDc.source),2)
   iFeed=strtrim(fstring(myDc.feed,'(I3)'),2)
   fileName=type + '_' + src + '_' + iFeed + '_' + scanStr $\
     + sfreq + 'fits'

   return
end


