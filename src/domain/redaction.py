import re

class DataRedactor:
    """
    Deterministic regex-based PII redaction layer.
    """
    
    # Pre-compile regex patterns for performance
    
    # Matches typical email formats
    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    # Matches typical phone numbers (e.g. 555-555-5555, (555) 555-5555, +1-555-555-5555)
    PHONE_REGEX = re.compile(r'(?:\+?\d{1,3}[\s-]?)?(?:\(\d{3}\)|\d{3})[\s-]?\d{3}[\s-]?\d{4}')
    
    # Matches US SSN (XXX-XX-XXXX)
    SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    
    # Matches credit/debit card numbers (13-19 digits, optional spaces/dashes)
    CARD_REGEX = re.compile(r'\b(?:\d[ -]*?){13,19}\b')
    
    # Matches common secrets like API keys or Bearer tokens
    # Basic heuristic: Bearer <base64 or hex> or specific prefixes
    SECRET_REGEX = re.compile(
        r'(?i)\b(?:bearer\s+[A-Za-z0-9\-\._~+/]+=*|'
        r'ak_live_[A-Za-z0-9]+|'
        r'sk_live_[A-Za-z0-9]+|'
        r'sk_test_[A-Za-z0-9]+|'
        r'(?:api_key|apikey|secret|token|password)[\s:=]+[\"\']?[A-Za-z0-9\-\._~+/]{16,}={0,2}[\"\']?)'
    )
    
    @classmethod
    def redact(cls, text: str) -> str:
        """
        Redacts PII from the provided string. Returns the string with PII replaced by placeholders.
        """
        if text is None:
            return ""
        if not isinstance(text, str):
            return str(text)
            
        redacted = text
        redacted = cls.EMAIL_REGEX.sub('[EMAIL]', redacted)
        redacted = cls.SSN_REGEX.sub('[SSN]', redacted)
        # Note: CARD_REGEX can sometimes match normal long numbers. We ensure word boundaries.
        # It's important to process SSN and CARD before PHONE to avoid partial matches
        redacted = cls.CARD_REGEX.sub('[CARD]', redacted)
        redacted = cls.PHONE_REGEX.sub('[PHONE]', redacted)
        redacted = cls.SECRET_REGEX.sub('[SECRET]', redacted)
        
        return redacted
