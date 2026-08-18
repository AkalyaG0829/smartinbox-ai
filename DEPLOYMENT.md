# SmartInbox Production Deployment Guide

This guide details how to deploy the SmartInbox AI architecture in a production cloud environment. 

## 1. Required Cloud Services
To run SmartInbox in production, you will need:
- **Compute Instance**: A VM (e.g. AWS EC2, DigitalOcean Droplet) with at least 4GB RAM and 2 vCPUs to comfortably run Docker Compose, the embedding models, and PostgreSQL.
- **Docker & Docker Compose**: Ensure Docker Engine and the Compose plugin are installed on the target machine.
- **Domain Name (Optional but Recommended)**: To serve the frontend and backend over HTTPS via a reverse proxy.

## 2. Required Environment Variables
Create a `.env` file on the production server from the `.env.example` template. Never commit this file.

### Required Variables:
- `DATABASE_URL`: Connection string to PostgreSQL (e.g., `postgresql://user:password@db:5432/smartinbox_db`)
- `REDIS_URL`: Connection string to Redis (e.g., `redis://redis:6379/0`)
- `API_KEY`: A strong, randomly generated string for backend authentication. Do not leave blank.
- `CORS_ORIGINS`: Comma-separated list of allowed origins (e.g., `https://yourdomain.com`).
- `ENVIRONMENT`: Set to `production`.

### PostgreSQL Database Settings:
- `POSTGRES_USER`: Database user.
- `POSTGRES_PASSWORD`: Secure database password.
- `POSTGRES_DB`: Database name.

### Optional AI Provider Settings:
- If using cloud providers instead of local execution, set `SPEECH_TO_TEXT_PROVIDER=cloud`, `OCR_PROVIDER=cloud`, or `EMBEDDING_PROVIDER=cloud` and provide `OPENAI_API_KEY` or `GEMINI_API_KEY`.

## 3. PostgreSQL + pgvector Setup
The application uses the `ankane/pgvector` Docker image to enable the vector extension required for semantic embeddings. Data is persisted in the `postgres_data` Docker volume. Ensure you do not arbitrarily delete this volume to avoid data loss.

Initialization occurs automatically via `docker/postgres/init.sql`. The `migrator` service runs `alembic upgrade head` on startup to ensure the database schema is up-to-date.

## 4. Redis Setup
Redis acts as the Celery message broker and rate limiter backend. It runs as a container using the official Alpine image. Data is persisted in the `redis_data` volume.

## 5. Backend Deployment
The FastAPI backend is built via `docker/backend/Dockerfile`. In production, it runs using `uvicorn` bounded to `0.0.0.0:8000`. It depends on the successful completion of the Alembic migrations and the availability of Redis.

## 6. Celery Worker Deployment
Two Celery workers (`ml_worker` and `routing_worker`) run alongside the backend to process intensive machine learning and routing tasks asynchronously. The Dead Letter Queue (DLQ) feature remains fully functional.

## 7. Frontend Deployment
The Vite/React SPA is built using a multi-stage Dockerfile (`docker/frontend/Dockerfile.prod`). It compiles the static assets and serves them via a lightweight Nginx container, eliminating the need for the Vite development server in production.

## 8. CORS Configuration
CORS is strictly managed. Specify the public URL of your frontend in the `CORS_ORIGINS` environment variable to ensure secure communication with the backend.

## 9. Domain Configuration
To secure traffic, it is recommended to place the entire `docker-compose.production.yml` stack behind an HTTPS reverse proxy (like Nginx, Traefik, or Caddy) listening on ports 80/443. Route traffic to port `5173` (mapped to Nginx) for the frontend and `8000` for the backend.

## 10. Health Checks
The backend exposes a comprehensive health check at `/health` verifying connectivity to the database, Redis, and pgvector extension. Docker natively integrates with these checks to auto-restart unhealthy components.

## 11. Monitoring
Prometheus and Grafana are included in the compose file. 
> [!IMPORTANT]
> Keep the Prometheus and Grafana ports private unless specifically secured. For a portfolio deployment, avoid exposing port `3000` to the internet without a reverse proxy enforcing authentication.

## 12. Security Considerations
- **No API Keys in Frontend**: The production frontend communicates with the backend's `/api/v1/messages/demo` endpoint, which relies on strict rate-limiting instead of the master API key.
- **Fail-fast**: Hardcoded mock credentials have been removed. The backend will refuse to start if critical environment variables are missing.

## 13. Troubleshooting
- Check container logs: `docker compose -f docker-compose.production.yml logs backend`
- Rebuild containers: `docker compose -f docker-compose.production.yml build --no-cache`

## 14. Rollback Procedure
If a deployment fails, you can roll back to the previous image by specifying the exact commit hash in your compose file or reverting your Git branch and re-running `docker compose up -d --build`. Always back up the `postgres_data` volume before major schema migrations.
