from abc import ABC, abstractmethod
from typing import BinaryIO, List

class SpeechToTextProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_file: BinaryIO) -> str:
        """
        Transcribes audio data (from a file/stream) into plain text.
        """
        pass

class OCRProvider(ABC):
    @abstractmethod
    async def extract_text(self, image_file: BinaryIO) -> str:
        """
        Extracts alphanumeric characters and text lines from image files.
        """
        pass

class EmbeddingProvider(ABC):
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generates a dense float vector representation for text.
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """
        Returns the output dimension of the embeddings vector.
        """
        pass
class PromptInjectionShield(ABC):
    @abstractmethod
    def scan(self, text: str) -> bool:
        """
        Scans input text for potential prompt injection attempts.
        Returns True if a threat is detected, False otherwise.
        """
        pass
