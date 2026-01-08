# Use the latest Jenkins LTS image
FROM jenkins/jenkins:lts-jdk11

LABEL maintainer="Vagdevi Sagi <sagivagdevi@gmail.com>"

USER root

# Pre-install Jenkins plugins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Auto-create Jenkins admin user
COPY setupJenkins.groovy /usr/share/jenkins/ref/init.groovy.d/

# Install dependencies and tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl \
    maven \
    git \
    perl \
    wget \
    libnet-ssleay-perl \
    software-properties-common \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Add multiverse repo and install nikto
RUN add-apt-repository multiverse && \
    apt-get update && \
    apt-get install -y nikto && \
    rm -rf /var/lib/apt/lists/*

# Install Python security tools (SCA, SAST, secrets scanning)
RUN pip3 install --no-cache-dir \
    virtualenv \
    safety \
    liccheck \
    trufflehog \
    bandit \
    selenium \
    ansible \
    boto \
    boto3

# Copy ansible configuration
COPY ansible.cfg /etc/ansible/ansible.cfg

# Drop back to Jenkins user for security
USER jenkins
