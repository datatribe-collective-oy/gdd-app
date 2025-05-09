#!/bin/bash

# --- PART 1: DOCKER + COMPOSE INSTALL --- #

# Refresh package cache
dnf makecache -y

# Install Docker
dnf install -y docker
systemctl enable docker
systemctl start docker

# Add ec2-user to docker group (non-root access)
usermod -a -G docker ec2-user

# Install latest Docker Compose (v2 style)
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# --- PART 2: CLONE YOUR PROJECT --- #

cd /home/ec2-user

# Clone specific branch (adjust as needed)
git clone --branch feature/dags https://github.com/datatribe-collective/gdd-app.git

# Exit if cloning failed
if [ ! -d "gdd-app" ]; then
    echo "Git clone failed. Check branch or repo URL."
    exit 1
fi

cd gdd-app

# --- PART 3: START CONTAINERS --- #

docker compose build
docker compose up -d

# --- SCRIPT COMPLETE --- #
