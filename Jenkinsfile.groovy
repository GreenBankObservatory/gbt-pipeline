def lastCommit() {
    sh 'git log --format="%ae" | head -1 > commit-author.txt'                 
    lastAuthor = readFile('commit-author.txt').trim()
    sh 'rm commit-author.txt'
    return lastAuthor
}

// Used to send email notification of success or failure
def notify(status, details){
    def link = "http://colossus:8081/job/gbt-pipeline/${env.BUILD_NUMBER}"
    def failure_description = "";
    def lastChangedBy = lastCommit()
    if (status == 'failure') {
        failure_description = """${env.BUILD_NUMBER} failed."""
    }
    emailext (
      to: "nsizemor@nrao.edu",
      subject: "${status}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
      body: """${status}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':
        ${failure_description}
        Last commit by: ${lastChangedBy}
        Build summary: ${env.BUILD_URL}"""
    )
}

def checkout() {
    git '/home/sandboxes/nsizemor/repos/gbt-pipeline'
}

def build() {
    sh '''
        ./createPipelineEnv.bash
   '''
}

def runUnitTests() {
    sh '''
        source pipelineEnv/bin/activate
        source /opt/rh/devtoolset-4/enable
        cd test
        nosetests --with-xunit gbtpipeline_unit_tests.py
    '''
}

node {
    stage('Checkout') {
        try {
            cleanWs()
            checkout()
        } catch(error) {
            echo "Failure!"
            notify('failure', 'An error has occurred during the <b>Checkout</b> stage.')
            throw(error)
        }
    }
 
     stage('Build') {
        try {
            build()
        } catch(error) {
            echo "Failure!"
            notify('failure', 'An error has occurred during the <b>Build</b> stage.')
            throw(error)
        }
    }

    stage('Test') {
        try {
            runUnitTests()
            junit '**/nosetests.xml'
        } catch(error) {
            echo "Failure!"
            notify('failure', 'An error has occurred during the <b>Test</b> stage.')
            throw(error)
        }
    }

    stage('Notify') {
         notify('success', 'Sparrow built and tested successfully.')
    }
} 

