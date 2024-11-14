#!/usr/bin/env groovy

def schedule = env.BRANCH_NAME == 'master'       ? '@weekly' :
               env.BRANCH_NAME == 'release_24.4' ? '@weekly' : ''

pipeline {
  agent {
    label 'rhel8-not-broken'
  }

  triggers {
    // trigger a weekly build on the master branch
    cron(schedule)
  }

  //environment {
  //  LD_LIBRARY_PATH = "/opt/local/lib"
  //}

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
          ./RunAllUnitTests
        '''
        junit '**/*.xml'
      }
    }
  }

  post {
    always {
      do_notify(to: 'sddev@nrao.edu')
    }
  }
}
