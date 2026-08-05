import pytest
from unittest.mock import patch, MagicMock
from src.infrastructure.providers.sentence_transformer_provider import SentenceTransformersEmbeddingProvider
from src.worker import warm_up_model, process_message_async, emb_prov_singleton
import asyncio
import threading

def test_ml_provider_thread_safety_and_singleton():
    # Verify singleton
    assert isinstance(emb_prov_singleton, SentenceTransformersEmbeddingProvider)

    # Verify locks exist
    assert hasattr(emb_prov_singleton, "_init_lock")
    assert isinstance(emb_prov_singleton._init_lock, type(threading.Lock()))
    assert hasattr(emb_prov_singleton, "_inference_lock")
    assert isinstance(emb_prov_singleton._inference_lock, type(threading.Lock()))

    # Verify concurrent initialization does not race (mock sentence_transformers)
    with patch("sentence_transformers.SentenceTransformer") as MockST:
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]
        MockST.return_value = mock_model

        # Reset singleton state for test
        emb_prov_singleton._model = None

        # Simulate concurrent access
        def worker_thread():
            emb_prov_singleton._lazy_init()

        threads = [threading.Thread(target=worker_thread) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should only initialize the underlying model ONCE despite 10 threads
        MockST.assert_called_once()
        assert emb_prov_singleton._model is not None
