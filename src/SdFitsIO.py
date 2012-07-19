import csv
from collections import OrderedDict
from Calibration import Calibration
from pipeutils import Pipeutils

class SdFitsIO:
    """Class contains methods to read and write to the GBT SdFits format.
    
    This includes code for both the FITS files and associated index files.
    
    A description (but not a definition) of the SD FITS is here:
    https://safe.nrao.edu/wiki/bin/view/Main/SdfitsDetails
    
    """
    
    def __init__(self):
        
        self.pu = Pipeutils()
    
    def check_for_sdfits_file( self, infile, sdfitsdir, beginscan, endscan,\
                               refscan1, refscan2, VERBOSE ):
        """Check for the existence of the SDFITS input file.
        
        If the SDFITS input file exists, then use it. Otherwise,
        recreate it from the project directory, if it is provided.
        
        Keywords:
        infile -- an SDFITS file path
        sdfitsdir -- an archive directory path as an alternative to an SDFITS file
        beginscan -- optional begin scan number for filling by sdfits
        endscan -- optional end scan number for filling by sdfits
        refscan1 -- optional reference scan number for filling by sdfits
        refscan2 -- optional reference scan number for filling by sdfits
        VERBOSE -- verbosity level
        
        Returns:
        SDFITS input file path
        
        """
        # if the SDFITS input file doesn't exist, generate it
        if (not os.path.isfile(infile) and os.path.isdir(sdfitsdir)):
            if VERBOSE > 0:
                print "SDFITS input file does not exist; trying to generate it from",\
                      "sdfits-dir input parameter directory and user-provided",\
                      "begin and end scan numbers."
    
            if not os.path.exists('/opt/local/bin/sdfits'):
                print "ERROR: input sdfits file does not exist and we can not"
                print "    regenerate it using the 'sdfits' filler program in"
                print "    Green Bank. (/opt/local/bin/sdfits).  Exiting"
                sys.exit(2)
    
            if beginscan and endscan:
                if not beginscan <= endscan:
                    print 'ERROR: begin scan is greater than end scan',beginscan,'>',endscan
                    sys.exit(9)
    
            if beginscan or endscan or refscan1 or refscan2:
    
                scanslist = [beginscan,endscan,refscan1,refscan2]
                while(True):
                    try:
                        scanslist.remove(False)
                    except(ValueError):
                        break
    
                minscan = min(scanslist)
                maxscan = max(scanslist)
    
            if minscan and not maxscan:
                scanrange = '-scans=' + str(minscan) + ': '
            elif maxscan and not minscan:
                scanrange = '-scans=:'+ str(maxscan) + ' '
            elif minscan and maxscan:
                scanrange = '-scans=' + str(minscan) + ':' + str(maxscan) + ' '
            else:
                scanrange = ''
    
            sdfitsstr = '/opt/local/bin/sdfits -fixbadlags ' + \
                        scanrange + sdfitsdir
    
            if VERBOSE > 0:
                print sdfitsstr
    
            os.system(sdfitsstr)
            
            filelist = glob.glob(os.path.basename(sdfitsdir)+'.raw.*fits')
            if 1==len(filelist):
                infile = filelist[0]
            elif len(filelist) > 1:
                print "ERROR: too many possible SDFITS input files for pipeline"
                print "    please check input directory for a single"
                print "    raw fits file with matching index file"
                sys.exit(3)
            else:
                print "ERROR: could not identify an input SDFITS file for the"
                print "    pipeline.  Please check input directory."
                sys.exit(5)
    
            # if the SDFITS input file exists, then use it to create the map
            if os.path.isfile(infile):
                if VERBOSE > 2:
                    print "infile OK"
            else:
                if VERBOSE > 2:
                    print "infile not OK"
    
        return infile
    
  
    def get_start_mjd(self, indexfile,verbose=0):
        """Get the start date (mjd) of the session
    
        Keywords:
        indexfile -- file which contains integrations with time stamps
        verbose -- optional verbosity level
    
        Returns:
        The session start date (mjd) as an integer
        
        """
        myFile = open(indexfile,'rU')
    
        # skip over the index file header lines
        while True:
            row = myFile.readline().split()
            if len(row)==40:
                # we just found the column keywords, so read the next line
                row = myFile.readline().split()
                break
    
        dateobs = row[34]
        start_mjd = dateToMjd(dateobs)
        myFile.close()
        return int(start_mjd)
    
    def get_masks(self, indexfile,fitsfile=None,samplers=[],verbose=0):
        """Create a mask on the input file for each sampler
    
    
        Keywords:
        indexfile -- used to find integrations for each sampler
        fitsfile -- used to get length of table
        samplers -- (list) of samplers which is set when only masks for some
            samplers are desired
        verbose -- optional verbosity on output
    
        Returns:
        a (dictionary) of the form:
        mask[fits block][sampler name] = boolean mask on block table
    
        """
        myFile = open(indexfile,'rU')
        table_length = []
        if fitsfile:
            fd = pyfits.open(fitsfile,memmap=1,mode='readonly')
    
            # one set of masks per FITS extension
            # each set of masks has a mask for each sampler
            mask = []
            for blockid in range(1,len(fd)):
                table_length.append(fd[blockid].header['naxis2'])
                mask.append({})
    
            fd.close()
        else:
            if not bool(table_length):
                print 'ERROR: either fits file or table size must be provided'
                return False
    
        # skip over the index file header lines
        while True:
            row = myFile.readline().split()
            if len(row)==40:
                # we just found the column keywords, so read the next line
                row = myFile.readline().split()
                break
    
        while row:
            
            sampler = row[20]
            ii = int(row[4])
            extension_idx = int(row[3])-1  # FITS extention index, same as blockid +1 (above)
    
            # if samplers is empty, assume all samplers
            # i.e. not samplers == all samplers
            # if 1 or more sampler is specified, only use those for masks
            if (not samplers) or (sampler in samplers):
                
                # add a mask for a new sampler
                if not sampler in mask[extension_idx]:
                    mask[extension_idx][sampler] = np.zeros((table_length[extension_idx]),dtype='bool')
    
                mask[extension_idx][sampler][ii] = True
                
            # read the next row
            row = myFile.readline().split()
    
        # print results
        for idx,maskblock in enumerate(mask):
            total = 0
            if verbose: print '-------------------'
            if verbose: print 'EXTENSION',idx+1
            if verbose: print '-------------------'
            for sampler in maskblock:
                total = total + maskblock[sampler].tolist().count(True)
                if verbose: print sampler,maskblock[sampler].tolist().count(True)
            if verbose: print 'total',total
            
        myFile.close()
        
        return mask
    
    def get_maps_and_samplers(self, allmaps,indexfile,debug=False):
        """Find mapping blocks. Also find samplers used in each map
    
        Keywords:
        allmaps -- when this flag is set, mapping block discovery is enabled
        indexfile -- input required to search for maps and samplers
        debug -- optional debug flag
    
        Returns:
        a (list) of map blocks, with each entry a (tuple) of the form:
        (int) reference 1,
        (list of ints) mapscans,
        (int) reference 2,
        samplermap,
            (dictionary) [sampler] = (int)feed, (string)pol, (float)centerfreq
        'PS' -- default representing Position-switched
                this will change to when FS-mode is supported with map discovery
        
        """
    
        myFile = open(indexfile,'rU')
        
        scans = {}
        map_scans = {}
    
        # skip over the index file header lines
        while True:
            row = myFile.readline().split()
            if len(row)==40:
                # we just found the column keywords, so read the next line
                row = myFile.readline().split()
                break
    
        samplermap = {}
        while row:
    
            obsid = row[7]
            scan = int(row[10])
            sampler = row[20]
            feed = int(row[14])
            pol = row[11]
            centerfreq = float(row[29])
    
            if not scan in scans:
                samplermap = {}
    
            samplermap[sampler] = (feed,pol,centerfreq)
            scans[scan] = (obsid,samplermap)
    
            # read the next row
            row = myFile.readline().split()
    
        myFile.close()
    
        # print results
        if debug:
            print '------------------------- All scans'
            for scan in scans:
                print 'scan',scan,scans[scan][0]
    
            print '------------------------- Relavant scans'
    
        for scan in scans:
            if scans[scan][0].upper()=='MAP' or scans[scan][0].upper()=='OFF':
                map_scans[scan] = scans[scan]
    
        mapkeys = map_scans.keys()
        mapkeys.sort()
    
        if debug:
            for scan in mapkeys:
                print 'scan',scan,map_scans[scan][0]
    
        maps = [] # final list of maps
        ref1 = False
        ref2 = False
        prev_ref2 = False
        mapscans = [] # temporary list of map scans for a single map
    
        if debug:
            print 'mapkeys', mapkeys
    
        samplermap = {}
    
        if not allmaps:
            return scans
            
        for idx,scan in enumerate(mapkeys):
    
            # look for the offs
            if (map_scans[scan][0]).upper()=='OFF':
                # if there is no ref1 or this is another ref1
                if not ref1 or (ref1 and bool(mapscans)==False):
                    ref1 = scan
                    samplermap = map_scans[scan][1]
                else:
                    ref2 = scan
                    prev_ref2 = ref2
    
            elif (map_scans[scan][0]).upper()=='MAP':
                if not ref1 and prev_ref2:
                    ref1 = prev_ref2
            
                mapscans.append(scan)
    
            # see if this scan is the last one in the relevant scan list
            # or see if we have a ref2
            # if so, close out
            if ref2 or idx==len(mapkeys)-1:
                maps.append((ref1,mapscans,ref2,samplermap,'PS'))
                ref1 = False
                ref2 = False
                mapscans = []
                
        if debug:
            import pprint
            pprint.pprint(maps)
    
            for idx,mm in enumerate(maps):
                print "Map",idx
                if mm[2]:
                    print "\tReference scans.....",mm[0],mm[2]
                else:
                    print "\tReference scan......",mm[0]
                print "\tMap scans...........",mm[1]
                print "\tMap type...........",mm[4]
    
        return maps
    
    def parseSdfitsIndex(self, infile):
        
        class ObservationRows:
            def __init__(self):
                self.rows = OrderedDict()
            def addRow(self, scan, feed, window, polarization,
                               fitsExtension, rowOfFitsFile, typeOfScan):
                key = (scan,feed,window,polarization)
                if key in self.rows:
                    self.rows[key]['ROW'].append(rowOfFitsFile)
                else:
                    self.rows[key] = {'EXTENSION': fitsExtension,
                                      'ROW': [rowOfFitsFile],
                                      'TYPE': typeOfScan }
            def get(self,scan,feed,window,polarization):
                key = (scan,feed,window,polarization)
                return self.rows[key]

        try:
            ifile = open(infile)
        except IOError:
            print "ERROR: Could not open file.  Please check and try again."
            raise
        
        print 'Input index file is', infile
    
        while True:
            line = ifile.readline()
            # look for start of row data or EOF (i.e. not line)
            if '[rows]' in line or not line:
                break
    
        reader = csv.DictReader(ifile,delimiter=' ',skipinitialspace=True)
        
        observation = ObservationRows()
        
        for row in reader:
    
            scanid = int(row['SCAN'])
            feed = int(row['FDNUM'])
            windowNum = int(row['IFNUM'])
            pol = int(row['PLNUM'])
            fitsExtension = int(row['EXT'])
            rowOfFitsFile = int(row['ROW'])
            typeOfScan = ''
            
            # we can assume all integrations of a single scan are within the same
            #   FITS extension
            observation.addRow(scanid, feed, windowNum, pol,
                                       fitsExtension, rowOfFitsFile, typeOfScan)
            
        try:
            ifile.close()
        except NameError:
            raise
        
        return observation

    def getReferenceIntegration(self, calON, calOFF):
        
        cal = Calibration()
        
        cref = cal.Cref(calON.field('DATA'), calOFF.field('DATA'))
        ccal = cal.Ccal(calON.field('DATA'), calOFF.field('DATA'))
        tcal = calOFF.field('TCAL')
        tref = cal.Tref( cref, ccal, tcal )

        dateobs = calOFF.field('DATE-OBS')
        timestamp = self.pu.dateToMjd(dateobs)
        
        #----------------
        # IDL Tsys computation
        # middle 80%
        #number_of_data_channels = len(tref)
        #lo = int(.1*number_of_data_channels)
        #hi = int(.9*number_of_data_channels)
        #idl_tsys =  tcal * (calOFF.field('DATA')[lo:hi]).mean() / (calON.field('DATA')[lo:hi]-calOFF.field('DATA')[lo:hi]).mean() + tcal/2.
        #print idl_tsys
        #idl_tsys =  tcal * calOFF.field('DATA') / (calON.field('DATA')-calOFF.field('DATA')) + tcal/2.
        #----------------
    
        exposure = calON.field('EXPOSURE') + calOFF.field('EXPOSURE')
        
        return cref,tref,exposure,timestamp
   