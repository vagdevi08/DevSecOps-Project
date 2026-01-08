/*
DevSecOps Pipeline for PythonSecurityPipeline

Stages:
1. Git Secrets Check (truffleHog)
2. Software Composition Analysis (Safety + Liccheck)
3. Static Code Analysis (Bandit)
4. Docker Security Audit (Lynis)
5. Environment Setup (EC2 via Ansible)
6. Dynamic App Security Testing (Selenium + Nikto)
7. Host Audit (Lynis via Ansible)
8. Web Application Firewall Deployment (ModSecurity)
*/

def testenv = "null"

pipeline {
  agent any

  environment {
    REPO_URL = 'https://github.com/pawnu/secDevLabs.git'
    REQ_FILE = 'owasp-top10-2017-apps/a7/gossip-world/app/requirements.txt'
    APP_DIR = 'owasp-top10-2017-apps/a7/gossip-world'
    DOCKERFILE_PATH = 'owasp-top10-2017-apps/a7/gossip-world/deployments/Dockerfile'
    ARCHIVE_PATH = '/var/jenkins_home/pythonapp.tar.gz'
    ANSIBLE_HOSTS = '/var/jenkins_home/ansible_hosts'
    BUILD_LOG_DIR = "${env.WORKSPACE}/${env.BUILD_TAG}"
  }

  stages {
    stage('Checkout') {
      steps {
        echo 'Cloning project repo...'
        git 'https://github.com/pawnu/secDevLabs.git'
      }
    }

    stage('Secrets Scan') {
      steps {
        echo 'Running truffleHog...'
        sh 'trufflehog git https://github.com/pawnu/secDevLabs.git --no-update'
      }
    }

    stage('Software Composition Analysis') {
      steps {
        echo 'Running safety check...'
        sh 'safety check -r $REQ_FILE || true'

        echo 'Running liccheck...'
        sh '''
          virtualenv venv
          source venv/bin/activate
          pip install -r $REQ_FILE
          liccheck -s ~/strategy.ini -r $REQ_FILE || true
          deactivate
        '''
      }
    }

    stage('Static Analysis (SAST)') {
      steps {
        echo 'Running Bandit scan...'
        sh 'bandit -r $APP_DIR -ll || true'
      }
    }

    stage('Container Security Audit') {
      steps {
        script {
          echo 'Running Lynis Dockerfile audit...'

          def lynisDir = '/var/jenkins_home/lynis'
          if (!fileExists("${lynisDir}/lynis")) {
            sh """
              wget https://downloads.cisofy.com/lynis/lynis-3.0.9.tar.gz -O /tmp/lynis.tar.gz
              mkdir -p ${lynisDir}
              tar xfvz /tmp/lynis.tar.gz -C ${lynisDir} --strip-components=1
            """
          }

          dir(lynisDir) {
            sh """
              mkdir -p $BUILD_LOG_DIR
              ./lynis audit dockerfile $DOCKERFILE_PATH | ansi2html > $BUILD_LOG_DIR/docker-report.html
              mv /tmp/lynis.log $BUILD_LOG_DIR/docker_lynis.log || true
              mv /tmp/lynis-report.dat $BUILD_LOG_DIR/docker_lynis-report.dat || true
            """
          }
        }
      }
    }

    stage('Provision Test Environment') {
      steps {
        echo 'Setting up EC2 test environment...'
        sh '''
          echo "[local]" > $ANSIBLE_HOSTS
          echo "localhost ansible_connection=local" >> $ANSIBLE_HOSTS
          echo "[tstlaunched]" >> $ANSIBLE_HOSTS

          tar czf $ARCHIVE_PATH -C owasp-top10-2017-apps/a7/ .

          ssh-keygen -t rsa -N "" -f ~/.ssh/psp_ansible_key || true
          ansible-playbook -i $ANSIBLE_HOSTS ~/createAwsEc2.yml
        '''
        script {
          testenv = sh(
            script: "awk '/\\[tstlaunched\\]/{getline; print}' $ANSIBLE_HOSTS",
            returnStdout: true
          ).trim()
          echo "Test environment IP: ${testenv}"
        }

        sh 'ansible-playbook -i $ANSIBLE_HOSTS ~/configureTestEnv.yml'
      }
    }

    stage('DAST (Authenticated Scan)') {
      steps {
        echo 'Running Authenticated Dynamic Scan...'
        script {
          if (testenv != "null") {
            def seleniumIp = env.SeleniumPrivateIp ?: "selenium-chrome"
            sh "python ~/authDAST.py $seleniumIp ${testenv} $BUILD_LOG_DIR/DAST_results.html"
          } else {
            error("Test environment not found!")
          }
        }
      }
    }

    stage('System Audit') {
      steps {
        echo 'Running host audit with Lynis...'
        sh 'ansible-playbook -i $ANSIBLE_HOSTS ~/hostaudit.yml --extra-vars "logfolder=$BUILD_LOG_DIR/"'
      }
    }

    stage('Deploy WAF') {
      steps {
        echo 'Deploying ModSecurity WAF...'
        sh 'ansible-playbook -i $ANSIBLE_HOSTS ~/configureWAF.yml'
      }
    }
  }

  post {
    always {
      echo 'Pipeline finished. Optionally terminate EC2 instance.'
      /*
      if (testenv != "null") {
        echo "Tearing down test host: ${testenv}"
        sh 'ansible-playbook -i $ANSIBLE_HOSTS ~/killec2.yml'
      }
      */
    }
  }
}
