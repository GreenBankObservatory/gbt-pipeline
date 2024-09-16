#!/usr/bin/env groovy

def schedule = env.BRANCH_NAME == 'master'       ? '@weekly' :
               env.BRANCH_NAME == 'release_19.4' ? '@weekly' : ''

pipeline {
  agent {
    label 'rhel8'
  }

  triggers {
    // trigger a weekly build on the master branch
    cron(schedule)
  }

  // environment {
  //   // LD_LIBRARY_PATH = "/opt/local/lib"
  // }

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

    stage('Install') {
      steps {
        sh 'uv sync'
      }
    }

    stage('Test') {
      steps {
        sh '''
          uv run pytest --junit-xml=junit.xml
        '''
        junit '**/*.xml'
      }
    }

    stage('Regression Test') {
      steps {
        sh '''
          uv run gbtpipeline -i /home/gbtpipeline/reference-data/TKFPA_29/TKFPA_29.raw.acs.fits
        '''
      }
    }
  }

  post {
    always {
      do_notify()
    }
  }
}
