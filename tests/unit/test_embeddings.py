import sys
import asyncio
from unittest.mock import MagicMock

# Register mock module to prevent ModuleNotFoundError on environments without ML dependencies
mock_st = MagicMock()
sys.modules['sentence_transformers'] = mock_st

from src.infrastructure.providers.sentence_transformer_provider import SentenceTransformersEmbeddingProvider

def test_sentence_transformers_provider_mocked():
    """
    Verifies SentenceTransformersEmbeddingProvider behavior using mock model wrappers
    to ensure fast, offline execution without model weight downloads.
    """
    mock_model = MagicMock()
    mock_st.SentenceTransformer.return_value = mock_model
    
    # Deterministic dummy vector generator to verify consistency and differences
    def mock_encode(sentences, **kwargs):
        import numpy as np
        results = []
        for s in sentences:
            val = sum(ord(c) for c in s) % 100 / 100.0
            results.append(np.array([val] * 384, dtype=np.float32))
        return np.array(results)
        
    mock_model.encode.side_effect = mock_encode
    
    provider = SentenceTransformersEmbeddingProvider(model_name="all-MiniLM-L6-v2")
    
    # 1. Verify get_dimension
    assert provider.get_dimension() == 384
    
    # 2. Verify empty input returns a zero vector of dimension 384
    empty_vector = asyncio.run(provider.get_embedding(""))
    assert len(empty_vector) == 384
    assert all(v == 0.0 for v in empty_vector)
    
    # 3. Verify get_embedding returns 384 float values
    vec1 = asyncio.run(provider.get_embedding("hello"))
    assert len(vec1) == 384
    assert isinstance(vec1[0], float)
    
    # 4. Verify same input produces consistent semantic representation
    vec1_again = asyncio.run(provider.get_embedding("hello"))
    assert vec1 == vec1_again
    
    # 5. Verify different inputs produce different embeddings without errors
    vec2 = asyncio.run(provider.get_embedding("world"))
    assert len(vec2) == 384
    assert vec1 != vec2
    
    mock_st.SentenceTransformer.assert_called_with("all-MiniLM-L6-v2")
