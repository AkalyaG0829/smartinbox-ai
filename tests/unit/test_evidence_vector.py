import pytest
import asyncio
from unittest.mock import MagicMock, patch
from src.infrastructure.models import User, Channel, ChannelMember, Contact, Message
from src.domain.evidence import EvidenceRetriever
from src.infrastructure.providers.mock_providers import MockEmbeddingProvider

def test_evidence_retriever_sqlite_jaccard_fallback(db_session):
    """
    Verifies SQLite test compatibility and legacy Jaccard fallback behavior
    when executing queries in a non-PostgreSQL environment.
    """
    # 1. Setup test data in the SQLite test database
    user = User(id="u_test_001", email="user_test@example.com")
    db_session.add(user)

    chan = Channel(id="c_test_001", name="Test Channel", type="personal", external_id="c_test_001")
    db_session.add(chan)
    db_session.flush()

    member = ChannelMember(user_id=user.id, channel_id=chan.id, role="member", is_muted=False)
    db_session.add(member)

    contact = Contact(id="u_test_002", name="Contact Test", type="user")
    db_session.add(contact)
    contact2 = Contact(id="u_test_003", name="Contact Test 2", type="user")
    db_session.add(contact2)
    db_session.flush()

    msg1 = Message(id="msg_test_001", channel_id=chan.id, sender_id=contact.id, message_text="Hello this is important meeting details", media_type="none")
    msg2 = Message(id="msg_test_002", channel_id=chan.id, sender_id=contact2.id, message_text="Unrelated chat about lunch", media_type="none")
    db_session.add(msg1)
    db_session.add(msg2)
    db_session.flush()

    msg_input = {
        "user_id": "user_test@example.com",
        "conversation_type": "personal",
        "sender_user_id": "u_test_002",
        "message_text": "Need meeting details ASAP",
        "media_type": "none"
    }

    # 2. Run retrieval using Jaccard fallback
    emb_prov = MockEmbeddingProvider()
    results = asyncio.run(EvidenceRetriever.retrieve_evidence(
        db=db_session,
        msg=msg_input,
        text_to_search="meeting details",
        embedding_provider=emb_prov,
        similarity_threshold=0.6,
        limit=3
    ))

    # SQLite fallback should find msg1 because of token overlap
    assert len(results) >= 1
    assert "msg_test_001" in results
    assert "msg_test_002" not in results

def test_evidence_retriever_postgresql_pgvector():
    """
    Verifies the PostgreSQL semantic query behavior, configurable similarity threshold,
    retrieval limits, user/channel filtering, and top-K behavior.
    """
    db_mock = MagicMock()
    db_mock.bind.dialect.name = "postgresql"

    # Mock user resolver
    mock_user = MagicMock()
    mock_user.id = "u_pg_001"
    db_mock.query.return_value.filter.return_value.first.return_value = mock_user

    # Mock vector query results
    mock_row1 = MagicMock()
    mock_row1.id = "msg_pg_001"
    mock_row1.distance = 0.3

    mock_row2 = MagicMock()
    mock_row2.id = "msg_pg_002"
    mock_row2.distance = 0.5

    mock_row3 = MagicMock()
    mock_row3.id = "msg_pg_003"
    mock_row3.distance = 0.8

    db_mock.query.return_value.join.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [
        mock_row1, mock_row2, mock_row3
    ]

    msg_input = {
        "user_id": "pg_user@example.com",
        "conversation_type": "personal",
        "message_text": "Hello pgvector query",
        "media_type": "none"
    }

    emb_prov = MagicMock()
    async def mock_get_emb(text):
        return [0.1] * 384
    emb_prov.get_embedding.side_effect = mock_get_emb

    # A. Test default threshold (0.6) and limit (3)
    results = asyncio.run(EvidenceRetriever.retrieve_evidence(
        db=db_mock,
        msg=msg_input,
        text_to_search="semantic query",
        embedding_provider=emb_prov,
        similarity_threshold=0.6,
        limit=3
    ))
    # Excludes msg_pg_003 because its distance is 0.8
    assert results == ["msg_pg_001", "msg_pg_002"]

    # B. Test configurable similarity threshold (0.4)
    results_threshold = asyncio.run(EvidenceRetriever.retrieve_evidence(
        db=db_mock,
        msg=msg_input,
        text_to_search="semantic query",
        embedding_provider=emb_prov,
        similarity_threshold=0.4,
        limit=3
    ))
    assert results_threshold == ["msg_pg_001"]

    # C. Test configurable retrieval limit (1)
    results_limit = asyncio.run(EvidenceRetriever.retrieve_evidence(
        db=db_mock,
        msg=msg_input,
        text_to_search="semantic query",
        embedding_provider=emb_prov,
        similarity_threshold=0.6,
        limit=1
    ))
    assert results_limit == ["msg_pg_001"]

def test_hnsw_index_configuration():
    """
    Verifies that the PostgreSQL HNSW index exists on the Message model definition
    and targets pgvector's vector_cosine_ops operator class.
    """
    from src.infrastructure.models import Message

    indexes = [idx for idx in Message.__table__.indexes if idx.name == "messages_embedding_vector_hnsw_idx"]
    assert len(indexes) == 1
    hnsw_index = indexes[0]
    assert hnsw_index.dialect_options["postgresql"]["using"] == "hnsw"
    assert hnsw_index.dialect_options["postgresql"]["ops"] == {"embedding_vector": "vector_cosine_ops"}

def test_evidence_retriever_graceful_failure(db_session):
    """
    Verifies graceful database/vector query exception handling.
    """
    # Force connection failure
    msg_input = {
        "user_id": "user_fail@example.com",
        "conversation_type": "personal",
        "message_text": "Fail test",
        "media_type": "none"
    }

    results = asyncio.run(EvidenceRetriever.retrieve_evidence(
        db=None,
        msg=msg_input,
        text_to_search="semantic",
        embedding_provider=None
    ))
    assert results == []
