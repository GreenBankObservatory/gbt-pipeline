============
GBT Pipeline
============

This directory contains code and documentation for the Green Bank
Telescope(GBT) data analysis pipelines.


The GBT Pipeline Project has two main goals.

The first is to generate a quick-look data reduction pipeline for GBT
spectroscopy data that is capable of processing at least 80% of all
sessions observed with the GBT in "Standard Observing Modes".

The quick-look pipeline will operate with minimal user intervention.
Starting with the name of a GBT project directory, the pipeline will
run the sdfits filler, determine the observing mode used for
spectroscopic data, calibrate and average data for each target in the
session, fit a spectral baseline, and write the reduced data into an
sdfits file.  Where appropriate, the pipeline will attempt to identify
and flag RFI.  The pipeline will have some heuristics to help it fit
the spectral baselines.  In cases where complex baselines or extensive
RFI are major issues, the observer will always do better to process
the data by hand.  The pipeline will generate a set of statistics and
in some cases it will provide nominal scientific parameters (for
example, fitting extragalactic HI profiles).  The pipeline will
generate a "summary sheet" for each target observed in the session.
The purpose of the quick-look pipeline is to provide the community
with easy access to GBT data, including data from projects that they
were not involved with.  The product of this pipeline (i.e. reduced
spectra) will be provided to the astronomical community through the
NRAO Image Archive.

The second main goal of the GBT Pipeline Project is to provide a set
of data processing tools to help observers produce publication-quality
data products.  These tools will allow observers to tweak parameters
in their data reduction steps with a straightforward interface.  Users
should expect to engage in an iterative process, working with the data
and examining the results of their processing several times before
achieving the best result.  These tools will assist users in making
maps from their spectral line mapping observations.  They will also be
applicable for point-source spectroscopy, allowing users to specify
calibration parameters and other relevant parameters to achieve their
best product.  That product might be either a data cube representing a
map, or a spectrum for a single position on the sky.  The KFPA
pipeline, the initial product of the GBT Pipeline Project, is an
example of a tool in this category.

---------------
Project website
---------------

https://safe.nrao.edu/wiki/bin/view/GB/Gbtpipeline/WebHome

Mapping pipeline code is written in Python.  Dependencies include
getForecastValues, idlToSdfits, Obit, parseltongue and AIPS.

SDFITS files are the required input.

Due to the  interaction with weather prediction scripts only available in 
Green Bank, the code can only be effectively run on a Green Bank network 
computer.

The spectral pipeline code is written in GBTIDL.

jmasters@nrao.edu

*Last modified*:  22 June 2013
