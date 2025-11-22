# Production Deployment Guide

This guide outlines the steps to deploy the Trading Signal Analyzer to a production environment.

## 1. Prerequisites

*   **Docker and Docker Compose:** Ensure you have Docker and Docker Compose installed on your production server.
*   **Reverse Proxy:** You will need a reverse proxy (e.g., Nginx, Apache, or a cloud provider's load balancer) to route traffic to the application.

## 2. Configuration

### Backend

The backend is configured using environment variables in the `docker-compose.yml` file. No further configuration is required.

### Frontend

The frontend is configured to be served from the same domain as the backend. The API requests are proxied to the backend via a reverse proxy.

## 3. Building and Running the Application

To build and run the application, use the following command:

```bash
docker-compose up --build -d
```

This will build the Docker images and start the backend and frontend services in detached mode.

## 4. Reverse Proxy Configuration

You need to configure your reverse proxy to:

1.  Serve the frontend's static files.
2.  Route all requests to `/api` to the backend service on port 5000.

Here is an example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        # Assuming you have a mechanism to serve the frontend build from here
        # This could be a volume mount or a separate container
        root   /path/to/your/frontend/build;
        index  index.html;
        try_files $uri /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 5. Deployment complete

Once you have configured your reverse proxy, the application will be accessible at your domain.
