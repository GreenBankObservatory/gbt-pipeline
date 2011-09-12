.. GBT Pipeline documentation master file, created by
   sphinx-quickstart on Mon Oct 18 14:22:35 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

GBT Pipeline Code Documentation
===============================

The Green Bank Telescope pipeline (gbtpipeline) was originally built for the calibration and mapping of K-band Focal Plane Array (KFPA) observations.  However, it's design is general enough to accomadate the processing of other bands and receivers.  In addition to K-band data, L-band data has also been successfully processed with the pipeline.

At a high level, the pipeline makes some assumptions about the mapping technique and format of the input data.

Position-switched maps are assumed to have no more than two associated reference scans.  At most, a mapping block will have a reference scan before and after a set of mapping scans.  The input must be a single SDFITS file containing all of the scans necessary to calibrate and map, and there must be an associated index file.  Both the sdfits and index inputs are produced by the sdfits filler program.  Frequency-switched calibration is also supported.

In order for the pipeline to automatically discover mapping blocks in a SDFITS file, the scans must be annotated with either "OFF" or "MAP", representing the reference and map scans respectively.  This feature is not yet supported in frequency-switched maps, so scan numbers must be given explicitly.

The pipeline is written in Python and is divided into several modules.  There are several external dependcies.

.. toctree::
   :maxdepth: 3

   pipeline
   dependencies
   installation

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

