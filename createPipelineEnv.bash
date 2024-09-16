#!/bin/bash

# Bail on errors
set -e

if [ -n "$1" ]; then
    venv_path="$1"
else
    venv_path="./${USER}_pipeline_env"
fi

# Prevent numpy error "ImportError: libptf77blas.so: cannot open shared object file: No such file or directory"
export LD_LIBRARY_PATH=/opt/local/lib:$LD_LIBRARY_PATH
#virtualenv --python=/home/gbt7/newt/bin/python "$venv_path"
# If you're going to make a new venv, you should use 2.7.18. I stuck that in a venv for monctrl that you could use:
virtualenv -p python2.7 "$venv_path"

# Enter the virtual environment
source "$venv_path/bin/activate"
pip install --upgrade pip
# Install numpy prior to other requirements due to poor dependency resolution in early pip versions
#pip install numpy==1.6.2
# Install the rest of the requirements
pip install -r requirements.txt

