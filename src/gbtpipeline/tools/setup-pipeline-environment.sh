#!/bin/bash

#
# this installation script assumes a Green Bank installation of RHEL6
# with a default python version 2.6 and a system level Obit.so library
#

DATE=`date +"%s"`

# ------------------------------------- create scratch and install directories
SCRATCH_DIR=/home/scratch/${USER}/pipeline-install-${DATE}
mkdir -p ${SCRATCH_DIR}
echo created ${SCRATCH_DIR}

INSTALL_DIR=/home/gbt7/pipeline

mkdir -p ${INSTALL_DIR}
echo created ${INSTALL_DIR}

# ---------------------------- cd into scratch area and download dependencies

cd ${SCRATCH_DIR}
echo 'downloading virtualenv'
curl -O https://raw.github.com/jmasters/gbt-pipeline/master/src/dependencies/virtualenv.py

# ------------------------------------------------------------ create virtual env
echo 'making virtual calibration env'
cd ${SCRATCH_DIR}
VIRTENV=pipeline-env
rm -rf ${INSTALL_DIR}/${VIRTENV}
python ./virtualenv.py ${INSTALL_DIR}/${VIRTENV}

# ------------------------------------------------------- activate virtual env
source ${INSTALL_DIR}/${VIRTENV}/bin/activate

# -----------------------------------------------------------------------------
#
#   CALIBRATION SETUP
#
# -----------------------------------------------------------------------------

# ------------------------------------------------------------ install numpy
echo 'installing numpy'
pip install numpy

# ------------------------------------------------------------ install fitsio
echo 'installing fitsio'
pip install fitsio

# ------------------------------------------------------------ install blessings
echo 'installing blessings'
pip install blessings

# ------------------------------------------------------------ install ordereddict
echo 'installing ordereddict'
pip install ordereddict

# ------------------------------------------------------------ install argparse
echo 'installing argparse'
pip install argparse

# -----------------------------------------------------------------------------
#
#   TESTING SETUP
#
# -----------------------------------------------------------------------------

# ------------------------------------------------------------ install nose
echo 'installing nose'
pip install nose

# ------------------------------------------------------------ install matplotlib
echo 'installing matplotlib'
pip install matplotlib

# ------------------------------------------------------------ install ipython
echo 'installing ipython'
pip install ipython

# -----------------------------------------------------------------------------
#
#   USER TOOL SETUP
#
# -----------------------------------------------------------------------------

# ------------------------------------------------------------ install pyfits
echo 'installing pyfits'
pip install pyfits

deactivate

# -----------------------------------------------------------------------------
#
#   IMAGING SETUP
#
# -----------------------------------------------------------------------------

# ---------------------------- cd into scratch area and download dependencies

cd ${SCRATCH_DIR}
OBIT_VERSION=413
echo 'downloading obit'
svn checkout -r ${OBIT_VERSION} https://svn.cv.nrao.edu/svn/ObitInstall

cd ${SCRATCH_DIR}
echo 'downloading parseltongue'
curl -O https://raw.github.com/jmasters/gbt-pipeline/master/src/dependencies/parseltongue.tar.gz

# ------------------------------------------------------------ create virtual env
echo 'making virtual imaging env'
cd ${SCRATCH_DIR}
VIRTENV=imaging-env
rm -rf ${INSTALL_DIR}/${VIRTENV}
python ./virtualenv.py ${INSTALL_DIR}/${VIRTENV}

# ------------------------------------------------------- activate virtual env
source ${INSTALL_DIR}/${VIRTENV}/bin/activate

# ------------------------------------------------------------ install numpy
echo 'installing numpy'
pip install numpy

# ------------------------------------------------------------ install pyfits
echo 'installing pyfits'
pip install pyfits

# ---------------------------------------------------------- build Obit
echo 'building Obit'
cd ${SCRATCH_DIR}/ObitInstall
./InstallObit.sh -without ZLIB PYTHON MOTIF GLIB PLPLOT CFITSIO FFTW GSL ZLIB MOTIF WWW CURL XMLRPC Boost WVR THIRD ObitView ObitSD
# copy build to install area
cp -rf ${SCRATCH_DIR}/ObitInstall/ObitSystem ${INSTALL_DIR}/obit

# ---------------------------------------------------------- build ParselTongue

echo 'building ParselTongue'
cd ${SCRATCH_DIR}
tar xvzf parseltongue.tar.gz 
cd parseltongue-2.0
mv ./configure ./configure.sav
echo 'updating ParselTongue configure script'
sed 's/Obit.py/Obit.so/g' ./configure.sav > ./configure
chmod u+x ./configure

PYTHONPATH=${INSTALL_DIR}/obit/Obit/python/ LD_LIBRARY_PATH=/opt/local/lib:${INSTALL_DIR}/obit/Obit ./configure --prefix=${INSTALL_DIR}
make
make install

deactivate

exit
