# Containerisation

## Overview

The GDD Timing System application uses Docker containers to package and deploy its various components. This containerized approach provides consistency across development and production environments, simplifies dependency management, and enables easy deployment of the complete system.

## Container Architecture

The application is composed of the following containers:

1. **NGINX** - Reverse proxy and web server
2. **FastAPI** - Backend API service
3. **Streamlit** - Frontend user interface
4. **Airflow** - Workflow orchestration for data processing
5. **MinIO** - S3-compatible object storage service (included in the local `docker-compose` setup)

Most of these containers are defined in individual Dockerfiles, and all are managed and orchestrated using Docker Compose.

## Container Details

### NGINX Container

**Dockerfile**: [`Dockerfile.nginx`](../Dockerfile.nginx)

**Purpose**:

- Acts as a reverse proxy for all services.
- Controls access to admin interfaces.

**Key Features**:

- Based on nginx:1.28.
- Uses environment variable substitution for IP-based access control.
- Routes traffic to the appropriate service based on URL path.

**Configuration**:

- Main config template: `nginx/nginx.conf.template`.
- NGINX listens on port **80** (default HTTP) and proxies requests to backend services.
- Routes:
  - `/` → Streamlit UI (proxied to port 8501).
  - `/api/` → FastAPI backend (proxied to port 8000).
  - `/airflow/` → Airflow webserver (proxied to port 8080) - IP restricted.
  - `/minio-console/` → MinIO console (proxied to port 9001) - IP restricted.

### FastAPI Container

**Dockerfile**: [`Dockerfile.fastapi`](../Dockerfile.fastapi)

**Purpose**:

- Provides REST API endpoints for the application.
- Handles data processing requests.
- Interfaces with the data storage layer.

**Key Features**:

- Based on python:3.11-slim.
- Exposes port 8000.
- Installs the application and its dependencies from pyproject.toml.

**Components**:

- Main API module: `/app/api_service/main.py`.
- Universal module for shared functionality.
- Data fetcher and GDD counter modules.

### Streamlit Container

**Dockerfile**: [`Dockerfile.streamlit`](../Dockerfile.streamlit)

**Purpose**:

- Provides the web-based user interface.
- Visualizes GDD data and predictions.
- Enables user interaction with the system.

**Key Features**:

- Based on python:3.11-slim.
- Exposes port 8501.
- Installs the application and its dependencies from pyproject.toml.

**Components**:

- Main Streamlit app: `/app/scripts/streamlit_app.py`.

### Airflow Container

**Dockerfile**: [`Dockerfile.airflow`](../Dockerfile.airflow)

**Purpose**:

- Orchestrates data fetching and processing workflows.
- Manages and logs the ETL pipeline runs.

**Key Features**:

- Based on apache/airflow:2.8.2-python3.11.
- Installs the application and its dependencies from pyproject.toml.

**Components**:

- DAG definitions in `/opt/airflow/dags/`.
- Initialization script: `init-airflow.sh`.
- Makefile for aiding common operations in DAG orchestration.

### MinIO Container

**Image**: `minio/minio:RELEASE.2025-05-24T17-08-30Z`

**Purpose**:

- Provides an S3-compatible object storage service.
- Used locally for storing raw weather data fetched by Airflow DAGs.

**Key Features**:

- Exposes port 9000 for the S3 API and port 9001 for the MinIO web console.
- Data is persisted in the `minio_data` Docker volume, mounted at `/data` inside the container.
- Configured with user credentials and a default bucket via environment variables.
- Includes a healthcheck to ensure the service is ready before dependent services start.

**Configuration (from `docker-compose.yaml`):**

- **Ports**:
    - API: `${MINIO_API_PORT_E:-9000}` (host) to `9000` (container)
    - Console: `${MINIO_CONSOLE_PORT_E:-9001}` (host) to `9001` (container)
- **Environment Variables**:
    - `MINIO_ROOT_USER`: Populated by the `${MINIO_ACCESS_KEY}` environment variable; serves as the access key for MinIO.
    - `MINIO_ROOT_PASSWORD`: Populated by the `${MINIO_SECRET_KEY}` environment variable; serves as the secret key for MinIO.
    - `MINIO_DEFAULT_BUCKETS`: Populated by the `${MINIO_DATA_BUCKET_NAME}` environment variable; specifies the bucket to be used for storing data.
- **Command**: `server /data --console-address ":9001"` - Starts the MinIO server, serving data from the `/data` directory and making the console available on port 9001.
- **Healthcheck**: Uses `mc ready local` to verify service availability.

## Environment Variables

The containers rely on environment variables for configuration, which provided through Docker Compose:

- `NGINX_ALLOWED_ADMIN_IP_1`, `NGINX_ALLOWED_ADMIN_IP_2`: IP addresses allowed to access admin interfaces.
- Database credentials (for PostgreSQL).
- Airflow configuration.
- Storage backend configuration (S3 or MinIO).

## Internal Communication Network

All services within the Docker Compose setup are connected to a custom bridge network named `gdd_internal`.

**Key Features**:

- **Service Discovery**: Containers can discover and communicate with each other using their service names as hostnames (e.g., `postgres`, `fastapi`, `minio`).
- **Isolation**: This network isolates the application's containers from other Docker networks or the host machine's network, enhancing security and organization.
- **Defined in `docker-compose.yaml`**: The network `gdd_internal_net` is explicitly defined with the `bridge` driver.

## Healthchecks

To ensure services start in the correct order and are operational, `docker-compose.yaml` defines healthchecks for critical services:

- **PostgreSQL (`postgres`)**: Uses `pg_isready` to verify that the database server is up and ready to accept connections. Airflow services depend on this healthcheck passing before they start.
- **MinIO (`minio`)**: Uses `mc ready local` to check if the MinIO server is operational and ready to serve requests.

Services like `airflow-init`, `airflow-webserver`, and `airflow-scheduler` have `depends_on` clauses with `condition: service_healthy` for `postgres`, ensuring the database is available before Airflow attempts to connect. The `airflow-init` service also has a `condition: service_completed_successfully` dependency, ensuring database migrations and user creation are done before the main Airflow components start.

## Security Considerations

- Admin interfaces (Airflow, MinIO) are IP-restricted through NGINX configuration.
- Application containers (FastAPI, Streamlit, Airflow) and service containers (PostgreSQL, MinIO) run as non-root users. The NGINX master process runs as root as required, while worker processes run with lower privileges.
- The application's code and dependencies are installed from known sources.
- Minimized attack surface: Dockerfiles are structured to copy only necessary files into the images, but more optimisation development can be done to further reduce the image size and attack surface.
- Principle of Least Privilege: Efforts are made to ensure containers operate with only the permissions necessary for their function. This includes running processes as non-root users and isolating network traffic.

## Development vs. Production

In development:

- All containers run on a single host.
- Volume mounts are used for rapid development.

In production:

- Secrets are being managed securely through AWS Parameter Store.
- Container resource limits should be set.

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
