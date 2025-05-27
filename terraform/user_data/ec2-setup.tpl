#!/bin/bash
set -euxo pipefail

# Redirect all output to log.
exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting EC2 bootstrap"

# Install base packages.
dnf update -y
dnf install -y docker openssl git aws-cli

systemctl enable docker
systemctl start docker

usermod -aG docker ec2-user

# Install Docker Compose !! Important: Do not make any changes to this part !!
cat > /usr/local/bin/install-docker-compose.sh <<'EOF'
#!/bin/bash
curl -SL https://github.com/docker/compose/releases/download/v2.36.0/docker-compose-linux-x86_64 \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
EOF

bash /usr/local/bin/install-docker-compose.sh


# Check version.
docker --version
docker-compose version || true

# Switch to ec2-user's home.
cd /home/ec2-user

# Download docker-compose.yml from GitHub.
curl -sSL https://raw.githubusercontent.com/datatribe-collective/gdd-app/docker-compose.yaml\
  -o docker-compose.yaml

# Fetch secrets from SSM and decrypt them.
POSTGRES_USER_E=$(aws ssm get-parameter --name "/gdd/POSTGRES_USER_E" --with-decryption --query "Parameter.Value" --output text)
POSTGRES_DB_E=$(aws ssm get-parameter --name "/gdd/POSTGRES_DB_E" --with-decryption --query "Parameter.Value" --output text)
POSTGRES_PASSWORD_E=$(aws ssm get-parameter --name "/gdd/POSTGRES_PASSWORD_E" --with-decryption --query "Parameter.Value" --output text)

AIRFLOW_USER_E=$(aws ssm get-parameter --name "/gdd/AIRFLOW_USER_E" --with-decryption --query "Parameter.Value" --output text)
AIRFLOW_PASSWORD_E=$(aws ssm get-parameter --name "/gdd/AIRFLOW_PASSWORD_E" --with-decryption --query "Parameter.Value" --output text)

# For reference, incase minio is being used under deployment.
# MINIO_ACCESS_KEY=$(aws ssm get-parameter --name "/gdd/MINIO_ACCESS_KEY" --with-decryption --query "Parameter.Value" --output text)
# MINIO_SECRET_KEY=$(aws ssm get-parameter --name "/gdd/MINIO_SECRET_KEY" --with-decryption --query "Parameter.Value" --output text)
# MINIO_DATA_BUCKET_NAME=$(aws ssm get-parameter --name "/gdd/MINIO_DATA_BUCKET_NAME" --with-decryption --query "Parameter.Value" --output text)
# MINIO_API_PORT_E=$(aws ssm get-parameter --name "/gdd/MINIO_API_PORT_E" --with-decryption --query "Parameter.Value" --output text)
# MINIO_CONSOLE_PORT_E=$(aws ssm get-parameter --name "/gdd/MINIO_CONSOLE_PORT_E" --with-decryption --query "Parameter.Value" --output text)

NGINX_ALLOWED_IP_1E=$(aws ssm get-parameter --name "/gdd/NGINX_ALLOWED_IP_1E" --with-decryption --query "Parameter.Value" --output text)
NGINX_ALLOWED_IP_2E=$(aws ssm get-parameter --name "/gdd/NGINX_ALLOWED_IP_2E" --with-decryption --query "Parameter.Value" --output text)


# Generate .env file for docker-compose.
cat > .env <<EOF
POSTGRES_USER_E=$${POSTGRES_USER_E}
POSTGRES_PASSWORD_E=$${POSTGRES_PASSWORD_E}
POSTGRES_DB_E=$${POSTGRES_DB_E}

AIRFLOW_ADMIN_USER=$${AIRFLOW_USER_E}
AIRFLOW_ADMIN_PASSWORD=$${AIRFLOW_PASSWORD_E}

# MINIO_ENDPOINT_URL=http://minio:9000
# MINIO_ACCESS_KEY=$${MINIO_ACCESS_KEY}
# MINIO_SECRET_KEY=$${MINIO_SECRET_KEY}
# MINIO_DATA_BUCKET_NAME=$${MINIO_DATA_BUCKET_NAME}
# MINIO_API_PORT_E=$${MINIO_API_PORT_E}
# MINIO_CONSOLE_PORT_E=$${MINIO_CONSOLE_PORT_E}

STORAGE_BACKEND=s3
BRONZE_PREFIX=bronze
SILVER_PREFIX=silver
GOLD_PREFIX=gold

NGINX_ALLOWED_IP_1=$${NGINX_ALLOWED_IP_1E}
NGINX_ALLOWED_IP_2=$${NGINX_ALLOWED_IP_2E}

EOF


# Make sure everything is owned by ec2-user.
chown -R ec2-user:ec2-user /home/ec2-user

# Start docker-compose stack.
docker-compose --env-file .env up -d

# Wipe out the .env file after use.
shred -u .env