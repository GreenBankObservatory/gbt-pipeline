#!/usr/bin/env groovy

pipeline {
  agent {
    label 'rhel8'
  }

  triggers {
    // trigger a weekly build on the master branch
    cron('@weekly')
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
          ./RunAllUnitTests
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
