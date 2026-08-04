import time
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import Dict, Any
from celery.result import AsyncResult

from src.config.settings import settings
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
    # Try to initialize database tables
    retries = 3
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception as e:
            print(f"Database connection waiting... Retrying. Error: {e}")
            time.sleep(2)
            retries -= 1

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

    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )

    return health_status

@app.post("/api/v1/messages/route", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def route_message(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Ingests an incoming message and determines the routing action.
    """
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

@app.post("/api/v1/messages/process", response_model=MessageProcessingResult, status_code=status.HTTP_200_OK)
async def process_message(payload: MessageProcessingRequest, db: Session = Depends(get_db)):
    """
    Ingests an incoming message and executes modular Phase 2 processing,
    returning structured safety, urgency, personalization, and classification results.
    """
    pipeline = MessageRoutingPipeline(
        db=db,
        stt_provider=stt_prov,
        ocr_provider=ocr_prov,
        embedding_provider=emb_prov,
        injection_shield=inj_shld
    )

    try:
        result = await pipeline.process_incoming_message(payload)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Message processing failed: {str(e)}"
        )

@app.post("/api/v1/messages/process-async", status_code=status.HTTP_202_ACCEPTED)
async def process_message_async_endpoint(payload: MessageProcessingRequest):
    """
    Asynchronously enqueues the message processing request via Celery background tasks.
    """
    try:
        task = process_message_async.delay(payload.model_dump())
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
async def get_task_status(task_id: str):
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
async def create_user_interaction(payload: UserInteractionRequest, db: Session = Depends(get_db)):
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
async def get_routing_alignment_analytics(db: Session = Depends(get_db)):
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
async def get_failed_tasks_dlq(db: Session = Depends(get_db)):
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
async def replay_failed_task(log_id: int, db: Session = Depends(get_db)):
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
