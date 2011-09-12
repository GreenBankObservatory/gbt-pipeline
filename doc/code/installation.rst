Pipeline Installation
=====================

Updating test
-------------

The test version of the pipeline (gbtpipeline-test) is automatically updated every hour from code checked into the github repository master branch.  This is done via a cronjob in the pipeline account which runs an update script (/users/pipeline/update-test-version.sh).

The gbtpipeline-test executable is a symlink chain in /opt/local/bin with the following structure:

| /opt/local/bin/gbtpipeline-test
| --> /opt/local/stow/nrao-gb/bin/gbtpipeline-test
| --> /home/gbtpipeline/integration/gbtpipeline

Updating the release
--------------------

Updating the release version of the pipeline is a more involved process than updating test.  Special care must be given to not introduce bugs and break dependencies.  For this reason, 
there is no automatic update.  However, scripts exist to simplify the process.

.. todo:: describe the scripts

The gbtpipeline executable is a symlink chain in /opt/local/bin with the following structure:

| /opt/local/bin/gbtpipeline
| --> /opt/local/stow/nrao-gb/bin/gbtpipeline
| --> /home/gbtpipeline/release/gbtpipeline
| --> /home/gbtpipeline/{M}.{m}/gbtpipeline

where {M} and {m} are major and minor revision number, respectively.

The previous release is moved to gbtpipeline-old so that is still accessible until the next release.  The link structure is as follows:

| /opt/local/bin/gbtpipeline-old
| --> /opt/local/stow/nrao-gb/bin/gbtpipeline-old
| --> /home/gbtpipeline/old/gbtpipeline
| --> /home/gbtpipeline/{M}.{m}/gbtpipeline

where {M} and {m} are major and minor revision number, respectively.

Installation from scratch
-------------------------

Begininng a pipeline installation from scratch is an involved process.

.. todo:: needs to be filled in

Off-site use
------------

The pipeline is currently not able to run off-site without some hacking of the pipeline code.  To begin with, the startup script (gbtpipeline) assumes we are on the GB network.  The purpose of the script is to set up paths, so it can be modified to set correct paths for another computing environment.

The weather forecast files only live on the GB network, in the home directory of Ron Maddalena.  A user can either stop calibration at Ta, or if they have a GB account, they can modify the code to copy the forecast files to their local machine during the course of a pipeline execution.

Furthermore, pipeline dependencies must be available.  These requirements can be found in the :doc:`dependencies` section of the documentation.