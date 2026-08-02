import re
from typing import BinaryIO, List
from src.domain.interfaces import SpeechToTextProvider, OCRProvider, EmbeddingProvider, PromptInjectionShield

class MockSpeechToTextProvider(SpeechToTextProvider):
    async def transcribe(self, audio_file: BinaryIO) -> str:
        # Simplistic mock that reads raw stream or returns default text
        return "[transcription of voice note]"

    # Support simple transcription lookup for regression/parity mapping
    def lookup_regression_transcript(self, media_id: str) -> str:
        # Return a known transcript if media_id is provided, to mimic OCR/STT lookup
        return ""

class MockOCRProvider(OCRProvider):
    async def extract_text(self, image_file: BinaryIO) -> str:
        return "[extracted text from image]"

class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    async def get_embedding(self, text: str) -> List[float]:
        # Generate a deterministic pseudo-embedding based on the text string
        if not text:
            return [0.0] * self.dimension
        
        # Simple hash-based deterministic mock vector
        vector = []
        for i in range(self.dimension):
            val = sum(ord(c) * (i + 1) for c in text) % 1000
            vector.append(float(val) / 1000.0)
        return vector

    def get_dimension(self) -> int:
        return self.dimension

class LocalPromptInjectionShield(PromptInjectionShield):
    def scan(self, text: str) -> bool:
        if not text:
            return False
        text_lower = text.lower()
        # Look for typical instruction override commands
        injection_patterns = [
            r"assistant\s+instruction",
            r"ignore\s+(previous|system|sender|safety|risk|rules)",
            r"override\s+action",
            r"notify\s+immediately",
            r"always\s+notify"
        ]
        for pattern in injection_patterns:
            if re.search(pattern, text_lower):
                return True
        return False
