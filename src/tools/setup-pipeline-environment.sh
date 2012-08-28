#!/bin/bash

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

# -----------------------------------------------------------------------------
#
#   CALIBRATION SETUP
#
# -----------------------------------------------------------------------------

PYVER=2.7.3

cd ${SCRATCH_DIR}
echo 'downloading python'
curl -O http://www.python.org/ftp/python/${PYVER}/Python-${PYVER}.tgz

# ------------------------------------------------------------- build python
echo 'building python'
cd ${SCRATCH_DIR}
tar xvzf Python-${PYVER}.tgz
cd Python-${PYVER}
./configure --prefix=${INSTALL_DIR}
make install

# ------------------------------------------------------------ create virtual env
echo 'making virtual calibration env'
cd ${SCRATCH_DIR}
rm -rf ${INSTALL_DIR}/calibration-env
${INSTALL_DIR}/bin/python${PYVER} ./virtualenv.py ${INSTALL_DIR}/calibration-env
source ${INSTALL_DIR}/calibration-env/bin/activate

# ------------------------------------------------------------ install numpy
echo 'installing numpy'
pip install numpy

# ------------------------------------------------------------ install fitsio
echo 'installing fitsio'
pip install fitsio

# ------------------------------------------------------------ install blessings
echo 'installing blessings'
pip install blessings

deactivate

# -----------------------------------------------------------------------------
#
#   IMAGING SETUP
#
# -----------------------------------------------------------------------------

PYVER=2.4
OBITVER=1.1.425-1-64b

cd ${SCRATCH_DIR}
echo 'downloading python'
curl -O http://www.python.org/ftp/python/${PYVER}/Python-${PYVER}.tgz

# ------------------------------------------------------------- build python
echo 'building python'
cd ${SCRATCH_DIR}
tar xvzf Python-${PYVER}.tgz
cd Python-${PYVER}
./configure --prefix=${INSTALL_DIR}
make install

# ------------------------------------------------------------ create virtual env
echo 'making virtual calibration env'
cd ${SCRATCH_DIR}
rm -rf ${INSTALL_DIR}/imaging-env
${INSTALL_DIR}/bin/python${PYVER} ./virtualenv.py ${INSTALL_DIR}/imaging-env
source ${INSTALL_DIR}/imaging-env/bin/activate

cd ${SCRATCH_DIR}
echo 'downloading obit'
curl -O https://svn.cv.nrao.edu/obit/linux_distro/obit-${OBITVER}.tar.gz
mv obit-${OBITVER}.tar.gz ${INSTALL_DIR}
cd  ${INSTALL_DIR}
tar xvzf obit-${OBITVER}.tar.gz

cd ${SCRATCH_DIR}
echo 'downloading parseltongue'
curl -O https://raw.github.com/jmasters/gbt-pipeline/master/src/dependencies/parseltongue.tar.gz
# ---------------------------------------------------------- build ParselTongue

echo 'building ParselTongue'
cd ${SCRATCH_DIR}
tar xvzf parseltongue.tar.gz 
cd parseltongue-2.0
mv ./configure ./configure.sav
echo 'updating ParselTongue configure script'
sed 's/Obit.py/Obit.so/g' ./configure.sav > ./configure
chmod u+x ./configure
PYTHONPATH=${INSTALL_DIR}/obit-${OBITVER}/lib64/obit/python/ LD_LIBRARY_PATH=${INSTALL_DIR}/obit-${OBITVER}/lib64 ./configure --prefix=${INSTALL_DIR}
make
make install

deactivate

# to run ParselTongue
#  PYTHONPATH=${INSTALL_DIR}/obit-${OBITVER}/lib64/obit/python/  LD_LIBRARY_PATH=${INSTALL_DIR}/obit-${OBITVER}/lib64  $INSTALL_DIR/bin/ParselTongue

exit
