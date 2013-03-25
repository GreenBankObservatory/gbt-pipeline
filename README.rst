============
GBT Pipeline
============

This directory contains code and documentation for the 
Green Bank Telescope(GBT) data analysis pipelines.

The mapping pipeline supports both *position-switched* and *frequency-switched* 
observations.

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

*Last modified*:  21 March 2013
