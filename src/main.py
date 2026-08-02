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
from src.application.schemas import MessageProcessingRequest, MessageProcessingResult
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
