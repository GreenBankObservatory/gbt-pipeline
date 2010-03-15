#!/bin/bash

time kfpa_pipeline --infile=/home/sandboxes/jmasters/data/AGBT08B_040_03.raw.acs.fits \
                   --begin-scan=16 \
                   --end-scan=49 \
                   --vsource-center=5.8 \
                   --vsource-width=2.0 \
                   --vsource-begin=-.2 \
                   --vsource-end=11.8 \
                   --refscan1=15 \
                   --refscan2=51 \
                   --all-scans-as-ref \
                   --verbose=3 \
                   --nodisplay
