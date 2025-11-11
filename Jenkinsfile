pipeline {
    agent any

    environment {
        OLLAMA_HOST = "http://localhost:11434"
        MODEL = "llama3.2"
        PYTHON = "python3"
    }

    stages {
        stage('Setup Python') {
            steps {
                sh '''
                    echo "=== Setting up Python environment ==="
                    sudo apt update -y
                    sudo apt install -y python3-venv
                    ${PYTHON} -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install requests
                    pip install pytest
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
