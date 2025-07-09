pipeline {
    agent any  // 어떤 에이전트에서든 실행

    environment {
        // 필요한 경우 가상환경 경로 또는 환경변수 설정
        VENV = "${WORKSPACE}/venv"
    }

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/your-org/your-django-project.git'
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

        // 필요하다면 아래처럼 배포 스테이지도 추가 가능
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
