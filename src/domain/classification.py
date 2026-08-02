import re
from typing import Dict, Any, List
from src.domain.preprocessing import has_word_match
from src.application.schemas import SafetyResult

class MessageClassifier:
    def __init__(self):
        # Category patterns using token boundary matching
        self.spam_keywords = ["win", "winner", "winning", "lottery", "cashback", "lucky draw", "jackpot", "prize desk"]
        self.promotion_keywords = ["sale", "off", "discount", "offer", "coupon", "marketing", "unsubscribe", "try50", 
                                   "kurta set", "denim jacket", "promo", "selling", "sell", "interested", "dm if", "dm"]
        self.greeting_keywords = ["good morning", "good evening", "sabko", "positive energy", "blessings", "vibes", "how are you", "hope today is peaceful"]
        
        self.forward_phrases = ["forward this", "luck changes", "sharing here", "forward to family"]
        self.forward_words = ["fwd"]
        
        self.urgent_keywords = ["prod review", "bridge now", "escalation", "incident bridge", "emergency", "critical", 
                                "blocking", "asap", "immediate", "immediately", "deadline", "penalty list", "heads-up", "water now", "now", "warning", "attention", "urgent request"]
        self.negate_urgency = ["nothing urgent", "no urgency", "no rush", "whenever", "not urgent", "whenever you get time"]
        
        self.payment_keywords = ["due", "payment", "transaction", "amount due", "credit card bill", "bill", "invoice", "rewards"]
        self.event_keywords = ["parents", "school parents", "circular", "field trip", "internship", "faculty advising", 
                               "consent", "meeting", "standup", "class", "session", "cultural", "celebration", "gathering", 
                               "festival", "party", "club", "form is open", "sheet", "appointment", "clinic", "prescription", "doctor"]
        self.update_keywords = ["order", "packed", "shipped", "delivered", "hub", "delivery-code", "tracking", "fedex", 
                                "delivery attempt", "pickup", "driver", "route status", "scheduled between"]
        
        self.is_safety_advisory_pattern = r"\bsafety advisory\b|\bsecurity advisory\b|\bnever ask\b"

    def classify(
        self, 
        text: str, 
        msg: Dict[str, Any], 
        sender_profile: Dict[str, Any], 
        historical_stats: Dict[str, Any],
        safety: SafetyResult,
        has_credentials_request: bool
    ) -> str:
        """
        Layered Message Classifier:
        Layer 1: Deterministic rules (keyword scans)
        Layer 2: Context / Evidence checks (conversation type, business categories)
        Layer 3: AI Provider delegates (future stubs)
        """
        text_to_analyze = text or ""
        text_lower = text_to_analyze.lower()
        conv_type = msg.get('conversation_type')
        media_type = msg.get('media_type')

        # Safety override mapping
        if safety.detected:
            indicators = safety.matched_indicators
            is_impersonation = (
                "brand impersonation" in safety.sanitized_text or 
                "domain mismatch" in safety.sanitized_text or 
                has_credentials_request
            )
            if "user reported" in indicators:
                return 'scam' if has_credentials_request else 'spam'
            if has_credentials_request:
                return 'scam'
            return 'scam' if is_impersonation else 'spam'

        # --- Layer 1: Deterministic Rules ---
        is_spam = has_word_match(text_to_analyze, self.spam_keywords)
        is_promotion = has_word_match(text_to_analyze, self.promotion_keywords)
        is_greeting = has_word_match(text_to_analyze, self.greeting_keywords)
        
        is_forward = (
            has_word_match(text_to_analyze, self.forward_words) or 
            any(phrase in text_lower for phrase in self.forward_phrases) or 
            msg.get('forwarded_count', 0) > 3
        )
        
        has_negation = has_word_match(text_to_analyze, self.negate_urgency)
        is_urgent = has_word_match(text_to_analyze, self.urgent_keywords) and not has_negation
        is_payment = has_word_match(text_to_analyze, self.payment_keywords)
        is_event = has_word_match(text_to_analyze, self.event_keywords)
        is_update = has_word_match(text_to_analyze, self.update_keywords)
        is_safety_advisory = bool(re.search(self.is_safety_advisory_pattern, text_lower))

        # --- Layer 2: Context & Evidence ---
        msg_type = 'unknown'

        if is_greeting:
            msg_type = 'greeting'
        elif is_forward:
            msg_type = 'forward'
        elif is_safety_advisory:
            msg_type = 'business_update'
        elif is_promotion:
            msg_type = 'promotion'
        elif is_urgent:
            msg_type = 'urgent'
        elif is_payment:
            msg_type = 'payment'
        elif is_event:
            msg_type = 'event'
        elif is_update and conv_type == 'business':
            msg_type = 'business_update'
        elif conv_type == 'personal':
            msg_type = 'personal'
        elif conv_type == 'group':
            msg_type = 'personal'
        elif conv_type == 'business':
            category = sender_profile.get('category', 'utilities')
            if category == 'healthcare':
                msg_type = 'event' if is_event else 'business_update'
            elif category in ['ecommerce_delivery', 'logistics', 'utilities']:
                msg_type = 'business_update'
            elif category in ['bank', 'payments', 'fintech']:
                msg_type = 'payment'
            else:
                msg_type = 'business_update'
                
        has_fast_historical_reply = historical_stats.get('has_fast_historical_reply', False)
        if media_type == 'voice' and conv_type != 'business' and has_fast_historical_reply:
            msg_type = 'urgent'
            
        if conv_type == 'personal' and historical_stats.get('total_count', 0) == 0:
            if msg_type not in ['scam', 'spam', 'urgent', 'payment']:
                msg_type = 'unknown'
                
        if is_spam:
            msg_type = 'spam'

        return msg_type
