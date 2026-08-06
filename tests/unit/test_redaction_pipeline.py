import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.application.pipeline import MessageRoutingPipeline
from src.application.schemas import MessageProcessingRequest
from src.worker import handle_task_failure
from src.infrastructure.models import Message, FailedTaskLog
from src.database.session import SessionLocal

@pytest.mark.asyncio
async def test_ocr_transcript_redaction():
    stt_mock = AsyncMock()
    ocr_mock = AsyncMock()
    ocr_mock.extract_text.return_value = "Receipt for test@example.com"
    emb_mock = AsyncMock()
    emb_mock.get_embedding.return_value = [0.1, 0.2]
    inj_mock = MagicMock()
    inj_mock.scan.return_value = None
    
    db_mock = MagicMock()
    db_mock.query().filter().first.return_value = None
    db_mock.bind.dialect.name = "postgresql"
    
    pipeline = MessageRoutingPipeline(
        db=db_mock,
        stt_provider=stt_mock,
        ocr_provider=ocr_mock,
        embedding_provider=emb_mock,
        injection_shield=inj_mock
    )
    
    req = MessageProcessingRequest(
        message_id="msg_123",
        user_id="user1",
        conversation_type="personal",
        media_type="image",
        media_id="img_1",
        created_at="2026-08-01T00:00:00Z"
    )
    
    res = await pipeline.process_incoming_message(req)
    
    # Verify embedding used redacted text
    emb_mock.get_embedding.assert_called_with("Receipt for [EMAIL]")
    
    # Verify DB save used redacted transcript
    added_objs = [call.args[0] for call in db_mock.add.call_args_list]
    saved_msg = next((obj for obj in added_objs if isinstance(obj, Message)), None)
    assert saved_msg is not None
    assert saved_msg.media_transcript == "Receipt for [EMAIL]"

@pytest.mark.asyncio
async def test_stt_transcript_redaction():
    stt_mock = AsyncMock()
    stt_mock.transcribe.return_value = "Call me back at 555-123-4567"
    ocr_mock = AsyncMock()
    emb_mock = AsyncMock()
    emb_mock.get_embedding.return_value = [0.1, 0.2]
    inj_mock = MagicMock()
    inj_mock.scan.return_value = None
    
    db_mock = MagicMock()
    db_mock.query().filter().first.return_value = None
    db_mock.bind.dialect.name = "postgresql"
    
    pipeline = MessageRoutingPipeline(
        db=db_mock,
        stt_provider=stt_mock,
        ocr_provider=ocr_mock,
        embedding_provider=emb_mock,
        injection_shield=inj_mock
    )
    
    req = {
        "message_id": "msg_456",
        "user_id": "user1",
        "conversation_type": "personal",
        "media_type": "voice",
        "media_id": "aud_1"
    }
    
    res = await pipeline.route_incoming_message(req)
    
    emb_mock.get_embedding.assert_called_with("Call me back at [PHONE]")
    added_objs = [call.args[0] for call in db_mock.add.call_args_list]
    saved_msg = next((obj for obj in added_objs if isinstance(obj, Message)), None)
    assert saved_msg is not None
    assert saved_msg.media_transcript == "Call me back at [PHONE]"

from unittest.mock import patch

def test_dlq_exception_redaction():
    db_mock = MagicMock()
    with patch('src.database.session.SessionLocal', return_value=db_mock):
        class FakeSender:
            name = "test_task"
        sender = FakeSender()
        exception = ValueError("Validation failed for user@example.com with token abc123def456xyz789")
        
        handle_task_failure(sender, "task_1", exception, args=({"payload": "data"},), kwargs={}, traceback_obj=None, einfo=None)
        
        added_objs = [call.args[0] for call in db_mock.add.call_args_list]
        log = next((obj for obj in added_objs if isinstance(obj, FailedTaskLog)), None)
        assert log is not None
        assert "user@example.com" not in log.exception_details
        assert "[EMAIL]" in log.exception_details
        assert "abc123def456xyz789" not in log.exception_details
        assert "[SECRET]" in log.exception_details
