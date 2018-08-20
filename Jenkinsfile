pipeline {
  agent {
    // label 'rhel7'
    'any'
  }

  stages {
    stage('Init') {
      steps {
        lastChanges(
          since: 'LAST_SUCCESSFUL_BUILD',
          format:'SIDE',
          matching: 'LINE'
        )
      }
    }

    stage('virtualenv') {
      steps {
        sh './createPipelineEnv.bash jenkins-pipeline-env'
      }
    }

    stage('Test') {
      steps {
        sh '''
          export LD_LIBRARY_PATH=/opt/local/lib:$LD_LIBRARY_PATH
          source jenkins-pipeline-env/bin/activate
          source /opt/rh/devtoolset-4/enable
          nosetests --with-xunit --xunit-file=unittests.xml test/gbtpipeline_unit_tests.py
          nosetests --with-xunit --xunit-file=calibration.xml test/test_Calibration.py
          #nosetests --with-xunit --xunit-file=inegration.xml test/test_Integration.py
          nosetests --with-xunit --xunit-file=pipeutils.xml test/test_Pipeutils.py
          nosetests --with-xunit --xunit-file=smoothing.xml test/test_smoothing.py
        '''
        junit '**/*.xml'
      }
    }
  }

  post {
    always {
      do_notify(to: 'tchamber@nrao.edu')
    }
  }
}
