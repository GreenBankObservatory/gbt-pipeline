# Copyright (C) 2007 Associated Universities, Inc. Washington DC, USA.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Correspondence concerning GBT software should be addressed as follows:
#       GBT Operations
#       National Radio Astronomy Observatory
#       P. O. Box 2
#       Green Bank, WV 24944-0002 USA

# $Id$

import logging
import sys
import time

import blessings


class Logging:
    """Class for screen and text file logging of pipeline operation.

    """

    def __init__(self, opt, prefix, toconsole=True):

        self.t = blessings.Terminal()
        self.logger = None

        logfilename = prefix + '_' + self.timestamp() + '.log'
        self.configure_logfile(opt, logfilename, toconsole)

    def timestamp(self):
        """Return a string with the current date and time

        The format of the string is: dd.mm.yyyy_hh:mm:ss

        """

        lt = time.localtime(time.time())
        return "%02d.%02d.%04d_%02d:%02d:%02d" % (lt[2], lt[1], lt[0], lt[3], lt[4], lt[5])

    def doMessage(self, level, *args):
        """Write a message to the log file

        Keyword arguments:
        logger -- the log handler object
        level -- the level of the message (ERR, WARN, INFO, etc.)
        args -- the message text; this is a variable lengh list

        """
        message = ' '.join(map(str, (args)))
        if 'CRIT' == level:
            self.logger.error('{t.bold}{t.red}CRITICAL:{t.normal} {m}'.format(m=message, t=self.t))
            sys.stdout.flush()
        elif 'ERR' == level:
            self.logger.error('{t.bold}{t.red}ERROR:{t.normal} {m}'.format(m=message, t=self.t))
            sys.stdout.flush()
        elif 'WARN' == level:
            self.logger.error('{t.bold}{t.yellow}WARNING:{t.normal} {m}'.format(m=message, t=self.t))
            sys.stdout.flush()
        elif 'INFO' == level:
            self.logger.info(message)
        elif 'DBG' == level:
            self.logger.debug('{t.bold}{t.blue}DEBUG:{t.normal} {m}'.format(m=message, t=self.t))
            sys.stdout.flush()
        else:
            print 'ERROR: please check logging level.', level
        sys.stdout.flush()
        sys.stderr.flush()

    def configure_logfile(self, opt, logfilename, toconsole=True):
        """Configure the format and levels for the logfile

        Keyword arguments:
        opt -- user-defined verbosity options
        logfilename -- name of desired log file
        toconsole -- optional console output

        """
        LEVELS = {5: logging.DEBUG,     # errors + warnings + summary + debug
                  4: logging.INFO,      # errors + warnings + summary
                  3: logging.WARNING,   # errors + warnings
                  2: logging.ERROR,     # errors only
                  1: logging.CRITICAL,  # unused
                  0: logging.CRITICAL}  # no output

        level = LEVELS.get(opt.verbose, logging.DEBUG)

        loggername = logfilename.split('.')[0]

        self.logger = logging.getLogger(loggername)

        # logging level defaults to WARN, so we need to override it
        self.logger.setLevel(logging.DEBUG)

        # create file handler which logs even debug messages
        fh = logging.FileHandler(filename='log/'+logfilename, mode='w')
        fh.setLevel(logging.DEBUG)
        fh_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(fh_formatter)
        self.logger.addHandler(fh)

        if toconsole:
            # create console handler with a higher log level
            ch = logging.StreamHandler()
            ch.setLevel(level)
            # create formatter and add it to the handlers
            ch_formatter = logging.Formatter("%(message)s")
            ch.setFormatter(ch_formatter)
            # add the handlers to logger
            self.logger.addHandler(ch)
