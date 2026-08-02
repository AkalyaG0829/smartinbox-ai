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

    async def get_embedding(self, text: str) -> List[float]:
        """
        Generates a 384-dimensional dense float vector using local SentenceTransformers.
        """
        if not text:
            return [0.0] * self.get_dimension()
        
        self._lazy_init()
        
        try:
            loop = asyncio.get_running_loop()
            embeddings = await loop.run_in_executor(None, lambda: self._model.encode([text]))
        except RuntimeError:
            embeddings = self._model.encode([text])
            
        return [float(x) for x in embeddings[0]]

    def get_dimension(self) -> int:
        """
        SentenceTransformers all-MiniLM-L6-v2 produces a vector length of 384.
        """
        return 384
