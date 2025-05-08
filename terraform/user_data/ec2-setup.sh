#!/bin/bash

### --- PART 1: NGINX + HTTPS --- ###

# Update package cache only (no full upgrade to avoid long boot times)
dnf makecache -y

# Install nginx and openssl
dnf install -y nginx openssl

# Enable and start nginx
systemctl enable nginx
systemctl start nginx

# Create self-signed certificate (valid for 1 year)
mkdir -p /etc/ssl/certs /etc/ssl/private
openssl req -x509 -nodes -days 365 \
-newkey rsa:2048 \
-keyout /etc/ssl/private/gdd_selfsigned.key \
-out /etc/ssl/certs/gdd_selfsigned.crt \
-subj "/C=GB/ST=London/L=London/O=GDD/OU=Dev/CN=localhost"

# Create nginx reverse proxy config
tee /etc/nginx/conf.d/gdd_app.conf > /dev/null <<'EOF'
server {
    listen 443 ssl;
    server_name _;

    ssl_certificate /etc/ssl/certs/gdd_selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/gdd_selfsigned.key;

    location / {
        proxy_pass http://127.0.0.1:8501/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Test nginx config and reload
nginx -t && systemctl reload nginx

### --- PART 2: DOCKER + DOCKER COMPOSE --- ###

# Install Docker
dnf install -y docker

# Enable and start Docker service
systemctl enable docker
systemctl start docker

# Add ec2-user to docker group
usermod -a -G docker ec2-user

# Install latest Docker Compose dynamically
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)

curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

chmod +x /usr/local/bin/docker-compose

# Optional: Log docker compose version to cloud-init logs for debugging
docker-compose --version



### --- PART 3: (Optional) Start Docker Compose --- ###

# NOTE:
# If you want Terraform to automatically start your Docker Compose stack
# when the EC2 instance boots, uncomment the following lines.
# For now, they are commented so you can start the stack manually for testing.

# cd /home/ec2-user
# docker-compose up -d

# Reminder:
# This assumes your docker-compose.yml is located at:
# /home/ec2-user/docker-compose.yml

### --- SCRIPT COMPLETE --- ###
