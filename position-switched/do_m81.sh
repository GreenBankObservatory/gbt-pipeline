#!/bin/bash

time /home/sandboxes/kfpa_pipeline/kfpa_pipeline \
     --infile=AGBT03B_034_01.raw.acs.fits \
     --begin-scan=61 \
     --end-scan=91 \
     --verbose=3
