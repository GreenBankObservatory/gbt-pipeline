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

  environment {
    // LD_LIBRARY_PATH = "/opt/local/lib"
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
        sh 'uv sync'
      }
    }

    stage('Examples') {
      steps {
        sh '''
          uv run ./pipeline_examples
        '''
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
  }

  post {
    always {
      do_notify()
    }
  }
}
