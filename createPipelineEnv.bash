#!/bin/bash

virtualenv --python=/home/gbt7/newt/bin/python ./pipelineEnv
source pipelineEnv/bin/activate                                                                                       
pip install -U pip                                                                                               
pip install -U setuptools                                                                                        
pip install numpy==1.6.2                                                                                         
pip install -r reqs.txt
pip install noseXUnit
#source /opt/rh/devtoolset-4/enable
python src/gbt_pipeline.py -i /home/gbtpipeline/reference-data/TKFPA_29/TKFPA_29.raw.acs.fits
#nosetests --with-xunit test/gbtpipeline_unit_tests.py
