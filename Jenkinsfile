pipeline {
agent any
stages {

    stage('Checkout Code') {
        steps {
            git branch: 'main',
                url: 'https://github.com/kalpesh-pachpute/Prediction-application.git'
        }
    }

    stage('Verify Docker') {
        steps {
            bat 'docker --version'
            bat 'docker compose version'
        }
    }

    stage('Cleanup Existing Containers') {
        steps {
            bat 'docker compose down --remove-orphans'
        }
    }

    stage('Deploy Application') {
        steps {
            bat 'docker compose up -d --build'
        }
    }

    stage('Verify Deployment') {
        steps {
            bat 'docker compose ps'
        }
    }
}

post {
    success {
        echo 'Deployment successful'
    }

    failure {
        echo 'Deployment failed'
    }

    always {
        bat 'docker compose ps'
    }
}

}
