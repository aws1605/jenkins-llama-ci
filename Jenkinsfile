pipeline {
    agent any

    environment {
        PYTHON = "python3"
    }

    stages {
        stage('Setup Python') {
            steps {
                sh '''
                    echo "=== Setting up Python environment ==="
                    ${PYTHON} -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install requests pytest
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    echo "=== Running Tests and Capturing Log ==="
                    . venv/bin/activate
                    pytest --maxfail=1 --disable-warnings -q > build.log 2>&1 || true
                    echo "=== Test execution finished ==="
                    ls -lh build.log || true
                '''
            }
        }

        stage('AI Analysis and Email') {
            steps {
                sh '''
                    echo "=== Running AI Analysis ==="
                    . venv/bin/activate
                    ${PYTHON} analyze_log.py || true
                '''
            }
        }
    }

    post {
        always {
            echo "=== Cleaning up Workspace ==="
            sh 'ls -lh'
        }
    }
}
