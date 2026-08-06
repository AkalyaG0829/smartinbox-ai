import pytest
from src.domain.redaction import DataRedactor

def test_redact_email():
    assert DataRedactor.redact("Contact me at test@example.com.") == "Contact me at [EMAIL]."
    assert DataRedactor.redact("Email: admin.user_name+tag@sub.domain.co.uk") == "Email: [EMAIL]"

def test_redact_phone():
    assert DataRedactor.redact("Call me at 555-123-4567") == "Call me at [PHONE]"
    assert DataRedactor.redact("Phone: (555) 123-4567") == "Phone: [PHONE]"
    assert DataRedactor.redact("+1-555-123-4567 is the number.") == "[PHONE] is the number."

def test_redact_ssn():
    assert DataRedactor.redact("My SSN is 123-45-6789.") == "My SSN is [SSN]."

def test_redact_credit_card():
    assert DataRedactor.redact("Card: 1234 5678 1234 5678") == "Card: [CARD]"
    assert DataRedactor.redact("Use 1234-5678-1234-5678 for payment.") == "Use [CARD] for payment."
    assert DataRedactor.redact("Or 1234567812345678") == "Or [CARD]"

def test_redact_secrets():
    assert DataRedactor.redact("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9") == "[SECRET]"
    assert DataRedactor.redact("Here is my token: \"abc123def456xyz789\"") == "Here is my [SECRET]"
    assert DataRedactor.redact("api_key = abc123def456xyz789") == "[SECRET]"
    assert DataRedactor.redact("ak_live_12345abcde") == "[SECRET]"

def test_multiple_pii_in_one_message():
    text = "User test@example.com has phone 555-555-5555 and SSN 123-45-6789."
    expected = "User [EMAIL] has phone [PHONE] and SSN [SSN]."
    assert DataRedactor.redact(text) == expected

def test_normal_text_unchanged():
    text = "Send me the OTP right now, this is urgent!"
    assert DataRedactor.redact(text) == text
    assert DataRedactor.redact("Meeting at 10 AM") == "Meeting at 10 AM"

def test_empty_or_none():
    assert DataRedactor.redact(None) == ""
    assert DataRedactor.redact("") == ""
    assert DataRedactor.redact("   ") == "   "

def test_routing_phrases_not_corrupted():
    # Ensuring that the redaction doesn't mistakenly strip out routing cues
    assert DataRedactor.redact("Mark this as spam") == "Mark this as spam"
    assert DataRedactor.redact("This is urgent") == "This is urgent"
    assert DataRedactor.redact("Send me the OTP") == "Send me the OTP"
