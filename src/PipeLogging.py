class Logging:
    """Class for screen and text file logging of pipeline operation.

    """

    def timestamp(self):
        """Return a string with the current date and time
    
        The format of the string is: dd.mm.yyyy_hh:mm:ss
    
        """
        lt = time.localtime(time.time())
        return "%02d.%02d.%04d_%02d:%02d:%02d" % (lt[2], lt[1], lt[0], lt[3],
                                                  lt[4], lt[5])
        
      
    def doMessage(self,logger,level,*args):
        """Write a message to the log file
    
        Keyword arguments:
        logger -- the log handler object
        level -- the level of the message (ERR,WARN,INFO,etc.)
        args -- the message text; this is a variable lengh list
    
        """
        message = ' '.join(map(str,(args)))
        if msg.CRIT == level:
            logger.critical(message)
        elif msg.ERR == level:
            logger.error(message)
        elif msg.WARN == level:
            logger.warning(message)
        elif msg.INFO == level:
            logger.info(message)
        elif msg.DBG == level:
            logger.debug(message)
        else:
            logger.critical(message)
    
    def configure_logfile(self, opt,logfilename,toconsole=True):
        """Configure the format and levels for the logfile
    
        Keyword arguments:
        opt -- user-defined verbosity options
        logfilename -- name of desired log file
        toconsole -- optional console output
    
        """
        LEVELS = {5: logging.DEBUG, # errors + warnings + summary + debug
                  4: logging.INFO, # errors + warnings + summary
                  3: logging.WARNING, # errors + warnings
                  2: logging.ERROR, # errors only
                  1: logging.CRITICAL, # unused
                  0: logging.CRITICAL} # no output 
    
        level = LEVELS.get(opt.verbose, logging.DEBUG)
    
        loggername = logfilename.split('.')[0]
        logger = logging.getLogger(loggername)
        
        # logging level defaults to WARN, so we need to override it
        logger.setLevel(logging.DEBUG)
        
        # create file handler which logs even debug messages
        fh = logging.FileHandler(filename=logfilename,mode='w')
        fh.setLevel(logging.DEBUG)
        fh_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)
    
        if toconsole:
            # create console handler with a higher log level
            ch = logging.StreamHandler()
            ch.setLevel(level)
            # create formatter and add it to the handlers
            ch_formatter = logging.Formatter("%(message)s")
            ch.setFormatter(ch_formatter)
            # add the handlers to logger
            logger.addHandler(ch)
        
        return logger
    