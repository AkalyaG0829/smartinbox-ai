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
    # This is a stub task for the MVP background worker setup in Phase 1
    # In Phase 3, this worker will invoke SpeechToTextProvider / OCRProvider
    # and update the message record in the database.
    return {
        "status": "completed",
        "message_id": message_id,
        "media_type": media_type
    }
