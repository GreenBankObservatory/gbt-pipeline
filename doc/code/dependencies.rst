External Dependencies
=====================

FITS access (pyfits)
--------------------

PyFITS provides an interface to FITS formatted files under the Python scripting language and PyRAF, the Python-based interface to IRAF. It is useful both for interactive data analysis and for writing analysis scripts in Python using FITS files as either input or output. PyFITS is a development project of the Science Software Branch at the Space Telescope Science Institute.

Numerical Python (numpy)
------------------------

NumPy is the fundamental package needed for scientific computing with Python. It contains among other things:

    * a powerful N-dimensional array object
    * sophisticated (broadcasting) functions
    * tools for integrating C/C++ and Fortran code
    * useful linear algebra, Fourier transform, and random number capabilities.

Besides its obvious scientific uses, NumPy can also be used as an efficient multi-dimensional container of generic data. Arbitrary data-types can be defined. This allows NumPy to seamlessly and speedily integrate with a wide variety of databases.

Numpy is licensed under the BSD license, enabling reuse with few restrictions.

Scientific Python (scipy)
-------------------------

SciPy is open-source software for mathematics, science, and engineering. It is also the name of a very popular conference on scientific programming with Python. The SciPy library depends on NumPy, which provides convenient and fast N-dimensional array manipulation. The SciPy library is built to work with NumPy arrays, and provides many user-friendly and efficient numerical routines such as routines for numerical integration and optimization.

The pipeline makes minimal use of scipy for smoothing and interpolation.

GBT Weather Forecasting (from Ron Maddalena)
--------------------------------------------
http://www.gb.nrao.edu/~rmaddale/Weather/index.html

AIPS (idlToSdfits + Parseltongue + Obit)
----------------------------------------

The Astronomical Image Processing System is a software package for calibration, data analysis, image display, plotting, and a variety of ancillary tasks on Astronomical Data. It comes from the National Radio Astronomy Observatory.

A local GBT utililty, idlToSdfits (written by Glen Langston) is used to convert from NRAO SDFITS format to AIPS SDFITS format.

Obit is a group of software packages for handling radio astronomy data, especially interferometric and single dish OTF imaging.

ParselTongue is a Python interface to classic AIPS, Obit and possibly other task-based data reduction packages.

In the GBT pipeline, the combination of these packages is used for gridding, imaging and (sometimes) baseline removal.
