pipeline {
    agent any
    environment {
        PYTHONUNBUFFERED = '1'
    }
    stages {
        stage('Setup Python') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt || true
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest --maxfail=1 --disable-warnings -q || true
                    python3 analyze_log.py || true
                '''
            }
        }
    }

    post {
        always {
            sh 'python3 analyze_log.py || true'
        }
    }
}
