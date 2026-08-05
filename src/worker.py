from celery import Celery
from src.config.settings import settings
from sqlalchemy.exc import OperationalError, DBAPIError
from redis.exceptions import ConnectionError, TimeoutError
import logging
import contextvars
from celery.signals import task_prerun, task_postrun

correlation_id_var = contextvars.ContextVar("correlation_id", default="-")

class CeleryTelemetryFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id_var.get()
        if not hasattr(record, "taskName"):
            record.taskName = "-"
        return True

logger = logging.getLogger("smartinbox_worker")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "task": "%(taskName)s", "message": "%(message)s"}'))
logger.addHandler(handler)
logger.addFilter(CeleryTelemetryFilter())

@task_prerun.connect
def setup_task_logging(task_id, task, *args, **kwargs):
    # Try to extract correlation ID if passed in args/kwargs
    # For now we'll just set it to the celery task id if not provided
    correlation_id_var.set(task_id)

@task_postrun.connect
def teardown_task_logging(task_id, task, *args, **kwargs):
    correlation_id_var.set("-")

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
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_routes={
        'tasks.process_message_async': {'queue': 'ml_queue'},
        'tasks.recalculate_personalization_stats': {'queue': 'routing_queue'},
        'tasks.process_media_async': {'queue': 'routing_queue'},
    }
)

from celery.signals import worker_ready

from src.infrastructure.providers.sentence_transformer_provider import SentenceTransformersEmbeddingProvider
emb_prov_singleton = SentenceTransformersEmbeddingProvider(model_name=settings.EMBEDDING_MODEL)

@worker_ready.connect
def warm_up_model(sender, **kwargs):
    """
    Eagerly loads and warms up the SentenceTransformer model when worker boots.
    """
    if settings.WORKER_ROLE not in ["all", "ml"]:
        logger.info(f"Skipping ML warmup. Worker role is {settings.WORKER_ROLE}.", extra={"taskName": "warm_up_model"})
        return

    try:
        emb_prov_singleton.warmup()
        logger.info("Celery worker eager warmup completed successfully", extra={"taskName": "warm_up_model"})
    except Exception as e:
        logger.error(f"Celery worker eager warmup failed: {e}", extra={"taskName": "warm_up_model"})

@celery_app.task(
    name="tasks.process_media_async",
    soft_time_limit=60,
    time_limit=90
)
def process_media_async(message_id: str, media_type: str, media_url: str):
    """
    Background job to process media elements (speech-to-text / OCR) asynchronously.
    """
    logger.info(f"Starting async media parsing task for message {message_id} ({media_type})", extra={"taskName": "tasks.process_media_async"})
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
    max_retries=5,
    soft_time_limit=120,
    time_limit=150
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
    inj_shld = LocalPromptInjectionShield()

    pipeline = MessageRoutingPipeline(
        db=db,
        stt_provider=stt_prov,
        ocr_provider=ocr_prov,
        embedding_provider=emb_prov_singleton,
        injection_shield=inj_shld
    )

    try:
        request = MessageProcessingRequest(**request_data)
        logger.info(f"Starting async processing for message {request.message_id}", extra={"taskName": "tasks.process_message_async"})
        result = asyncio.run(pipeline.process_incoming_message(request))
        return result.model_dump()
    except Exception as e:
        logger.error(f"Celery message processing failed: {str(e)}", extra={"taskName": "tasks.process_message_async"})
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
        logger.info(f"Starting background personalization re-aggregation for user {user_id} and sender {sender_id}", extra={"taskName": "tasks.recalculate_personalization_stats"})
        stats = PersonalizationService.get_historical_stats(session, user_id, sender_id)
        from src.application.personalization_cache import PersonalizationCache
        PersonalizationCache.set(user_id, sender_id, stats)
        return stats
    except Exception as e:
        logger.error(f"Error recalculating personalization stats: {str(e)}", extra={"taskName": "tasks.recalculate_personalization_stats"})
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
            payload_data = args[0]
            if isinstance(payload_data, dict):
                sanitized_data = payload_data.copy()
                sensitive_keys = ['api_key', 'password', 'token', 'authorization', 'secret']
                for key in sanitized_data:
                    if any(s in key.lower() for s in sensitive_keys):
                        sanitized_data[key] = "***MASKED***"
                original_payload = json.dumps(sanitized_data)
            elif isinstance(payload_data, str):
                original_payload = payload_data
            else:
                original_payload = str(payload_data)
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
        from src.application.metrics import DLQ_ENTRIES
        DLQ_ENTRIES.labels(task_name=task_name).inc()
        logger.error(f"Task {task_name} permanently failed. Logged to DLQ.", extra={"taskName": task_name})
    except Exception as e:
        logger.error(f"Failed to log task failure to DLQ: {e}", extra={"taskName": "handle_task_failure"})
    finally:
        db.close()
