# SmartInbox AI — Phase 1 Local Foundation

This is the production-grade, modular monolith implementation of **SmartInbox AI** (Phase 1). It defines the backend layout, SQLAlchemy models, abstract provider interfaces, and regression tests verifying 100% parity against the HackerRank prototype results.

---

## Project Structure

```
D:\Projects\smartinbox-ai\
├── docker-compose.yml           # Composition file (PostgreSQL + Redis + FastAPI + Celery)
├── requirements.txt             # Python project dependencies
├── .env                         # Local runtime environment secrets (configured for stub providers)
├── .env.example                 # Example variables template
├── docker/
│   ├── postgres/
│   │   └── init.sql             # DB setup (registers PGVector extension)
│   └── backend/
│       └── Dockerfile           # Backend container specification
├── src/
│   ├── main.py                  # FastAPI Application gateway and startup lifespans
│   ├── worker.py                # Celery worker queues and tasks definitions
│   ├── config/
│   │   └── settings.py          # App settings validation (using Pydantic-Settings)
│   ├── database/
│   │   └── session.py           # Database connection engines and session hooks
│   ├── domain/
│   │   ├── rules.py             # Ported & verified classification heuristics & thresholds
│   │   └── interfaces.py        # Abstract interfaces (STT, OCR, Embedding, InjectionShield)
│   ├── application/
│   │   └── pipeline.py          # Decoupled message routing pipeline (resolves db transactions)
│   └── infrastructure/
│       ├── models.py            # SQLAlchemy relational tables
│       └── providers/
│           └── mock_providers.py # Offline-friendly local stub implementations
└── tests/
    ├── conftest.py              # SQLite mock fixtures and HTTP Client configurations
    ├── unit/
    │   └── test_api.py          # Endpoint checks (/health and message routing validations)
    └── regression/
        ├── dataset/             # Parity verification datasets (copied from prototype)
        └── test_parity.py       # Core routing engine parity regression verification (110 messages)
```

---

## Local Development Setup

### 1. Pre-requisites
Ensure you have Python 3.10+ installed.

### 2. Installation
Install the project dependencies locally:
```bash
pip install -r requirements.txt
```

### 3. Run the Test Suite
Validate the entire backend routing pipeline and confirm 100% regression parity against the prototype outputs:
```bash
python -m pytest
```

---

## Running with Docker Compose

Once Docker/Docker Desktop is installed and running on your system, you can spin up the full infrastructure stack (FastAPI Backend, Celery Worker, Redis Cache, and PostgreSQL database with PGVector support):

```bash
# Build and launch all services in the background
docker compose up --build -d

# Verify all services are running and healthy
docker compose ps

# Inspect logs from the backend server
docker compose logs backend -f
```

---

## API Boundaries

### System Health
- **URL**: `GET /health`
- **Output**: Returns details on database connectivity, active environment status, and provider setups.

### Ingest Message Route
- **URL**: `POST /api/v1/messages/route`
- **Body**:
  ```json
  {
    "message_id": "test_msg_001",
    "user_id": "u_001",
    "conversation_type": "personal",
    "sender_user_id": "u_002",
    "created_at": "2026-07-30 22:19:00",
    "message_text": "Good morning!",
    "media_type": "none",
    "forwarded_count": 0
  }
  ```
- **Response**:
  ```json
  {
    "action": "digest",
    "message_type": "greeting",
    "reason": "Low-priority message or general communication, suitable for later reading.",
    "confidence": 0.82,
    "evidence_message_ids": "none"
  }
  ```
