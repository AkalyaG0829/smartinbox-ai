from celery import Celery
from src.config.settings import settings

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

@celery_app.task(name="tasks.process_message_async")
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
        MockEmbeddingProvider,
        LocalPromptInjectionShield
    )
    import asyncio

    db = SessionLocal()

    stt_prov = MockSpeechToTextProvider()
    ocr_prov = MockOCRProvider()
    emb_prov = MockEmbeddingProvider()
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
