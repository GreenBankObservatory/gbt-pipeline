#!/bin/bash

DATE=`date +"%s"`

# ------------------------------------- create scratch and install directories

SCRATCH_DIR=/home/scratch/${USER}/pipeline-install-${DATE}
mkdir -p ${SCRATCH_DIR}
echo created ${SCRATCH_DIR}

INSTALL_DIR=/home/gbt7/pipeline

mkdir -p ${INSTALL_DIR}
echo created ${INSTALL_DIR}

# ---------------------------- set version numbers
PYVER=2.7.3
NUMPYVER=1.6.2
FITSIOVER=0.9.0
OBITVER=413

# ---------------------------- cd into scratch area and download dependencies

cd ${SCRATCH_DIR}
echo 'downloading python'
curl -O http://www.python.org/ftp/python/${PYVER}/Python-${PYVER}.tgz
echo 'downloading virtualenv'
curl -O https://raw.github.com/pypa/virtualenv/master/virtualenv.py
echo 'downloading parseltongue'
curl -O http://www.jive.nl/parseltongue/releases/parseltongue.tar.gz
echo 'downloading Obit'
svn checkout -r ${OBITVER} https://svn.cv.nrao.edu/svn/ObitInstall

# alternatively...
#curl -O http://www.jive.nl/parseltongue/releases/Obit-22JUN10a.tar.gz

# ------------------------------------------------------------- build python
echo 'building python'
cd ${SCRATCH_DIR}
tar xvzf Python-${PYVER}.tgz
cd Python-${PYVER}
./configure --prefix=${INSTALL_DIR}
make install

# ------------------------------------------------------------ create virtual env
echo 'making virtual env'
cd ${SCRATCH_DIR}
${INSTALL_DIR}/bin/python ./virtualenv.py ${INSTALL_DIR}/pipeline-env
source ${INSTALL_DIR}/pipeline-env/bin/activate

# ------------------------------------------------------------ install numpy
echo 'installing numpy'
pip install numpy==${NUMPYVER}

# ------------------------------------------------------------ install fitsio
echo 'installing fitsio'
pip install fitsio

# ------------------------------------------------------------ install blessings
echo 'installing blessings'
pip install blessings

# ------------------------------------------------------------ install pyfits
echo 'installing pyfits'
pip install pyfits

# ------------------------------------------------------------ install ipython
echo 'installing ipython'
pip install ipython

# ------------------------------------------------------------ install matplotlib
echo 'installing matplotlib'
pip install matplotlib

# ---------------------------------------------------------- build Obit
echo 'building Obit'
cd ${SCRATCH_DIR}/ObitInstall
PATH=${INSTALL_DIR}/bin:${PATH} InstallObit.sh -without ZLIB PYTHON MOTIF GLIB

# ---------------------------------------------------------- build ParselTongue
echo 'building ParselTongue'
cd ${SCRATCH_DIR}
tar xvzf parseltongue.tar.gz 
cd parseltongue-2.0
mv ./configure ./configure.sav
echo 'updating ParselTongue configure script'
sed 's/Obit.py/Obit.so/g' ./configure.sav > ./configure
chmod u+x ./configure

PATH=${INSTALL_DIR}/bin:${PATH} ./configure --with-obit=${SCRATCH_DIR}/ObitInstall/ObitSystem/Obit --prefix=${INSTALL_DIR}

make
make install

deactivate

exit

# -------------------------------------------------- other useful stuff
#
## edit matplotlib source to get it to work
#sed s/numpy.ma/numpy.core.ma/ ${INSTALL_DIR}/lib/python2.6/site-packages/matplotlib/numerix/npyma/__init__.py >tempfile
#mv tempfile ${INSTALL_DIR}/lib/python2.6/site-packages/matplotlib/numerix/npyma/__init__.py
#sed s/numpy.ma/numpy.core.ma/ ${INSTALL_DIR}/lib/python2.6/site-packages/matplotlib/numerix/ma/__init__.py >tempfile
#mv tempfile ${INSTALL_DIR}/lib/python2.6/site-packages/matplotlib/numerix/ma/__init__.py
#
## --------------------------------------------- remove scratch build area
#
#rm -rf ${SCRATCH_DIR}
