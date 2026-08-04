from celery import Celery
from src.config.settings import settings
from sqlalchemy.exc import OperationalError, DBAPIError
from redis.exceptions import ConnectionError, TimeoutError

# Initialize Celery app
celery_app = Celery(
    "smartinbox_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

from celery.signals import worker_ready

@worker_ready.connect
def warm_up_model(sender, **kwargs):
    """
    Eagerly loads and warms up the SentenceTransformer model when worker boots.
    """
    try:
        from src.infrastructure.providers.sentence_transformer_provider import SentenceTransformersEmbeddingProvider
        emb_prov = SentenceTransformersEmbeddingProvider(model_name=settings.EMBEDDING_MODEL)
        emb_prov.warmup()
    except Exception as e:
        print(f"Celery worker eager warmup failed: {e}")

@celery_app.task(name="tasks.process_media_async")
def process_media_async(message_id: str, media_type: str, media_url: str):
    """
    Background job to process media elements (speech-to-text / OCR) asynchronously.
    """
    print(f"Starting async media parsing task for message {message_id} ({media_type})")
    return {
        "status": "completed",
        "message_id": message_id,
        "media_type": media_type
    }

@celery_app.task(
    name="tasks.process_message_async",
    autoretry_for=(OperationalError, DBAPIError, ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=5
)
def process_message_async(request_data: dict) -> dict:
    """
    Background job to execute modular message processing asynchronously.
    """
    from src.database.session import SessionLocal
    from src.application.schemas import MessageProcessingRequest
    from src.application.pipeline import MessageRoutingPipeline
    from src.infrastructure.providers.mock_providers import (
        MockSpeechToTextProvider,
        MockOCRProvider,
        LocalPromptInjectionShield
    )
    from src.infrastructure.providers.sentence_transformer_provider import SentenceTransformersEmbeddingProvider
    import asyncio

    db = SessionLocal()

    stt_prov = MockSpeechToTextProvider()
    ocr_prov = MockOCRProvider()
    emb_prov = SentenceTransformersEmbeddingProvider(model_name=settings.EMBEDDING_MODEL)
    inj_shld = LocalPromptInjectionShield()

    pipeline = MessageRoutingPipeline(
        db=db,
        stt_provider=stt_prov,
        ocr_provider=ocr_prov,
        embedding_provider=emb_prov,
        injection_shield=inj_shld
    )

    try:
        request = MessageProcessingRequest(**request_data)
        result = asyncio.run(pipeline.process_incoming_message(request))
        return result.model_dump()
    except Exception as e:
        print(f"Celery message processing failed: {str(e)}")
        raise e
    finally:
        db.close()

@celery_app.task(
    name="tasks.recalculate_personalization_stats",
    autoretry_for=(OperationalError, DBAPIError, ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=5
)
def recalculate_personalization_stats(user_id: str, sender_id: str, db=None) -> dict:
    """
    Asynchronously aggregates historical statistics for a user/sender pair,
    preparing the data for caching.
    """
    from src.database.session import SessionLocal
    from src.application.personalization_service import PersonalizationService

    is_external_db = db is not None
    session = db if is_external_db else SessionLocal()
    try:
        print(f"Starting background personalization re-aggregation for user {user_id} and sender {sender_id}")
        stats = PersonalizationService.get_historical_stats(session, user_id, sender_id)
        from src.application.personalization_cache import PersonalizationCache
        PersonalizationCache.set(user_id, sender_id, stats)
        return stats
    except Exception as e:
        print(f"Error recalculating personalization stats: {str(e)}")
        raise e
    finally:
        if not is_external_db:
            session.close()

from celery.signals import task_failure
import json
import traceback

@task_failure.connect
def handle_task_failure(sender, task_id, exception, args, kwargs, traceback_obj, einfo, **kw):
    """
    Catches permanently failed Celery tasks and persists them to the FailedTaskLog.
    """
    from src.database.session import SessionLocal
    from src.infrastructure.models import FailedTaskLog
    db = SessionLocal()
    try:
        task_name = sender.name if hasattr(sender, 'name') else "unknown"
        original_payload = None
        if args and len(args) > 0:
            if isinstance(args[0], dict):
                original_payload = json.dumps(args[0])
            elif isinstance(args[0], str):
                original_payload = args[0]
            else:
                original_payload = str(args)
        tb_str = "".join(traceback.format_exception(type(exception), exception, traceback_obj)) if traceback_obj else None
        failed_log = FailedTaskLog(
            task_id=task_id,
            task_name=task_name,
            original_payload=original_payload,
            exception_details=str(exception),
            traceback_details=tb_str
        )
        db.add(failed_log)
        db.commit()
    except Exception as e:
        print(f"Failed to log task failure to DLQ: {e}")
    finally:
        db.close()
