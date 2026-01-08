#!/bin/bash

set -e  # Exit on error
set -o pipefail

# --- Update system and install essentials ---
echo "🔧 Updating and installing Docker, Compose, Java..."
apt-get update -y
apt-get install -y docker.io docker-compose default-jre curl openssl

# Add Ubuntu user to Docker group
usermod -aG docker ubuntu

# Enable Docker to start on boot
systemctl enable docker

# --- Generate Jenkins config values ---
echo "🔐 Generating Jenkins credentials and environment config..."
export Jenkins_PW=$(openssl rand -base64 16)
export JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

# Get instance metadata (works on EC2)
export JenkinsPublicHostname=$(curl -s http://169.254.169.254/latest/meta-data/public-hostname)
export SeleniumPrivateIp=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)

echo "🌐 Jenkins Hostname: $JenkinsPublicHostname"
echo "🌐 Selenium Private IP: $SeleniumPrivateIp"

# --- Launch containers ---
echo "🐳 Building and starting Docker containers..."
docker-compose up -d --build

echo "⏳ Waiting for Jenkins to initialize..."
sleep 45  # Wait for Jenkins to boot and run init scripts

# --- Download Jenkins CLI ---
echo "📥 Downloading Jenkins CLI..."
wget -q http://127.0.0.1:8080/jnlpJars/jenkins-cli.jar

# --- Create Jenkins pipeline job ---
echo "📦 Creating Jenkins job from config.xml..."
java -jar ./jenkins-cli.jar \
     -s http://localhost:8080 \
     -auth myjenkins:$Jenkins_PW \
     create-job pythonpipeline < config.xml

echo -e "\n✅ Jenkins setup complete!"
echo "🚪 Login Credentials:"
echo "👤 Username: myjenkins"
echo "🔑 Password: $Jenkins_PW"
