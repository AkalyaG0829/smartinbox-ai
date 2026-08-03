import asyncio
from typing import List
from src.domain.interfaces import EmbeddingProvider

class SentenceTransformersEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _lazy_init(self):
        """
        Lazy load model weights only upon the first embedding request.
        Prevents startup overhead if model is unused or dependencies are missing.
        """
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)

    def warmup(self):
        """
        Eagerly loads model weights and runs a dummy encoding to warm up the ST model,
        preventing cold start latency on first request.
        """
        print(f"Eagerly warming up embedding model: {self.model_name}...")
        self._lazy_init()
        try:
            self._model.encode(["warmup"])
            print("Embedding model warmup complete.")
        except Exception as e:
            print(f"Embedding model warmup failed: {str(e)}")

    async def get_embedding(self, text: str) -> List[float]:
        """
        Generates a 384-dimensional dense float vector using local SentenceTransformers.
        """
        if not text:
            return [0.0] * self.get_dimension()

        # Check cache-aside
        from src.application.embedding_cache import EmbeddingCache
        cached_vector = EmbeddingCache.get(text)
        if cached_vector is not None:
            return cached_vector

        self._lazy_init()

        try:
            loop = asyncio.get_running_loop()
            embeddings = await loop.run_in_executor(None, lambda: self._model.encode([text]))
        except RuntimeError:
            embeddings = self._model.encode([text])

        result = [float(x) for x in embeddings[0]]

        # Populate cache
        EmbeddingCache.set(text, result)

        return result

    def get_dimension(self) -> int:
        """
        SentenceTransformers all-MiniLM-L6-v2 produces a vector length of 384.
        """
        return 384
