pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps {
        checkout([$class: 'GitSCM', branches: [[name: '*/main']],
                  userRemoteConfigs: [[url: 'https://github.com/<yourusername>/jenkins-llama-ci.git']]])
      }
    }

    stage('Setup Python') {
      steps {
        sh 'python3 --version || true'
        sh 'python3 -m venv venv || true'
        sh '. venv/bin/activate && pip install -r requirements.txt || true'
      }
    }

    stage('Run Tests') {
      steps {
        sh '''
           set -o pipefail
           (pytest -q 2>&1) | tee build.log
        '''
        archiveArtifacts artifacts: 'build.log', fingerprint: true
      }
    }
  }

  post {
    always {
      sh 'python3 analyze_log.py || true'
    }
  }
}
