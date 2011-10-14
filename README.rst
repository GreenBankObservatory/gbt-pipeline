============
GBT Pipeline
============

This directory contains code and documentation for the 
Green Bank Telescope(GBT) data analysis pipeline.

The pipeline supports both *position-switched* and *frequency-switched* mapping 
observations.

---------------
Project website
---------------

https://safe.nrao.edu/wiki/bin/view/Kbandfpa/WebHome

All pipeline code is written in Python.

Pipeline dependencies include getForecastValues, idlToSdfits,
Obit, parseltongue and AIPS.

SDFITS files are the required pipeline input.

Due to the  interaction with weather prediction scripts only available in 
Green Bank, the code can only be effectively run on a Green Bank network 
computer.

jmasters@nrao.edu

*Last modified*:  14 October 2011
