#!/bin/bash
set -euo pipefail

log() {
  echo -e "\033[1;34m[INFO]\033[0m $1"
}

fail() {
  echo -e "\033[1;31m[ERROR]\033[0m $1"
  exit 1
}

# --- PART 1: DOCKER + COMPOSE INSTALL --- #
log "Refreshing package cache..."
dnf makecache -y || fail "dnf makecache failed"

log "Installing Docker..."
dnf install -y docker || fail "Docker installation failed"

log "Enabling and starting Docker..."
systemctl enable docker || fail "Failed to enable Docker"
systemctl start docker || fail "Failed to start Docker"

log "Adding ec2-user to Docker group..."
usermod -a -G docker ec2-user || fail "Failed to add ec2-user to docker group"

log "Installing Docker Compose..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose || fail "Failed to download docker-compose"
chmod +x /usr/local/bin/docker-compose

# --- PART 2: CLONE YOUR PROJECT --- #
cd /home/ec2-user

log "Cloning project repository (branch: feature/dags)..."
git clone --branch feature/dags https://github.com/datatribe-collective/gdd-app.git || fail "Git clone failed"

cd gdd-app || fail "gdd-app folder not found after clone"

# --- PART 3: BUILD AND START CONTAINERS --- #
log "Building containers..."
docker compose build || fail "Docker compose build failed"

log "Starting containers in detached mode..."
docker compose up || fail "Docker compose up failed"

log "Script completed successfully."
