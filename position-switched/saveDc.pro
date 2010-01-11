;IDL Procedure to fully name and save a data container (dc)
;HISTORY
; 09NOV17 GIL initial version

pro saveDc, myDc, fileName, type

   if (not keyword_set( myDc)) then begin
      print, 'saveDc: save a data container, with fully qualified name'
      print, 'usage: saveDc, myDc, fileName, type
      print, 'where   myDc data container to save'
      print, '    filename string file name to be created (output)'
      print, '    type     prepended identifier string (input)'
      print, ''
      print, '----- Glen Langston, 2009 November 16; glangsto@nrao.edu'
      return
   endif

   if (not keyword_set(fileName)) then fileName = '' 
   if (not keyword_set(type)) then type = '' 

   ; create the file name
   nameDc, myDc, fileName, type

   ; save the data container
   save, myDc,filename=fileName
   return
end


