gbt_pipeline
============

The gbt_pipeline script is the primary driver of the pipeline.  It is called
after the user environment options are set by `gbtpipline`.

Amongst other things, gbt_pipeline does the following:

* reads and interprets and logs the command line options, in part by using commandline.py
* creates a pipeline for either:
   #. each map in the input file when the `--allmaps` option is set, or
   #. for a single map when the beginning, end and reference scans are supplied and `--allmaps` is not set
