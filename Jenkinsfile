pipeline{
    agent any
    stages{
        stage('checkout code'){
            steps{
                git branch:'main',
                url:'https://github.com/kalpesh-pachpute/Prediction-application.git'
            }
        }
        stage('verify docker'){
            steps{
                bat 'docker --version'
                bat 'docker compose version'
            }
        }
        stage('build container'){
            steps{
                bat 'docker compose build'
            }
        }
        stage('deploy container'){
            steps{
                bat 'docker compose down'
                bat 'docker compose up -d'
            }
        }
        stage('verify deployment'){
            steps{
                bat 'docker compose ps'
            }
        }

    }
    post{
        success{
            echo 'Deployment successful'
        }
        failure{
            echo 'Deployment failed'
        }
    }
}