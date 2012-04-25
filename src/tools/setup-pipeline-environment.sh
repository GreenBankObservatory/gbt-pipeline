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
echo 'downloading python-2.6.6'
curl -O http://www.python.org/ftp/python/2.6.6/Python-2.6.6.tgz
echo 'downloading numpy-1.4.1'
curl -O http://pypi.python.org/packages/source/n/numpy/numpy-1.4.1.tar.gz
echo 'downloading parseltongue-2.0'
curl -O http://www.jive.nl/parseltongue/releases/parseltongue.tar.gz
echo 'downloading pyfits-2.2.2'
svn checkout http://svn6.assembla.com/svn/pyfits/tags/pyfits_2_2_2
echo 'downloading Obit Revision 413'
svn checkout -r 413 https://svn.cv.nrao.edu/svn/ObitInstall

# alternatively...
#curl -O http://www.jive.nl/parseltongue/releases/Obit-22JUN10a.tar.gz

# ------------------------------------------------------------- build python
echo 'building python'
cd ${SCRATCH_DIR}
tar xvzf Python-2.6.6.tgz
cd Python-2.6.6
./configure --prefix=${INSTALL_DIR}
make install

# ------------------------------------------------------------ build numpy
echo 'building numpy'
cd ${SCRATCH_DIR}
tar xvzf numpy-1.4.1.tar.gz
cd numpy-1.4.1
ATLAS=None BLAS=None LAPACK=None ${INSTALL_DIR}/bin/python setup.py install

# ------------------------------------------------------------ build pyfits
echo 'building pyfits'
cd ${SCRATCH_DIR}/pyfits_2_2_2
${INSTALL_DIR}/bin/python setup.py install

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


exit


# -------------------------------------------------- other useful stuff
#
#cd ${SCRATCH_DIR}
#curl -O http://pypi.python.org/packages/2.6/s/setuptools/setuptools-0.6c11-py2.6.egg
#
#PATH=${INSTALL_DIR}/bin:${PATH} sh setuptools-0.6c11-py2.6.egg --prefix=${INSTALL_DIR}
#${INSTALL_DIR}/bin/easy_install pip
#${INSTALL_DIR}/bin/pip install matplotlib
#
## edit matplotlib source to get it to work
#sed s/numpy.ma/numpy.core.ma/ ${INSTALL_DIR}/lib/python2.6/site-packages/matplotlib/numerix/npyma/__init__.py >tempfile
#mv tempfile ${INSTALL_DIR}/lib/python2.6/site-packages/matplotlib/numerix/npyma/__init__.py
#sed s/numpy.ma/numpy.core.ma/ ${INSTALL_DIR}/lib/python2.6/site-packages/matplotlib/numerix/ma/__init__.py >tempfile
#mv tempfile ${INSTALL_DIR}/lib/python2.6/site-packages/matplotlib/numerix/ma/__init__.py
#
#${INSTALL_DIR}/bin/pip install ipython
#
## --------------------------------------------- remove scratch build area
#
#rm -rf ${SCRATCH_DIR}
