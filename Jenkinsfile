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
                        docker { image 'python:3.12-slim' }
                    }
                    environment {
                        HOME = "${WORKSPACE}"
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
                        docker { image 'sonarsource/sonar-scanner-cli:latest' }
                    }
                    steps {
                        unstash 'workspace'
                        withCredentials([string(credentialsId: 'sonarcloud-token', variable: 'SONAR_TOKEN')]) {
                            // The scanner automatically picks up the SONAR_TOKEN environment variable
                            sh '''
                                sonar-scanner \
                                -Dsonar.projectKey=Nikhil-Thengane700_fastapi-eks-app \
                                -Dsonar.organization=nikhil-thengane700 \
                                -Dsonar.sources=app \
                                -Dsonar.python.version=3.12 \
                                -Dsonar.host.url=https://sonarcloud.io \
                                -Dsonar.userHome=${WORKSPACE}/.sonar
                            '''
                        }
                        stash includes: '.scannerwork/report-task.txt', name: 'sonar-report'
                    }
                }
            }
        }

        stage('Quality Gate') {
            agent any
            steps {
                unstash 'sonar-report'
                withCredentials([string(credentialsId: 'sonarcloud-token', variable: 'SONAR_TOKEN')]) {
                    sh '''
                        REPORT_FILE=".scannerwork/report-task.txt"
                        CE_TASK_URL=$(grep ceTaskUrl= "$REPORT_FILE" | cut -d'=' -f2-)

                        STATUS="PENDING"
                        for i in $(seq 1 30); do
                            STATUS=$(curl -s -u ${SONAR_TOKEN}: "$CE_TASK_URL" | grep -o '"status":"[A-Z]*"' | head -1 | cut -d'"' -f4)
                            if [ "$STATUS" = "SUCCESS" ]; then
                                break
                            fi
                            sleep 5
                        done

                        ANALYSIS_ID=$(curl -s -u ${SONAR_TOKEN}: "$CE_TASK_URL" | grep -o '"analysisId":"[^"]*"' | cut -d'"' -f4)
                        QG_STATUS=$(curl -s -u ${SONAR_TOKEN}: "https://sonarcloud.io/api/qualitygates/project_status?analysisId=${ANALYSIS_ID}" | grep -o '"status":"[A-Z]*"' | head -1 | cut -d'"' -f4)

                        echo "Quality Gate Status: ${QG_STATUS}"
                        if [ "$QG_STATUS" != "OK" ]; then
                            echo "Quality Gate failed"
                            exit 1
                        fi
                    '''
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
                    // Fix: Changed --entrypoint=/bin/sh to --entrypoint="" to prevent Jenkins conflict
                    args '-v /var/run/docker.sock:/var/run/docker.sock --entrypoint="" -u root'
                }
            }
            steps {
                sh "trivy image --severity HIGH,CRITICAL --exit-code 0 ${ECR_REPO_URI}:${env.IMAGE_TAG}"
            }
        }

        stage('Get ECR Token') {
            agent {
                docker {
                    image 'amazon/aws-cli:latest'
                    args '--entrypoint=/bin/sh'
                }
            }
            stepsstage('Get ECR Token') {
            agent {
                docker {
                    image 'amazon/aws-cli:latest'
                    // Fix: Overriding entrypoint so Jenkins doesn't try to run 'aws cat'
                    args '--entrypoint=""' 
                }
            }
            steps {
                sh "aws ecr get-login-password --region ${AWS_REGION} > ecr_token.txt"
                stash includes: 'ecr_token.txt', name: 'ecr-token'
            }
        } {
                sh "aws ecr get-login-password --region ${AWS_REGION} > ecr_token.txt"
                stash includes: 'ecr_token.txt', name: 'ecr-token'
            }
        }

        stage('Push to ECR') {
            agent {
                docker {
                    image 'docker:24-cli'
                    args '-v /var/run/docker.sock:/var/run/docker.sock -u root'
                }
            }
            steps {
                unstash 'ecr-token'
                sh """
                    cat ecr_token.txt | docker login --username AWS --password-stdin ${ECR_REPO_URI}
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
                sh 'docker image prune -f || true'
            }
        }
    }
}