pipeline {
    agent any

    environment {
        VENV = "${WORKSPACE}/venv"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/2025-summer-project/Backend.git'
                    ]]
                ])
            }
        }

        stage('Setup Python & Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    python manage.py test
                '''
            }
        }

        stage('Collect Static Files') {
            steps {
                sh '''
                    . venv/bin/activate
                    python manage.py collectstatic --noinput
                '''
            }
        }

        // 배포는 필요하면 열어줘!
        // stage('Deploy') {
        //     steps {
        //         sh './deploy.sh'
        //     }
        // }
    }

    post {
        always {
            echo '작업 완료'
        }
        failure {
            echo '테스트 실패!'
        }
    }
}
