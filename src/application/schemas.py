from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class MessageProcessingRequest(BaseModel):
    message_id: str = Field(..., description="Unique message identifier")
    user_id: str = Field(..., description="The recipient user ID")
    conversation_type: str = Field(..., description="personal, group, or business")
    group_id: Optional[str] = Field(None, description="Group ID if conversation is group")
    business_id: Optional[str] = Field(None, description="Business ID if conversation is business")
    sender_user_id: Optional[str] = Field(None, description="Sender user ID if conversation is personal/group")
    created_at: str = Field(..., description="Timestamp of creation")
    message_text: Optional[str] = Field("", description="Raw text content of the message")
    media_type: Optional[str] = Field("none", description="none, image, or voice")
    media_id: Optional[str] = Field(None, description="Linked media element ID")
    forwarded_count: Optional[int] = Field(0, description="Forward count flag")
    
    # Custom fields for testing overrides
    do_not_disturb_window: Optional[str] = None
    group_muted: Optional[bool] = None
    allows_promotions: Optional[bool] = None
    verified: Optional[int] = None
    official_domain: Optional[str] = None
    domain_used_by_sender: Optional[str] = None
    user_reports_30d: Optional[int] = None
    category: Optional[str] = None
    is_mentioned: Optional[bool] = None
    is_sender_admin: Optional[bool] = None
    historical_stats: Optional[Dict[str, Any]] = None
    evidence_message_ids: Optional[str] = None

class SafetyResult(BaseModel):
    detected: bool = Field(False, description="True if a prompt injection or safety risk is detected")
    risk_level: str = Field("low", description="low, medium, high, critical")
    matched_indicators: List[str] = Field(default_factory=list, description="Matched indicators or keywords")
    sanitized_text: str = Field("", description="Sanitized text free of malicious instructions")

class UrgencyResult(BaseModel):
    is_urgent: bool = Field(False, description="True if message demands immediate review")
    urgency_score: float = Field(0.0, description="Score from 0.0 (low) to 5.0 (high)")
    urgency_reasons: List[str] = Field(default_factory=list, description="Urgency triggers found")

class PersonalizationResult(BaseModel):
    priority_score: float = Field(0.0, description="Priority rating from 0.0 to 5.0")
    trust_score: float = Field(0.0, description="Trust index based on sender reports")
    relationship_score: float = Field(0.0, description="User response rate / muting weight")
    reasons: List[str] = Field(default_factory=list, description="Personalization justifications")

class MessageProcessingResult(BaseModel):
    message_id: str = Field(..., description="Message ID associated with prediction")
    message_type: str = Field(..., description="Message category (personal, promotion, scam, spam, etc.)")
    action: str = Field(..., description="Selected routing action (notify, digest, mute)")
    confidence: float = Field(..., description="Calibrated engine certainty (0.0 to 1.0)")
    reason: str = Field(..., description="Human-readable decision explanation")
    safety_result: SafetyResult = Field(..., description="Prompt injection and threat details")
    urgency_result: UrgencyResult = Field(..., description="Urgency parsing details")
    personalization_result: PersonalizationResult = Field(..., description="Personalization scoring weights")
    evidence_message_ids: str = Field("none", description="Semicolon separated relevant history message IDs")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata logs (timestamps, version)")
