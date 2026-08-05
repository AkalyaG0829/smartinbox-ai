# Disaster Recovery Validation Procedure

This document provides a manual Disaster Recovery (DR) validation procedure for SmartInbox AI.

## SLA & Architecture Guarantees
- **RPO (Recovery Point Objective)**:
  - **PostgreSQL**: Dependent on external backup infrastructure (e.g., hourly WAL archiving implies ~1 hour max RPO).
  - **Redis (Celery Broker)**: ~1 second (due to `appendonly yes` fsync interval).
- **RTO (Recovery Time Objective)**:
  - Estimated at ~15-30 minutes for a complete infrastructure rebuild from code + snapshots, depending on database size.
- **Current Guarantees**:
  - Celery unacknowledged tasks (`late_ack=True`) are preserved and re-delivered if a worker crashes before completion.
  - Redis broker recovers queues across container restarts via AOF.
- **Not Guaranteed**:
  - Absolute Zero-Data-Loss for Redis enqueues due to the 1-second AOF fsync interval. If Redis hard-crashes exactly during a fast enqueue burst, sub-second enqueues might drop.
  - Automated database snapshotting (this remains an infrastructure/cloud responsibility).

## 1. PostgreSQL Recovery Validation
**Objective**: Verify backup → restore → migration verification → application verification.

1. **Backup**:
   ```bash
   docker exec -t smartinbox_db pg_dump -U $POSTGRES_USER -Fc $POSTGRES_DB > backup.dump
   ```
2. **Destroy**:
   ```bash
   docker-compose stop db backend ml_worker routing_worker
   docker-compose rm -f db
   docker volume rm smartinbox-ai_postgres_data
   ```
3. **Restore**:
   ```bash
   # Start DB only
   docker-compose up -d db
   # Wait for health check, then restore
   docker exec -i smartinbox_db pg_restore -U $POSTGRES_USER -d $POSTGRES_DB -1 < backup.dump
   ```
4. **Application Verification**:
   ```bash
   # Start stack, ensuring the migrator runs safely
   docker-compose up -d
   ```
   *Verify API traffic responds with 200 OK and historical data exists.*

## 2. Redis Persistence Validation
**Objective**: Verify AOF persistence → controlled restart → Celery queue recovery.

1. **Enqueue Tasks**: Send a large batch of async processing requests.
2. **Controlled Crash**:
   ```bash
   docker kill -s SIGKILL smartinbox_redis
   ```
3. **Recovery Verification**:
   ```bash
   docker-compose start redis
   ```
   *Check Celery worker logs. The workers should automatically backoff, reconnect, and process the exact number of enqueued tasks.*

## 3. Celery Idempotency & Late ACK Validation
**Objective**: Verify worker crash → late ACK redelivery → idempotency → DLQ/replay.

1. **Simulate Crash**: While an ML worker is processing a heavy embedding task, kill the container:
   ```bash
   docker kill -s SIGKILL smartinbox_ml_worker
   ```
2. **Redelivery Verification**: Restart the worker:
   ```bash
   docker-compose start ml_worker
   ```
   *The broker must re-deliver the aborted task. The application logic must process the duplicated task harmlessly (idempotency).*
3. **DLQ Validation**: Cause a task to permanently fail (e.g., invalid data) and verify it correctly enters the `FailedTaskLog` with sanitized payloads. Test the `/api/v1/tasks/dlq/{log_id}/replay` endpoint.

## 4. Application Container Failover
**Objective**: Verify container restart → health check → traffic recovery.

1. **Restart Backend**:
   ```bash
   docker-compose restart backend
   ```
2. **Verify Traffic**: Load balancer / API should briefly return 5xx and then recover as soon as the `/health` endpoint reports healthy.
