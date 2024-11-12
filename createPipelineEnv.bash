#!/bin/bash

# Bail on errors
set -e

if [ -n "$1" ]; then
    venv_path="$1"
else
    venv_path="./${USER}_pipeline_env"
fi

export LD_LIBRARY_PATH=/opt/local/lib:$LD_LIBRARY_PATH

if [[ $(exec uname -r) == *el7* ]]; then
    echo Running on RH7 machine.
    virtualenv -p python2.7 "$venv_path"
else 
    echo Running on RH8 machine.
    /users/gbosdd/pythonversions/2.7/bin/virtualenv "$venv_path"
    #virtualenv --python /home/gbt7/newt/bin/python "$venv_path"
fi    
# Enter the virtual environment
source "$venv_path/bin/activate"
pip install --upgrade pip

# Install the rest of the requirements
pip install -r requirements.txt

# for dev purposes - REMOVE THIS IF ON MASTER
# pip install -e .

