import unicodedata
import re
from typing import List

class MessagePreprocessor:
    @staticmethod
    def preprocess(text: str) -> str:
        """
        Normalizes whitespaces, casing, Unicode formatting, and punctuation variations.
        Preserves original text meaning for downstream classification.
        """
        if not text or not isinstance(text, str):
            return ""

        # 1. Unicode normalization (NFKC decomposes compatibility characters)
        normalized = unicodedata.normalize("NFKC", text)

        # 2. Punctuation normalizing
        # Normalize smart/curly single and double quotes to straight ones
        normalized = normalized.replace("‘", "'").replace("’", "'")
        normalized = normalized.replace("“", '"').replace("”", '"')
        
        # Normalize multiple spaces, tabs, and newlines to a single space (while preserving characters)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Strip leading/trailing whitespaces
        normalized = normalized.strip()
        
        return normalized

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """
        Splits clean text into distinct lowercase alphanumeric word tokens.
        Useful for keyword/phrase parsing.
        """
        clean_text = MessagePreprocessor.preprocess(text).lower()
        tokens = re.findall(r'\b\w+\b', clean_text)
        return tokens

def get_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculates Jaccard word similarity between two text strings."""
    if not isinstance(text1, str) or not isinstance(text2, str):
        return 0.0
    w1 = set(text1.lower().split())
    w2 = set(text2.lower().split())
    if not w1 or not w2:
        return 0.0
    return len(w1.intersection(w2)) / len(w1.union(w2))

def has_word_match(text: str, keywords: List[str]) -> bool:
    """Checks if any keyword is present in the text as a distinct word token using regex word boundaries."""
    if not isinstance(text, str) or not text.strip():
        return False
    text_lower = text.lower()
    for kw in keywords:
        kw_lower = kw.lower()
        pattern = r'\b' + re.escape(kw_lower) + r'\b'
        if re.search(pattern, text_lower):
            return True
    return False
