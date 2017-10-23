#!/usr/bin/python

import os
import tarfile
import shutil

VIRTUALENV_VER = '13.1.2'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def normalize(path):
    r"""Expand '~' if it's in the path and make the path name relative.

    Args:
        path(str): An un-normalized path string.

    Returns:
        str:
        A normalized path string.

    """
    # first normalize the directory string

    # if there is a '~', expand it
    path = os.path.expanduser(path)

    # get a relative path string
    path = os.path.relpath(path)

    return path


def location_ok(dirname):
    r"""Check if the user supplied path is OK for installation.

    Args:
        dirname(str): The path given by the user.

    Returns:
        bool:
        The result of the path check. True or False.

    """

    # check if it exists already
    if os.path.exists(dirname):
        print("'{pname}' exists.  Are you sure you want to install here? (Y/N) ".format(pname=dirname))
        yn = raw_input()

        # user decides path is not OK
        if 'n' == yn.lower():

            print("Please remove {pname} or choose another install location.".format(pname=dirname))
            return False

        # user decides path is OK
        elif 'y' == yn.lower():

            # if this is not a directory, try again
            if not os.path.isdir(dirname):
                print("'{pname}' is not a directory. Please try again".format(pname=dirname))
                return False

            else:
                print("OK. Installing in '{pname}'.".format(pname=dirname))
                return True

        else:
            # user didn't choose Y or N. Try again.
            return location_ok(dirname)

    else:
        # path does not exist
        if dirname.startswith('/'):
            parentdir = os.path.dirname(dirname)
            if os.path.exists(parentdir):
                return True
            else:
                print("Parent directory '{pname}' does not exist.  Please try again.".format(pname=parentdir))
                return False
        else:
            fullpathparent = os.path.dirname(os.getcwd() + '/' + dirname)
            if os.path.exists(fullpathparent):
                return True
            else:
                print("Parent directory '{pname}' does not exist.  Please try again.".format(pname=fullpathparent))
                return False


def make_venv(dirpath):

    if os.path.exists(dirpath):
        os.chdir(dirpath)
    else:
        os.mkdir(dirpath)
        os.chdir(dirpath)

    # see if the 'virtualenv' command exists
    print("   Downloading and running virtualenv.py in {path}.".format(path=dirpath))

    os.system('curl -O https://pypi.python.org/packages/source'
              '/v/virtualenv/virtualenv-{ver}.tar.gz'.format(ver=VIRTUALENV_VER))

    tar = tarfile.open('virtualenv-{ver}.tar.gz'.format(ver=VIRTUALENV_VER))
    tar.extractall()
    tar.close()
    #os.system('/usr/bin/python virtualenv-{ver}/virtualenv.py pipeline_env'.format(ver=VIRTUALENV_VER))
    os.system('/usr/bin/python virtualenv-{ver}/virtualenv.py -p /home/gbt7/newt/bin/python pipeline_env'.format(ver=VIRTUALENV_VER))

    print("Created {parent}/pipeline_env environment.".format(parent=dirpath))

    # cleanup
    os.unlink('virtualenv-{ver}.tar.gz'.format(ver=VIRTUALENV_VER))
    shutil.rmtree('virtualenv-{ver}'.format(ver=VIRTUALENV_VER))

    # doing execfile() on this file will alter the current interpreter's
    # environment so you can import libraries in the virtualenv
    activate_this_file = "pipeline_env/bin/activate_this.py"
    execfile(activate_this_file, dict(__file__=activate_this_file))

    print "Activated virtual environment."


def install_numpy():
    #os.system("pip install numpy")
    os.system("pip install --no-index --find-links python_archive numpy -v")


def install_others():

    os.system("pip install -r {rdir}/requirements.txt".format(rdir=SCRIPT_DIR))

if __name__ == "__main__":

    installdir = ''
    while True:
        # Prompt the user for an install location
        installdir = raw_input("Please specify an install directory for the gbtpipeline [.]: ")
        # default to current working directory
        if installdir.strip() == '':
            installdir = '.'
        installdir = normalize(installdir)
        if location_ok(installdir):
            break

    make_venv(installdir)
    install_numpy()
    install_others()
