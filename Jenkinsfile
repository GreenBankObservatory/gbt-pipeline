#!/usr/bin/env groovy

def schedule = env.BRANCH_NAME == 'master'       ? '@weekly' :
               env.BRANCH_NAME == 'release_19.4' ? '@weekly' : ''

pipeline {
  agent {
    label 'rhel7'
  }

  triggers {
    // trigger a weekly build on the master branch
    cron(schedule)
  }

  environment {
    LD_LIBRARY_PATH = "/opt/local/lib"
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

    stage('Examples') {
      steps {
        sh '''
          source jenkins-pipeline-env/bin/activate
          ./pipeline_examples
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          source jenkins-pipeline-env/bin/activate
          nosetests --with-xunit --xunit-file=unittests.xml test/gbtpipeline_unit_tests.py
          nosetests --with-xunit --xunit-file=calibration.xml test/test_Calibration.py
          nosetests --with-xunit --xunit-file=pipeutils.xml test/test_Pipeutils.py
          nosetests --with-xunit --xunit-file=smoothing.xml test/test_smoothing.py
        '''
        junit '**/*.xml'
      }
    }
  }

  post {
    always {
      do_notify()
    }
  }
}
