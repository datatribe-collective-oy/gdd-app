# Security Architecture

## Overview

The security architecture for the GDD Timing System is designed using the Onion Layer Model, where each layer represents a distinct level of security. This layered approach ensures that the system is robust, resilient, and capable of mitigating risks. Below is an explanation of the layers, starting from the outermost layer.


## Layer 1: Network Security

The outermost layer focuses on securing the network infrastructure. This includes:

- **Virtual Private Cloud (VPC):** The system operates within a dedicated AWS VPC to isolate resources from external networks.
- **Subnets:** A public subnet is configured to allow controlled access to resources. This approach was chosen for simplicity while maintaining adequate security through other measures like security groups, application-level restrictions, and containerization. Future iterations may implement private subnets for enhanced isolation if requirements change.
- **Internet Gateway:** An internet gateway is used to enable controlled access to the internet for public-facing resources.
- **Route Tables:** Custom route tables ensure that traffic is routed securely within the VPC.
- **Security Groups:** Security groups act as virtual firewalls, controlling inbound and outbound traffic. For example:
  - HTTP access is currently allowed from any IP, with security implemented at the application level through Nginx.
- **SSH Access:** SSH keys for EC2 access are managed securely without hardcoding sensitive information in the configuration. SSH access is limited to trusted IPs defined in `var.ssh_allowed_ips`.



## Layer 2: Compute Security

This layer secures the compute resources, primarily the EC2 instances:

- **IAM Instance Profiles:** EC2 instances are assigned IAM roles with minimal permissions required for their operation.
- **Key Pair Authentication:** SSH access to instances is secured using key pairs. Only the public key is referenced in Terraform configurations, while the private key is managed securely outside of the infrastructure code.
- **User Data Scripts:** EC2 instances are bootstrapped using secure scripts (`ec2-setup.tpl`) that:
  - Install necessary packages.
  - Configure Docker and Docker Compose.
  - Fetch secrets securely from AWS Systems Manager Parameter Store.
  - Ensure sensitive files (e.g., `.env`) are shredded after use.



## Layer 3: Application Security

The application layer focuses on securing the services running within the system:

- **Dockerized Services:** All services (e.g., FastAPI, Streamlit, Airflow) are containerized using Docker, ensuring isolation and consistency. Services communicate via an internal Docker network that's not directly accessible from outside.
- **Environment Variables:** Sensitive data (e.g., database credentials, API keys) is passed securely via environment variables.
- **Nginx Reverse Proxy:** Nginx acts as a security boundary, providing an additional layer between external traffic and the API service by enforcing access control and securing communication between services. For example:
  - Admin interfaces (e.g., Airflow, MinIO Console) are restricted to specific IPs using `NGINX_ALLOWED_ADMIN_IP_1` and `NGINX_ALLOWED_ADMIN_IP_2`.
  - WebSocket connections are explicitly supported and secured.
  ### API Security

  The FastAPI application implements several security measures:

  - **Input Validation:** API endpoints validate input data using FastAPI's Query parameters with type checking and validation rules to prevent injection attacks and ensure data integrity.
  - **Error Handling:** Comprehensive error handling with appropriate HTTP status codes (400, 404, 500) ensures proper client feedback without exposing internal system details.
  - **Structured Logging:** API operations and errors are logged with contextual information for diagnostic and audit purposes, capturing:
    - Error conditions with full stack traces.
    - Request processing information.
    - S3/MinIO connection issues.
    - Data processing errors.
  - **Service Isolation:** The API service runs in its own Docker container, isolated from other components to minimize the impact of potential vulnerabilities.
  - **Controlled Data Access:** API endpoints access data from the object storage (S3/MinIO) using carefully scoped permissions.


## Layer 4: Data Security

The innermost layer focuses on securing data storage and access:

- **AWS S3 Buckets:** Data is stored in S3 buckets with strict access controls in production:
  - Public access is blocked using `aws_s3_bucket_public_access_block`.
  - Buckets are tagged for traceability and auditing.
- **MinIO:** MinIO is used as an object storage solution primarily for local development, with access credentials secured and managed through environment variables. The infrastructure includes commented provisions for MinIO in production if needed as an alternative.
- **Database Security:** PostgreSQL is configured with username/password authentication, with credentials managed through environment variables. Data persistence is handled through Docker volumes, with network isolation provided by the container networking configuration. The PostgreSQL instance is used primarily for storing Airflow metadata only, not application data, which minimizes the risk profile of the database.


## Additional Security Measures

- **Monitoring and Logging:**
  - **Infrastructure Logging:** AWS CloudTrail tracks API calls and changes to the AWS environment.
  - **Application Logging:**
    - Terraform user data script output is logged to `/var/log/user-data.log` and system journal.
    - Docker container logs are accessible via `docker-compose logs`.
    - All bootstrap operations are logged with timestamps.
  - **Planned CloudWatch Integration:**
    - AWS CloudWatch will be configured for EC2 instance monitoring.
    - Docker container logs will be forwarded to CloudWatch Logs.
    - User data script logs will be streamed to CloudWatch Logs using CloudWatch agent where possible.
- **Health Checks:** Services are monitored using health checks to ensure availability and detect anomalies.
- **Dependency Management:** Terraform ensures that all dependencies (e.g., AWS resources) are managed securely and consistently.
- **IAM Policies:** All policies adhere to the principle of least privilege, with IAM roles and permissions managed separately from infrastructure code.


## Security Standards and Compliance

For future security enhancements and audits, the [OWASP Application Security Verification Standard (ASVS)](https://owasp.org/www-project-application-security-verification-standard/) should be used as a reference framework. ASVS provides a basis for testing web application technical security controls and offers requirements for secure development.

Key ASVS verification levels to consider:

- **Level 1:** Basic application security verification suitable for most applications.
- **Level 2:** Applications containing sensitive data requiring additional protection.
- **Level 3:** High-value applications, applications processing sensitive data, or applications requiring high levels of trust.

The ASVS framework should be consulted during security reviews and when implementing future security enhancements to ensure comprehensive coverage of security controls.

## Related Documentation

For more information on specific aspects of the architecture, refer to the following documentation:

- [System Architecture](./system-architecture.md) - Overall system design and component interactions.
- [Data Flow and Modeling](./data-flow-and-modeling.md) - Information on data processing and storage.
- [API Documentation](./api-documentation.md) - API endpoint specifications and usage.
- [Yr.no API Compliance](./yrno-api-compliance.md) - Compliance with the Yr.no Weather API terms of service.
- [AWS Services](./aws-services.md) - Details on AWS infrastructure and IAM configurations.
- [Containerisation](./containerisation.md) - Information on Docker container security and isolation.
- [Reverse Proxy](./reverse-proxy.md) - Details on Nginx configuration and access controls.
- [Security Architecture](./security-architecture.md) - Overview of the security measures and design.
- [Testing Plan](./testing-plan.md) - Outline of the testing strategy, including security testing.

These documents provide further context and detail on implementation throughout the system.
