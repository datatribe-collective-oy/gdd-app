#!/bin/bash
set -euxo pipefail

# Log setup
# exec > /var/log/user-data.log 2>&1
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
set -e


echo "Starting Docker install on Amazon Linux 2023..."

# Update system and install Docker
dnf update -y || echo "dnf update failed"
dnf install -y nginx openssl docker || echo "Install failed"

# Start and enable Docker
systemctl enable docker
systemctl start docker

# Add ec2-user to the docker group
usermod -aG docker ec2-user

# Install Docker Compose v2 (plugin)
dnf install -y docker-compose-plugin

# Test
docker --version
docker compose version || true  # Avoid failure if not installed

echo "Docker setup completed."
