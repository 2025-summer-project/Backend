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

       stage('Load .env from Jenkins') {
            steps {
                configFileProvider([configFile(fileId: 'my_backend_env', targetLocation: '.env')]) {
                echo ".env 파일을 Jenkins에서 로드했어요 💚"
            }
        }
    }


        stage('Install System Packages') {
            steps {
                sh '''
                    apt-get update
                    apt-get install -y pkg-config libmariadb-dev libmariadb-dev-compat gcc python3-dev
                '''
            }
        }

        stage('Setup Python & Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip setuptools wheel
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
    }

    post {
        success {
            sh """
            curl -H "Content-Type: application/json" \\
                 -X POST \\
                 -d '{
                     "username": "Jenkins CI",
                     "avatar_url": "https://www.jenkins.io/images/logos/jenkins/jenkins.png",
                     "embeds": [{
                         "title": "✅ Backend 빌드 성공!",
                         "description": "**Job:** #${env.BUILD_NUMBER}\\n🔗 [Jenkins에서 보기](${env.BUILD_URL})",
                         "color": 65280
                     }]
                 }' \
                 https://discord.com/api/webhooks/1392458187940298803/y3iurVacjDbVYc8LUZNCTjU0oSDVKTGagQwT5em2iGoj1sJ7vvuKL5I469zeZbfhLHqS
            """
        }
    }
}
