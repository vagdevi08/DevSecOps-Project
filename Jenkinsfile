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
    REPO_URL = 'https://github.com/vagdevi08/secDevLabs'
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
        git 'https://github.com/vagdevi08/secDevLabs.git'
      }
    }

    stage('Secrets Scan') {
      steps {
        echo 'Running truffleHog...'
        sh 'trufflehog filesystem . --no-update'
      }
    }

    stage('Software Composition Analysis') {
      steps {
        echo 'Running safety check...'
        sh 'safety check -r $REQ_FILE || true'

        echo 'Checking dependency licenses...'
        sh '''
          python3 -m venv venv
          . venv/bin/activate
          pip install -r $REQ_FILE
          pip install pip-licenses
          pip-licenses
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

      sh '''
        mkdir -p $BUILD_LOG_DIR
        lynis audit dockerfile $DOCKERFILE_PATH | tee $BUILD_LOG_DIR/docker_lynis.log
      '''
    }
  }
}

          stage('Setup test env') {
          steps {
              sh """
	      #refresh inventory
	      echo "[local]" > ~/ansible_hosts
	      echo "localhost ansible_connection=local" >> ~/ansible_hosts
	      echo "[tstlaunched]" >> ~/ansible_hosts
	      
	      tar cvfz /var/jenkins_home/pythonapp.tar.gz -C $WORKSPACE/owasp-top10-2017-apps/a7/ .

              ssh-keygen -t rsa -N "" -f ~/.ssh/psp_ansible_key || true
              ansible-playbook -i ~/ansible_hosts /home/ubuntu/DevSecOps-Project/jenkins_home/createAwsEc2.yml
              """		  
	      script{
		 testenv = sh(script: "sed -n '/tstlaunched/{n;p;}' /var/jenkins_home/ansible_hosts", returnStdout: true).trim()
	      }
	      echo "${testenv}"
	      sh  'ansible-playbook -i ~/ansible_hosts /home/ubuntu/DevSecOps-Project/jenkins_home/configureTestEnv.yml'
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
