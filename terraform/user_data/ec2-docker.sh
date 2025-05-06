#!/bin/bash

# Layer 3 - Application Layer Bootstrap (Docker setup)

# Update packages
dnf update -y

# Install Docker
dnf install -y docker

# Enable and start Docker service
systemctl enable docker
systemctl start docker

# Add ec2-user to the docker group -> run docker commands without sudo
usermod -a -G docker ec2-user

# Install Docker Compose (latest version)
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)

curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

chmod +x /usr/local/bin/docker-compose

# Optional: Verify installation. Logs to cloud-init logs, not visible directly in Terraform
docker-compose --version

