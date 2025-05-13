#!/bin/bash -xe
# The -xe flags mean:
# -x: Print commands and their arguments as they are executed.
# -e: Exit immediately if a command exits with a non-zero status.

# Update all packages
sudo dnf update -y

# Install Nginx
sudo dnf install nginx -y
sudo systemctl enable --now nginx # Enable and start Nginx

# Install Docker
sudo dnf install docker -y
sudo systemctl enable --now docker # Enable and start Docker
sudo usermod -a -G docker ec2-user # Add ec2-user to the docker group
                                   # Note: A logout/login or reboot is required for this group change to take effect in an interactive shell.

# Install Docker Compose (latest version from GitHub)
# Fetch the latest release version tag for Docker Compose
LATEST_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')

# Fallback if API call fails or for offline environments (adjust version as needed)
if [ -z "$LATEST_COMPOSE_VERSION" ]; then
    # You can manually find the latest from: https://github.com/docker/compose/releases
    LATEST_COMPOSE_VERSION="v2.27.0" # Example: Manually specify a recent version as a fallback (check for the actual latest)
    echo "Failed to fetch latest Docker Compose version, using fallback: ${LATEST_COMPOSE_VERSION}"
else
    echo "Fetched latest Docker Compose version: ${LATEST_COMPOSE_VERSION}"
fi

sudo curl -L "https://github.com/docker/compose/releases/download/${LATEST_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation by creating a symlink, which will fail if /usr/local/bin/docker-compose doesn't exist or isn't executable.
# This also makes 'docker-compose' available in standard paths if not already.
if [ -f /usr/local/bin/docker-compose ]; then
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    echo "Docker Compose installed successfully."
    # Attempt to get version to confirm
    /usr/local/bin/docker-compose version
else
    echo "ERROR: Docker Compose binary not found at /usr/local/bin/docker-compose after download."
    exit 1 # Exit with error if compose is not found
fi

# Log completion
echo "User data script finished successfully at $(date)" > /var/log/user-data-status.txt
echo "Nginx, Docker, and Docker Compose installation attempted on Amazon Linux 2023." >> /var/log/user-data-status.txt
echo "You can check this file on the instance via SSH: cat /var/log/user-data-status.txt" >> /var/log/user-data-status.txt
echo "Also check cloud-init logs: sudo cat /var/log/cloud-init-output.log" >> /var/log/user-data-status.txt