def getRef(scans, iPol, iBand, iFeed, dcRef, dcCal):
    """Average integrations to calc. reference and cal on-off spectra

    Keyword arguments:
    scans -- integer array of scan numbers to average
    iPol -- observation polarization number, range 0 to n-1
    iBand -- observation band number, range 0 to n-1
    iFeed -- observation feed number, range 0 to n-1

    Returns:
    #       Outputs are data containers'
    # output dcRef reference spectrum, average of cal ON and CAL off values'
    # output dcCal reference cal_on - cal_off spectrum'
    #       doShow optionally (doShow=1) show spectra accumulated'

    """

    #  prepare to compute sums 
    tSum = 0.0
    elSum = 0.0
    azSum = 0.0
    lonSum = 0.0
    latSum = 0.0 
    tLatSum = 0.0
    tLonSum = 0.0

    spectrum = gettp(scans[0], int=0, plnum=iPol, ifnum=iBand, fdnum=iFeed)

    #  copy most parameters to outputs
    dcRef = spectrum
    dcCal = spectrum

    spectrum_sum = []         #  structure to hold the ongoing sum

    nScans = len(scans)

    for iScan in range(nScans-1):
        calOns = getchunk(scan=scans[iScan], cal="T", plnum=iPol, \
                          ifnum=iBand, fdnum=iFeed)
     
     for i in range(len(calOns)-1):
         dcaccum, a, calOns[i]
       
     #  get average coordiate and system temps
     for i in range(len(calOns)):
       tInt=calOns[i].exposure & tSum=tSum+tInt
       elSum=elSum+(tInt*calOns[i].elevation)
       azSum=azSum+(tInt*calOns[i].azimuth)
       lonSum=lonSum+(tInt*calOns[i].longitude_axis)
       latSum=latSum+(tInt*calOns[i].latitude_axis)
       tLonSum=tlonSum+(tInt*calOns[i].target_longitude)
       tLatSum=tlatSum+(tInt*calOns[i].target_latitude)

     #  now clean up
     for i=0,n_elements(calOns)-1 do begin 
        data_free, calOns[i]
     endfor
   endfor

   accumave, a, calOnAve   #  get the average
   #  now start Cal Off average
   accumclear, a       #  clear it

   for iScan=0, (nScans-1) do begin

     calOfs = getchunk(scan=scans[iScan], cal="F", plnum=iPol, $\
                       ifnum=iBand, fdnum=iFeed)

     for i=0,n_elements(calOfs)-1 do begin 
        data_free, calOfs[i]
     endfor
   endfor  

   accumave,a, calOfAve    #  get the average

   # now complete cal on - cal off spectrum and store as a data container
   setdcdata, dcCal, (*calOnAve.data_ptr - *calOfAve.data_ptr)

   # now complete (cal on + cal off)/2 spectrum and store as a data container
   setdcdata, dcRef, (*calOnAve.data_ptr + *calOfAve.data_ptr)*0.5

   #  normalize the sums and transfer to output
   dcCal.elevation = elSum/tSum
   dcCal.azimuth   = azSum/tSum
   dcCal.longitude_axis = lonSum/tSum
   dcCal.latitude_axis  = latSum/tSum
   dcCal.target_longitude = tLonSum/tSum
   dcCal.target_latitude  = latSum/tSum
   dcCal.exposure  = tSum

   dcRef.elevation = elSum/tSum
   dcRef.azimuth   = azSum/tSum
   dcRef.longitude_axis = lonSum/tSum
   dcRef.latitude_axis  = latSum/tSum
   dcRef.target_longitude = tLonSum/tSum
   dcRef.target_latitude  = latSum/tSum
   dcRef.exposure  = tSum

   #  prepare to compute system temperature sums
   nChan = n_elements( *dcRef.data_ptr)
   bChan = round(nChan/10)
   eChan = nChan - bChan

   #  compute spectrum in units of cal
   ratios = (*dcRef.data_ptr)[bChan:eChan] / (*dcCal.data_ptr)[bchan:echan] 
   #  
   tSys = avg( ratios)*dcRef.mean_tcal
   dcCal.tsys = tSys
   dcRef.tsys = tSys

   if !g.has_display then unfreeze

   data_free, calOfAve & data_free, calOnAve
   accumclear, a & data_free, calOfAve & data_free, calOnAve


