# AWS Services

## Overview

This document outlines the AWS services used by the GDD Timing System application. The infrastructure follows a secure-by-default approach with isolated networking, least-privilege access controls, and comprehensive logging. All infrastructure is defined as code using Terraform to ensure consistency and reproducibility.

The project leverages several AWS services to host and manage the application. These services are mostly provisioned and managed using Terraform, as defined in the [terraform/main.tf](../terraform/main.tf) file.


## Amazon EC2 (Elastic Compute Cloud)

- **Resource:** `aws_instance.gdd_server`
- **Purpose:** An EC2 instance is provisioned to serve as the primary server for the application. It hosts the Docker containers for NGINX, FastAPI, Streamlit, and Airflow.
- **Details:**
  - The instance type is `t3.micro` (defined in [`aws_instance.gdd_server`](../terraform/main.tf)).
  - It uses an Amazon Linux 2023 AMI (AMI ID: `ami-0dd574ef87b79ac6c` defined in [`aws_instance.gdd_server`](../terraform/main.tf)).
  - User data script, [terraform/user_data/ec2-docker.sh](../terraform/user_data/ec2-docker.sh), is used to bootstrap the instance, primarily for installing Docker and Docker Compose.
  - An SSH key pair ([`aws_key_pair.gdd_key`](../terraform/main.tf)) is associated with the instance with IP-whitelisting enabled for secure access.

## Amazon S3 (Simple Storage Service)

- **Resource:** `aws_s3_bucket.gdd_raw_data`
- **Purpose:** An S3 bucket is used for storing raw weather data fetched by the Airflow DAGs. This data is then processed and used by the application.
- **Details:**
  - The bucket is named `gdd-raw-weather-data` (defined in [`aws_s3_bucket.gdd_raw_data`](../terraform/main.tf)).
  - Public access to the bucket is blocked via [`aws_s3_bucket_public_access_block.gdd_raw_data_block`](../terraform/main.tf) to ensure data privacy.

## Amazon VPC (Virtual Private Cloud)

- **Resource:** `aws_vpc.gdd_vpc`
- **Purpose:** A VPC is created to provide an isolated network environment for the AWS resources.
- **Details:**
  - The VPC has a CIDR block of `10.0.0.0/16`.
  - DNS support and hostnames are enabled.

## AWS Networking Components

- **Subnet (`aws_subnet.gdd_public_subnet`):** A public subnet is created within the VPC to allow the EC2 instance to be accessible from the internet. It's configured to map public IPs on launch.
- **Internet Gateway (`aws_internet_gateway.gdd_igw`):** An Internet Gateway is attached to the VPC to enable communication between resources in the VPC and the internet.
- **Route Table (`aws_route_table.gdd_route_table`):** A route table is configured to direct outbound traffic from the public subnet (`0.0.0.0/0`) to the Internet Gateway.
- **Route Table Association (`aws_route_table_association.gdd_rta`):** Associates the public subnet with the main route table.

## AWS Security Group

- **Resource:** `aws_security_group.gdd_sg`
- **Purpose:** A security group acts as a virtual firewall for the EC2 instance, controlling inbound and outbound traffic.
- **Details:**
  - **Ingress Rules:** Allows inbound traffic on:
    - Port 80 (HTTP) from anywhere (`0.0.0.0/0`).
    - Port 22 (SSH) from specified IP addresses (defined by the `ssh_allowed_ips` variable in your Terraform configuration).
  - **Egress Rules:** Allows all outbound traffic.

## Security Considerations


- **Logging and Monitoring:**
  - **Infrastructure Logging:** AWS CloudTrail is logging to track API calls and changes made to the AWS environment by the Terraform.
  - **Application Logging:**
    - Terraform user data script output is logged to `/var/log/user-data.log` and system journal.
    - Docker compose container logs are available via `docker-compose logs`.
    - All bootstrap operations are logged with timestamps via `set -x`.
  - **Planned CloudWatch Integration:**
    - AWS CloudWatch will be configured for EC2 instance monitoring.
    - Docker container logs will be forwarded to CloudWatch Logs.
    - If possible, user data script logs will be streamed to CloudWatch Logs using CloudWatch agent.
- **IAM Policies:**
  - IAM policies for the Terraform user/role, which grants permissions to provision resources, are managed separately and adhere to the principle of least privilege.
  - The IAM instance profile (`var.iam_instance_profile_name`) attached to the EC2 instance is also defined and managed outside of this specific Terraform configuration for infrastructure, granting the EC2 instance necessary permissions (e.g., to access S3).
  - **Terraform Scope:** The Terraform configuration focuses on provisioning the core infrastructure (VPC, EC2, S3, etc.) and does not manage IAM users, roles, or policies directly, separating infrastructure concerns from identity and access management.
- **SSH Key Management:** The SSH key pair used for accessing the EC2 instance is managed separately, ensuring secure access to the instance without hardcoding sensitive information in the Terraform configuration.

As detailed in [docs/system-architecture.md](../docs/system-architecture.md), NGINX, running on the EC2 instance, manages external access to the different application services.
