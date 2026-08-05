# Phase 5 Alerting and CI/CD Documentation

## Available Alerts
The following alerts are configured in `docker/prometheus/alert.rules.yml` to trigger in Alertmanager:

1. **HighAPI5xxErrorRate (Critical)**
   - **Meaning**: More than 5% of API requests return HTTP 5xx errors over a 5-minute rolling window.
2. **HighAPILatency (Warning)**
   - **Meaning**: The 99th percentile (P99) response time for API requests exceeds 2.0 seconds over 5 minutes.
3. **HighMLQueueBacklog (Warning)**
   - **Meaning**: More than 100 pending tasks are stuck in the `ml_queue`.
4. **HighRoutingQueueBacklog (Warning)**
   - **Meaning**: More than 100 pending tasks are stuck in the `routing_queue`.
5. **DLQSpike (Critical)**
   - **Meaning**: Celery tasks are actively failing beyond their retry limits and entering the Dead Letter Queue.
6. **WorkerDown (Critical)**
   - **Meaning**: Prometheus cannot scrape the `celery_exporter`. This indicates Celery brokers or workers might be crashed.
7. **BackendDown (Critical)**
   - **Meaning**: Prometheus cannot scrape the backend `/metrics` endpoint. The FastAPI instance might be down.

## Required Production Notification Secrets
By default, Alertmanager requires an incoming Slack webhook. 
You must configure the `slack_api_url` in `docker/alertmanager/alertmanager.yml`.
**IMPORTANT**: Never commit the actual Slack Webhook URL. It must be provided at deployment time via a templated configuration or environment variable injection (e.g., in a CI/CD deployment script, Kubernetes secret, or Vault).

## How to Configure Alertmanager
1. Mount your actual secrets into the Alertmanager container via a volume or inject them before building.
2. The current `docker/alertmanager/alertmanager.yml` uses placeholders (e.g., `XXXXXXXXXXXXXXXXXXXXXXXX`). 
3. The routing categorizes alerts by `severity`. Warnings go to the standard `#smartinbox-alerts` channel, while Critical alerts go to `#smartinbox-critical`.

## How Docker Images Are Published
The GitHub Actions pipeline (`.github/workflows/ci.yml`) uses the `docker/build-push-action` to automatically build and push the Docker image.
1. **Pull Requests**: The workflow will only run `pytest` regression tests. No images are built.
2. **Push to `main`**: The workflow runs tests. If tests pass, it logs into the GitHub Container Registry (GHCR) using the implicit `GITHUB_TOKEN`. 
3. **Tags**: It pushes the image tagged with `latest`, the `main` branch name, and an immutable Git commit SHA. No hardcoded DockerHub passwords are used.

## Manual Stack Validation
To validate the stack on a Docker-enabled host:
1. Provide a `.env` file with database credentials.
2. Run `docker-compose up -d`.
3. Verify that `docker-compose ps` shows `backend`, `ml_worker`, `routing_worker`, `migrator`, `celery_exporter`, `prometheus`, `grafana`, and `alertmanager`.
4. Test that `http://localhost:9090` (Prometheus) shows the alert rules loaded under "Alerts".
5. Run the load test `k6 run scripts/load_test.js` to trigger latency or backlog alerts, and check Alertmanager.
