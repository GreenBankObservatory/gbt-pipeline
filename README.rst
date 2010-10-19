============
GBT Pipeline
============

This directory contains *position-switched* code and documentation for the 
Green Bank Telescope K-band Focal Plane Array (KFPA) data analysis and 
reduction pipeline.

In the future, the pipeline will support *frequency-switched* mapping 
observations as well.

In addition, the code can sometime be run on mapping data from other 
receivers.

The code is authored by Glen Langston, Bob Garwood and Joe Masters at the
National Radio Astronomy Observatory (NRAO).

* Glen Langston -- glangsto@nrao.edu
* Bob Garwood   -- bgarwood@nrao.edu
* Joe Masters   -- jmasters@nrao.edu

---------------
Project website
---------------

https://safe.nrao.edu/wiki/bin/view/Kbandfpa/WebHome

Code is written in Python, except for getForecastValues (tcl) and
idlToSdfits (C).  The highest level script is gbtpipeline.

SDFITS files are the required pipeline input.

Due to the  interaction with weather prediction scripts
only available in Green Bank, the code can only be effectively run on a
Green Bank network computer.

*Last modified*:  19 October 2010
