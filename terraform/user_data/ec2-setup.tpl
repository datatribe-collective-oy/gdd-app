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

# Install Docker Compose !! Important: Do not make any changes to this part !!
cat > /usr/local/bin/install-docker-compose.sh <<'EOF'
#!/bin/bash
curl -SL https://github.com/docker/compose/releases/download/v2.36.0/docker-compose-linux-x86_64 \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
EOF

bash /usr/local/bin/install-docker-compose.sh


# Check version
docker --version
docker-compose version || true


docker-compose up -d || true


echo "Docker setup completed."
