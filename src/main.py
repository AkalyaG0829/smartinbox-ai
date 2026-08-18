import time
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import Dict, Any
from celery.result import AsyncResult
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid
import logging
import contextvars

# Logging and Correlation ID setup
correlation_id_var = contextvars.ContextVar("correlation_id", default="-")

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id_var.get()
        return True

logger = logging.getLogger("smartinbox")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "message": "%(message)s"}'))
logger.addHandler(handler)
logger.addFilter(CorrelationIdFilter())

# API Key Dependency
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key_header: str = Depends(api_key_header)):
    if not api_key_header or api_key_header != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    return api_key_header

from src.config.settings import settings

# Rate Limiter setup
limiter_storage = "memory://" if settings.ENVIRONMENT == "test" else settings.REDIS_URL
limiter = Limiter(key_func=get_remote_address, storage_uri=limiter_storage)
from src.database.session import engine, Base, get_db
from src.infrastructure.providers.mock_providers import (
    MockSpeechToTextProvider,
    MockOCRProvider,
    LocalPromptInjectionShield
)
from src.infrastructure.providers.sentence_transformer_provider import SentenceTransformersEmbeddingProvider
from src.application.pipeline import MessageRoutingPipeline
from src.application.schemas import MessageProcessingRequest, MessageProcessingResult, UserInteractionRequest
from src.worker import celery_app, process_message_async

# LIFESPAN - Create database schemas upon initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly warm up the embedding model during startup
    try:
        emb_prov.warmup()
    except Exception as e:
        print(f"Eager embedding model warmup failed: {e}")

    yield

app = FastAPI(
    title="SmartInbox AI Backend Monolith",
    description="Intelligent context-aware message notification router.",
    version="2.1.0",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware

cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add Rate Limiter Exception Handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        correlation_id_var.set(correlation_id)

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

app.add_middleware(CorrelationIdMiddleware)

import prometheus_client
from prometheus_fastapi_instrumentator import Instrumentator
import src.application.metrics  # Initialize custom business metrics

Instrumentator(registry=prometheus_client.REGISTRY).instrument(app).expose(app, include_in_schema=False)

# Providers initialization
stt_prov = MockSpeechToTextProvider()
ocr_prov = MockOCRProvider()
emb_prov = SentenceTransformersEmbeddingProvider(model_name=settings.EMBEDDING_MODEL)
inj_shld = LocalPromptInjectionShield()

@app.get("/health", status_code=status.HTTP_200_OK)
def get_health(db: Session = Depends(get_db)):
    """
    Performs system health check diagnostics on database and services.
    """
    health_status = {
        "status": "healthy",
        "database": "unreachable",
        "redis": "unreachable",
        "pgvector": "unreachable",
        "settings": {
            "environment": settings.ENVIRONMENT,
            "stt_provider": settings.SPEECH_TO_TEXT_PROVIDER,
            "ocr_provider": settings.OCR_PROVIDER,
            "embedding_provider": settings.EMBEDDING_PROVIDER
        }
    }

    try:
        db.execute(Base.metadata.tables["users"].select().limit(1))
        health_status["database"] = "healthy"
    except Exception as e:
        try:
            db.execute(engine.dialect.denier_query if hasattr(engine.dialect, "denier_query") else "SELECT 1")
            health_status["database"] = "healthy"
        except Exception:
            health_status["status"] = "unhealthy"

    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        if r.ping():
            health_status["redis"] = "healthy"
    except Exception:
        health_status["status"] = "unhealthy"

    try:
        from sqlalchemy import text
        res = db.execute(text("SELECT '[1,2,3]'::vector;")).fetchone()
        if res:
            health_status["pgvector"] = "healthy"
    except Exception:
        health_status["status"] = "unhealthy"

    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )

    return health_status

@app.post("/api/v1/messages/route", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
@limiter.limit("100/minute")
async def route_message(request: Request, payload: Dict[str, Any], db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """
    Ingests an incoming message and determines the routing action.
    """
    if settings.ENABLE_REDACTION and 'message_text' in payload and payload['message_text']:
        from src.domain.redaction import DataRedactor
        payload['message_text'] = DataRedactor.redact(payload['message_text'])

    pipeline = MessageRoutingPipeline(
        db=db,
        stt_provider=stt_prov,
        ocr_provider=ocr_prov,
        embedding_provider=emb_prov,
        injection_shield=inj_shld
    )

    try:
        decision = await pipeline.route_incoming_message(payload)
        return decision
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Routing execution failed: {str(e)}"
        )

@app.post("/api/v1/messages/demo", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def route_message_demo(request: Request, payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Public Live Demo endpoint. Ingests an incoming message and determines the routing action.
    Strictly rate-limited and requires no master API key.
    """
    # Enforce reasonable payload size limits
    if 'message_text' in payload and len(payload.get('message_text', '')) > 2000:
        raise HTTPException(status_code=400, detail="Message text too long for demo.")

    if settings.ENABLE_REDACTION and 'message_text' in payload and payload['message_text']:
        from src.domain.redaction import DataRedactor
        payload['message_text'] = DataRedactor.redact(payload['message_text'])

    pipeline = MessageRoutingPipeline(
        db=db,
        stt_provider=stt_prov,
        ocr_provider=ocr_prov,
        embedding_provider=emb_prov,
        injection_shield=inj_shld
    )

    try:
        decision = await pipeline.route_incoming_message(payload)
        return decision
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo routing execution failed: {str(e)}"
        )

@app.post("/api/v1/messages/process", response_model=MessageProcessingResult, status_code=status.HTTP_200_OK)
@limiter.limit("100/minute")
async def process_message(request: Request, request_data: MessageProcessingRequest, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """
    Ingests an incoming message and executes modular Phase 2 processing,
    returning structured safety, urgency, personalization, and classification results.
    """
    if settings.ENABLE_REDACTION and request_data.message_text:
        from src.domain.redaction import DataRedactor
        request_data.message_text = DataRedactor.redact(request_data.message_text)

    pipeline = MessageRoutingPipeline(
        db=db,
        stt_provider=stt_prov,
        ocr_provider=ocr_prov,
        embedding_provider=emb_prov,
        injection_shield=inj_shld
    )

    try:
        result = await pipeline.process_incoming_message(request_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Message processing failed: {str(e)}"
        )

@app.post("/api/v1/messages/process-async", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("100/minute")
async def process_message_asynchronously(request: Request, request_data: MessageProcessingRequest, api_key: str = Depends(get_api_key)):
    """
    Asynchronously enqueues the message processing request via Celery background tasks.
    """
    if settings.ENABLE_REDACTION and request_data.message_text:
        from src.domain.redaction import DataRedactor
        request_data.message_text = DataRedactor.redact(request_data.message_text)

    try:
        task = process_message_async.delay(request_data.model_dump())
        return {
            "task_id": task.id,
            "status": "PENDING"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task dispatch failed: {str(e)}"
        )

@app.get("/api/v1/messages/tasks/{task_id}", status_code=status.HTTP_200_OK)
@limiter.limit("200/minute")
async def get_task_status(request: Request, task_id: str, api_key: str = Depends(get_api_key)):
    """
    Checks the execution status of a background message processing task.
    """
    try:
        res = AsyncResult(task_id, app=celery_app)
        state = res.state

        if state == "SUCCESS":
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "result": res.result
            }
        elif state == "FAILURE":
            return {
                "task_id": task_id,
                "status": "FAILURE",
                "error": "Task execution failed during asynchronous processing"
            }
        else:
            return {
                "task_id": task_id,
                "status": state
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch task status: {str(e)}"
        )

@app.post("/api/v1/interactions", status_code=status.HTTP_201_CREATED)
@limiter.limit("200/minute")
async def register_user_interaction(request: Request, payload: UserInteractionRequest, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """
    Ingests user interaction metrics (clicks, replies, dismissals, reports) and persists in DB.
    """
    try:
        from src.infrastructure.models import User, Message, Channel, UserInteraction

        dialect_name = db.bind.dialect.name if (db and db.bind) else "sqlite"

        # Check if user exists, otherwise create a stub user if SQLite
        user_obj = db.query(User).filter(User.id == payload.user_id).first()
        if not user_obj:
            if dialect_name == "sqlite":
                user_obj = User(id=payload.user_id, email=payload.user_id)
                db.add(user_obj)
                db.flush()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {payload.user_id} does not exist"
                )

        # Check if message exists, otherwise create a stub message if SQLite
        msg_obj = db.query(Message).filter(Message.id == payload.message_id).first()
        if not msg_obj:
            if dialect_name == "sqlite":
                chan_id = "default_channel"
                chan_obj = db.query(Channel).filter(Channel.id == chan_id).first()
                if not chan_obj:
                    chan_obj = Channel(id=chan_id, name="Default Channel", type="personal", external_id=chan_id)
                    db.add(chan_obj)
                    db.flush()
                msg_obj = Message(id=payload.message_id, channel_id=chan_id, message_text="")
                db.add(msg_obj)
                db.flush()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Message {payload.message_id} does not exist"
                )

        interaction = UserInteraction(
            user_id=payload.user_id,
            message_id=payload.message_id,
            opened=payload.opened,
            replied=payload.replied,
            dismissed=payload.dismissed,
            reported=payload.reported,
            reaction_time_seconds=payload.reaction_time_seconds
        )
        db.add(interaction)
        db.commit()

        # Dispatch background Celery task to recalculate user personalization aggregates
        sender_id_val = msg_obj.sender_id or "default_sender"
        from src.application.personalization_cache import PersonalizationCache
        PersonalizationCache.invalidate(payload.user_id, sender_id_val)

        from src.worker import recalculate_personalization_stats
        recalculate_personalization_stats.delay(payload.user_id, sender_id_val)

        return {
            "status": "success",
            "message": "User interaction recorded successfully",
            "interaction_id": interaction.id
        }
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record interaction: {str(e)}"
        )

@app.get("/api/v1/analytics/alignment", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def get_routing_alignment_analytics(request: Request, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """
    Retrieves the routing decision alignment analytics by comparing system routing
    decisions with the user's actual interaction outcomes.
    """
    try:
        from src.application.analytics_service import AnalyticsService
        return AnalyticsService.get_routing_alignment_analytics(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alignment analytics: {str(e)}"
        )

@app.get("/api/v1/tasks/dlq", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def get_failed_tasks_dlq(request: Request, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """
    Retrieves a list of permanently failed tasks from the Dead Letter Queue.
    """
    try:
        from src.infrastructure.models import FailedTaskLog
        failed_logs = db.query(FailedTaskLog).filter(FailedTaskLog.is_replayed == False).all()
        return {
            "status": "success",
            "failed_tasks": [
                {
                    "id": log.id,
                    "task_id": log.task_id,
                    "task_name": log.task_name,
                    "failed_at": log.failed_at.isoformat() if log.failed_at else None,
                    "exception": log.exception_details,
                    "original_payload": log.original_payload
                } for log in failed_logs
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch DLQ: {str(e)}"
        )

@app.post("/api/v1/tasks/dlq/{log_id}/replay", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def replay_failed_task(request: Request, log_id: int, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """
    Replays a specific failed task from the DLQ by re-enqueueing it to Celery.
    """
    try:
        import json
        from src.infrastructure.models import FailedTaskLog
        failed_log = db.query(FailedTaskLog).filter(FailedTaskLog.id == log_id).first()
        if not failed_log:
            raise HTTPException(status_code=404, detail="Failed task log not found")
        if failed_log.is_replayed:
            raise HTTPException(status_code=400, detail="Task has already been replayed")
        payload = {}
        if failed_log.original_payload:
            try:
                payload = json.loads(failed_log.original_payload)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Original payload is not valid JSON, cannot replay safely")
        import src.worker as worker
        if failed_log.task_name == "tasks.process_message_async":
            worker.process_message_async.delay(payload)
        elif failed_log.task_name == "tasks.process_media_async":
            worker.process_media_async.delay(**payload)
        elif failed_log.task_name == "tasks.recalculate_personalization_stats":
            worker.recalculate_personalization_stats.delay(**payload)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported task type for replay: {failed_log.task_name}")
        failed_log.is_replayed = True
        db.commit()
        return {
            "status": "success",
            "message": f"Task {log_id} successfully re-enqueued for replay",
            "task_name": failed_log.task_name
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to replay DLQ task: {str(e)}"
        )
