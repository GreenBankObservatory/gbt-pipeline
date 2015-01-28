import os

if __name__ == '__main__':
    print "WARNING:   dbcon.py is being renamed to load.py"
    print "           Beginning with the next release, only "
    print "           the new name will be available."
    newfile = os.path.dirname(os.path.realpath(__file__)) + '/../load.py'
    print "Invoking:  " + os.path.normpath(newfile)
    execfile(newfile)
    
