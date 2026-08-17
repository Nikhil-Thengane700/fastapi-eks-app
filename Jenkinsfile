pipeline {
    agent none

    environment {
        AWS_REGION      = 'ap-south-1'
        ECR_REPO_URI    = '304485839932.dkr.ecr.ap-south-1.amazonaws.com/fastapi-eks-app'
        AWS_CREDS       = credentials('aws-ecr-creds')
    }

    stages {

        stage('Checkout') {
            agent any
            steps {
                checkout scm
                script {
                    env.IMAGE_TAG = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                }
                stash includes: '**', name: 'workspace'
            }
        }

        stage('Test & Code Quality') {
            parallel {
                stage('Unit Tests') {
                    agent {
                        docker {
                            image 'python:3.12-slim'
                            args '-u root'
                        }
                    }
                    steps {
                        unstash 'workspace'
                        sh '''
                            pip install -r requirements.txt --break-system-packages --quiet
                            pip install pytest httpx --break-system-packages --quiet
                            python -m pytest tests/ -v
                        '''
                    }
                }
                stage('SonarQube Scan') {
                    agent {
                        docker {
                            image 'sonarsource/sonar-scanner-cli:latest'
                            args '-u root --network host'
                        }
                    }
                    steps {
                        unstash 'workspace'
                        withSonarQubeEnv('SonarQube') {
                            sh '''
                                sonar-scanner \
                                -Dsonar.projectKey=fastapi-eks-app \
                                -Dsonar.sources=app \
                                -Dsonar.python.version=3.12
                            '''
                        }
                    }
                }
            }
        }

        stage('Quality Gate') {
            agent any
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Docker Build') {
            agent {
                docker {
                    image 'docker:24-cli'
                    args '-v /var/run/docker.sock:/var/run/docker.sock -u root'
                }
            }
            steps {
                unstash 'workspace'
                sh "docker build -t ${ECR_REPO_URI}:${env.IMAGE_TAG} ."
            }
        }

        stage('Trivy Scan') {
            agent {
                docker {
                    image 'aquasec/trivy:latest'
                    args '-v /var/run/docker.sock:/var/run/docker.sock --entrypoint="" -u root'
                }
            }
            steps {
                sh "trivy image --severity HIGH,CRITICAL --exit-code 0 ${ECR_REPO_URI}:${env.IMAGE_TAG}"
            }
        }

        stage('Push to ECR') {
            agent {
                docker {
                    image 'amazon/aws-cli:latest'
                    args '-v /var/run/docker.sock:/var/run/docker.sock --entrypoint="" -u root'
                }
            }
            steps {
                sh """
                    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO_URI}
                    docker push ${ECR_REPO_URI}:${env.IMAGE_TAG}
                """
            }
        }

        stage('Update Manifest') {
            agent any
            steps {
                unstash 'workspace'
                withCredentials([usernamePassword(credentialsId: 'github-creds', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
                    sh """
                        sed -i "s|image: .*|image: ${ECR_REPO_URI}:${env.IMAGE_TAG}|g" k8s/deployment.yaml
                        git config user.email "jenkins@ci.local"
                        git config user.name "Jenkins CI"
                        git add k8s/deployment.yaml
                        git commit -m "CI: update image tag to ${env.IMAGE_TAG}" || echo "No changes to commit"
                        git push https://\${GIT_USER}:\${GIT_TOKEN}@github.com/Nikhil-Thengane700/fastapi-eks-app.git HEAD:main
                    """
                }
            }
        }
    }

    post {
        always {
            node('') {
                sh 'docker system prune -f || true'
            }
        }
    }
}