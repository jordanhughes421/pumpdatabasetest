# Production Runbook

This runbook describes how to deploy the application in a production environment (e.g., AWS Lightsail) using Docker Compose.

## Architecture

*   **Reverse Proxy (Nginx)**: Serves the React frontend (SPA) and proxies API requests to the backend. Exposed on ports 80 and 443.
*   **Backend (FastAPI)**: Runs the application logic. Not exposed publicly; only accessible via the reverse proxy.

## Prerequisites

*   Docker and Docker Compose installed on the host.
*   Git to clone the repository.

## Starting Production

1.  **Clone the repository:**
    ```bash
    git clone <repo_url>
    cd <repo_directory>
    ```

2.  **Configure Environment:**
    Copy `.env.example` to `.env` (optional, as defaults are set in compose file, but good practice).
    ```bash
    cp .env.example .env
    ```

3.  **Start Services:**
    Use the production compose file to build and start the services.
    ```bash
    docker compose -f docker-compose.prod.yml up -d --build
    ```

4.  **Verify Deployment:**
    *   Visit `http://<your-domain-or-ip>/` to see the application.
    *   Visit `http://<your-domain-or-ip>/api/health` (or a known endpoint like `/api/`) to verify backend connectivity.

## Ports

| Service       | Internal Port | External Port | Description |
| :---          | :---          | :---          | :---        |
| reverse-proxy | 80            | 80            | HTTP        |
| reverse-proxy | 443           | 443           | HTTPS       |
| backend       | 8000          | -             | Internal API|

## Persistent Data

*   **Database**: The SQLite database is stored in a volume mapped to `./backend_data` on the host. Ensure this directory is backed up.
    *   Host path: `./backend_data`
    *   Container path: `/app/backend_data`
    *   Environment Variable: `SQLITE_DB_PATH` controls the location inside the container.

## Enabling HTTPS on Lightsail

To enable HTTPS, you generally have two options:

1.  **Use a Lightsail Load Balancer (Recommended for ease)**:
    *   Attach a Lightsail Load Balancer to your instance.
    *   Configure the Load Balancer to handle SSL/TLS (create/attach certificate).
    *   Traffic will reach your Nginx container on port 80 (HTTP) from the Load Balancer.

2.  **Certbot / Let's Encrypt (Self-managed)**:
    *   Install Certbot on the host or use a sidecar container.
    *   Mount the certificates into the `reverse-proxy` container.
    *   Update `nginx/default.conf` to listen on 443 ssl and point to the certificate files.
    *   Example Nginx config snippet:
        ```nginx
        server {
            listen 443 ssl;
            ssl_certificate /etc/nginx/certs/fullchain.pem;
            ssl_certificate_key /etc/nginx/certs/privkey.pem;
            ...
        }
        ```
