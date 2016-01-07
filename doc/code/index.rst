.. gbtpipeline documentation master file, created by
   sphinx-quickstart on Tue Jan  5 13:34:25 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

GBT Pipeline documentation
==========================

The Green Bank Telescope pipeline (gbtpipeline) was originally built for the calibration and mapping of K-band Focal Plane Array (KFPA) observations.  However, it's design is general enough to accommodate the processing of other bands and receivers.  In addition to K-band data, L-band data has also been successfully processed with the pipeline.

At a high level, the pipeline makes some assumptions about the mapping technique and format of the input data.

Position-switched maps are assumed to have no more than two associated reference scans.  At most, a mapping block will have a reference scan before and after a set of mapping scans.  The input must be either a single SDFITS file, or a directory of SDFITS files from a single observation, containing all of the scans necessary to calibrate and map.  There must also be an associated index file.  Both the sdfits and index inputs are produced by the ``sdfits`` filler program.  Frequency-switched calibration is also supported.

In frequency-switched maps, scan numbers must be given explicitly.

The pipeline is written in Python and is divided into several modules.  There are several external decencies.

Contents:

.. toctree::
   :maxdepth: 2

   pipeline
   dependencies
   installation

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

