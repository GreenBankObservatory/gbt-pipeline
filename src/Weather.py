import os
import glob
from Calibration import Calibration

class Weather:

    def __init__(self):
        
        self.cal = Calibration()
        self.last_integration_mjd_timestamp = None
        self.last_requested_freqHz = None
        self.last_zenith_opacity = None
        
    def retrieve_opacity_coefficients(self, opacity_coefficients_filename):
        """Return opacities (taus) derived from a list of coeffients
        
        These coefficients are produced from Ron Madalenna's getForecastValues script
        
        Keywords:
        infilename -- input file name needed for project name
        mjd -- date for data
        freq -- list of frequencies for which we seek an opacity
        
        Returns:
        a list of opacity coefficients for the time range of the dataset
        
        """
        FILE = open(opacity_coefficients_filename,'r')
    
        coeffs = []
        if FILE:
            for line in FILE:
                # find the most recent forecast and parse out the coefficients for 
                # each band
                # coeffs[0] is the mjd timestamp
                # coeffs[1] are the coefficients for 2-22 GHz
                # coeffs[2] are the coefficients for 22-50 GHz
                # coeffs[3] are the coefficients for 70-116 GHz
                coeffs.append((float(line.split('{{')[0]),\
                    [float(xx) for xx in line.split('{{')[1].split('}')[0].split(' ')],\
                    [float(xx) for xx in line.split('{{')[2].split('}')[0].split(' ')],\
                    [float(xx) for xx in line.split('{{')[3].split('}')[0].split(' ')]))
                   
        else:
            print "WARNING: Could not read coefficients for Tau in",opacity_coefficients_filename
            return False
    
        return coeffs

    def retrieve_zenith_opacity(self, integration_mjd_timestamp, freqHz):

        freqGHz = freqHz/1e9
        
        # if less than 2 GHz, opacity coefficients are not available
        if freqGHz < 2:
            return None

        # if the frequency is the same as the last requested and
        #  this time is within the same record (1 hr window) of the last
        #  recorded opacity coefficients, then just reuse the last
        #  zenith opacity value requested

        if self.last_requested_freqHz != None and self.last_requested_freqHz == freqHz and \
                integration_mjd_timestamp >= self.last_integration_mjd_timestamp and \
                integration_mjd_timestamp < self.last_integration_mjd_timestamp + .04167:
            
                return self.last_zenith_opacity
        
        self.last_integration_mjd_timestamp = integration_mjd_timestamp
        self.last_requested_freqHz = freqHz
                
        # retrieve a list of opacity coefficients files, based on a given directory
        # and filename structure
        opacity_coefficients_filename = False
        opacity_files = glob.glob(\
          '/users/rmaddale/Weather/ArchiveCoeffs/CoeffsOpacityFreqList_avrg_*.txt')
        self.number_of_opacity_files = len(opacity_files)
        
        if 0==self.number_of_opacity_files:
            #doMessage(logger,msg.WARN,'WARNING: No opacity coefficients file')
            print 'WARNING: No opacity coefficients file'
            return False
            
        # sort the list of files so they are in chronological order
        opacity_files.sort()
        
        # the following will become True if integration_mjd_timestamp is older than available ranges
        # provided in the opacity coefficients files
        tooearly = False
        # check the date of each opacity coefficients file
        for idx,opacity_candidate_file in enumerate(opacity_files):
            dates = opacity_candidate_file.split('_')[-2:]
            opacity_file_timestamp = []
            for date in dates:
                opacity_file_timestamp.append(int(date.split('.')[0]))
            opacity_file_starttime = opacity_file_timestamp[0]
            opacity_file_stoptime = opacity_file_timestamp[1]
        
            # set tooearly=True when integration_mjd_timestamp is older than available ranges
            if idx == 0 and integration_mjd_timestamp < opacity_file_starttime:
                tooearly = True
                break
        
            if integration_mjd_timestamp >= opacity_file_starttime and integration_mjd_timestamp < opacity_file_stoptime:
                opacity_coefficients_filename = opacity_candidate_file
                break
        
        if not opacity_coefficients_filename:
            if tooearly:
                #doMessage(logger,msg.ERR,'ERROR: Date is too early for opacities.')
                #doMessage(logger,msg.ERR,'  Try setting zenith tau at command line.')
                sys.exit(9)
            else:
                # if the mjd in the index file comes after the date string in all of the
                # opacity coefficients files, then we can assume the current opacity
                # coefficients file will apply.  a date string is only added to the opacity
                # coefficients file when it is no longer the most current.
                opacity_coefficients_filename = \
                  '/users/rmaddale/Weather/ArchiveCoeffs/CoeffsOpacityFreqList_avrg.txt'
        
        # opacities coefficients filename
        if opacity_coefficients_filename and os.path.exists(opacity_coefficients_filename):
            #doMessage(logger,msg.DBG,'Using coefficients from', opacity_coefficients_filename)
            self.opacity_coeffs = self.retrieve_opacity_coefficients(opacity_coefficients_filename)
        else:
            #doMessage(logger,msg.WARN,'WARNING: No opacity coefficients file')
            print 'WARNING: No opacity coefficients file'
            return False

        for coeffs_line in self.opacity_coeffs:
            if integration_mjd_timestamp > coeffs_line[0]:
                if (freqGHz >= 2 and freqGHz <= 22):
                    coeffs = coeffs_line[1]
                elif (freqGHz > 22 and freqGHz <= 50):
                    coeffs = coeffs_line[2]
                elif (freqGHz > 50 and freqGHz <= 116):
                    coeffs = coeffs_line[3]

        zenith_opacity = self.cal.zenith_opacity(coeffs, freqGHz)
        self.last_zenith_opacity = zenith_opacity
        
        return zenith_opacity