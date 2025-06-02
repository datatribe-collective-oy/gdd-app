# Nginx

This document outlines the Nginx configuration used as a reverse proxy for the GDD (Growing Degree Days) application stack. Nginx listens for incoming HTTP traffic and routes it to the appropriate backend services: Streamlit, FastAPI, Airflow, and MinIO.

## Configuration File: `nginx.conf.template`

The primary Nginx configuration is managed through a template file located at `nginx/nginx.conf.template`. This template is processed at container startup to inject environment-specific variables, such as like allowed IP addresses.

### Server Block

The main server block defines how Nginx handles incoming requests:

```nginx
server {
    listen 80;
    server_name _;
    # server_name localhost;
    # ... location blocks ...
}
```

- **`listen 80;`**: Nginx listens on port 80 for standard HTTP traffic.
- **`server_name _;`**: This makes the server block the default handler for any requests to the server's IP address on port 80 that don't match a more specific `server_name`.

### Location Blocks

#### 1. Streamlit Application (`location /`)

This block routes traffic to the Streamlit frontend application.

```nginx
    location / {
        proxy_pass http://streamlit:8501/;
        proxy_http_version 1.1; # Explicitly use HTTP/1.1 for upstream
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        # Increase timeouts for WebSocket connections
        proxy_read_timeout 100s;
        proxy_send_timeout 100s;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Cache control headers
        add_header Cache-Control 'no-cache, no-store, must-revalidate, proxy-revalidate';
        add_header Pragma 'no-cache'; # HTTP/1.0 backward compatibility
        add_header Expires '0'; # Proxies
    }
```

- **`proxy_pass http://streamlit:8501/;`**: Forwards requests to the Streamlit service.
- **WebSocket Support**: `proxy_http_version 1.1;`, `proxy_set_header Upgrade $http_upgrade;`, and `proxy_set_header Connection "upgrade";` are essential for enabling WebSocket connections, which Streamlit relies on for interactivity.
- **Timeouts**: `proxy_read_timeout 100s;` and `proxy_send_timeout 100s;` prevent Nginx from prematurely closing WebSocket connections during periods of inactivity.
- **Client Headers**: `Host`, `X-Real-IP`, `X-Forwarded-For`, and `X-Forwarded-Proto` headers are passed to provide the Streamlit backend with information about the original client request.
- **Cache Control**: `Cache-Control`, `Pragma`, and `Expires` headers are set to instruct browsers to always revalidate resources, preventing issues with stale cached content for this dynamic application.

#### 2. FastAPI Application (`location /api/`)

This block routes traffic to the FastAPI backend.

```nginx
    location /api/ {
        proxy_pass http://fastapi:8000/;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
```

- **`proxy_pass http://fastapi:8000/;`**: Forwards requests to the FastAPI service.
- **WebSocket Support**: `proxy_http_version 1.1;`, `proxy_set_header Upgrade $http_upgrade;`, and `proxy_set_header Connection "upgrade";` enable WebSocket connections, allowing FastAPI to handle real-time features seamlessly.
- **Client Headers**: `Host`, `X-Real-IP`, `X-Forwarded-For`, and `X-Forwarded-Proto` headers are passed to provide the FastAPI backend with information about the original client request.

#### 3. Airflow Webserver (`location /airflow/`)

This block routes traffic to the Airflow web UI while implementing strict IP-based access control to protect the administrative interface:

```nginx
    location /airflow/ {
        allow ${NGINX_ALLOWED_ADMIN_IP_1};
        allow ${NGINX_ALLOWED_ADMIN_IP_2};
        deny all;
        proxy_pass http://airflow-webserver:8080/;
        # ... standard proxy headers ...
    }
```

- **Access Control**: `allow ${NGINX_ALLOWED_ADMIN_IP_1};`, `allow ${NGINX_ALLOWED_ADMIN_IP_2};`, and `deny all;` restrict access to the Airflow UI to specified IP addresses. These IP addresses are injected at runtime.
- **`proxy_pass http://airflow-webserver:8080/;`**: Forwards requests to the Airflow webserver.

#### 4. MinIO Console (`location /minio-console/`)

This block routes traffic to the MinIO web console, also with IP-based access control.

```nginx
    location /minio-console/ {
        allow ${NGINX_ALLOWED_ADMIN_IP_1};
        allow ${NGINX_ALLOWED_ADMIN_IP_2};
        deny all;
        proxy_pass http://minio:9001/;
        # ... standard proxy headers ...
        proxy_set_header X-Minio-Original-Host $http_host;
    }
```

- **Access Control**: Similar IP whitelisting as for Airflow.
- **`proxy_pass http://minio:9001/;`**: Forwards requests to the MinIO console.
- **`proxy_set_header X-Minio-Original-Host $http_host;`**: This header ensures that MinIO correctly identifies the original host requested by the client. When MinIO is accessed via a reverse proxy, it requires this header to properly handle requests and generate URLs that match the original host, avoiding issues with incorrect redirects or resource links.

## Dynamic Configuration with `Dockerfile.nginx`

The `Dockerfile.nginx` handles the dynamic substitution of IP addresses for access control:

```dockerfile
ENTRYPOINT [ "sh", "-c" ]
CMD ["envsubst '$$NGINX_ALLOWED_ADMIN_IP_1 $$NGINX_ALLOWED_ADMIN_IP_2' \
     < /etc/nginx/templates/nginx.conf.template \
     > /etc/nginx/conf.d/default.conf \
   && exec nginx -g 'daemon off;'"]
```

- At container startup, `envsubst` replaces the placeholders `$$NGINX_ALLOWED_ADMIN_IP_1` and `$$NGINX_ALLOWED_ADMIN_IP_2` in `nginx.conf.template` with values from the environment variables `NGINX_ALLOWED_ADMIN_IP_1` and `NGINX_ALLOWED_ADMIN_IP_2`.
- The resulting configuration is written to `/etc/nginx/conf.d/default.conf`, which Nginx then loads.
- This allows for flexible IP whitelisting for administrative interfaces (Airflow, MinIO) without modifying the core Nginx configuration template directly. These environment variables are set in the `docker-compose.yaml` file and values are sourced from an `.env` file.
