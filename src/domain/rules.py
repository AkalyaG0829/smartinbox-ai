import re
import datetime
from typing import Dict, Any, List

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

def is_in_dnd_window(created_at: str, dnd_window: str) -> bool:
    """Checks if message timestamp is within the DND window (e.g. '22:00-07:00')."""
    if not isinstance(dnd_window, str) or '-' not in dnd_window:
        return False
    try:
        # Expected formats: 'YYYY-MM-DD HH:MM:SS' or ISO formats
        # We parse the time component
        dt = datetime.datetime.fromisoformat(created_at.replace(" ", "T"))
        t = dt.time()
        start_str, end_str = dnd_window.split('-')
        
        # Parse start and end times
        start_t = datetime.datetime.strptime(start_str.strip(), "%H:%M").time()
        end_t = datetime.datetime.strptime(end_str.strip(), "%H:%M").time()
        
        if start_t <= end_t:
            return start_t <= t <= end_t
        else:
            return t >= start_t or t <= end_t
    except Exception:
        # Fallback parsing
        try:
            # Try simple time splitting if timestamp only contains HH:MM:SS
            time_part = created_at.split()[1] if ' ' in created_at else created_at
            h, m = map(int, time_part.split(':')[:2])
            t = datetime.time(h, m)
            start_str, end_str = dnd_window.split('-')
            sh, sm = map(int, start_str.split(':'))
            eh, em = map(int, end_str.split(':'))
            start_t = datetime.time(sh, sm)
            end_t = datetime.time(eh, em)
            if start_t <= end_t:
                return start_t <= t <= end_t
            else:
                return t >= start_t or t <= end_t
        except Exception:
            return False

class MessageRouterRules:
    @staticmethod
    def classify_and_route(
        msg: Dict[str, Any],
        user_pref: Dict[str, Any],
        sender_profile: Dict[str, Any],
        historical_stats: Dict[str, Any],
        evidence_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Processes a single message against routing heuristics.
        
        Args:
            msg: message dict containing text, conversation_type, media details etc.
            user_pref: user preference settings like dnd_window, is_muted etc.
            sender_profile: details on sender (verified status, domains, reports)
            historical_stats: summary rates (reply_rate, dismissal_rate, report_rate)
            evidence_ids: list of matched evidence message_ids
            
        Returns:
            Dict containing action, message_type, reason, confidence, evidence_message_ids
        """
        text = msg.get('message_text') or ""
        conv_type = msg.get('conversation_type')
        evidence_str = ";".join(evidence_ids) if evidence_ids else "none"
        
        text_to_analyze = text
        text_lower = text_to_analyze.lower()
        
        # 1. Compile content signals
        # OTP / Phishing
        credential_keywords = ["otp", "verification code", "verification link", "password", "login code", "login link", 
                               "six digit", "6 digit", "verification pending", "confirm card", "confirm password", 
                               "profile will be blocked", "wallet verification failed", "account-login.in", "verify now", "verification code abhi"]
        has_credentials_request = has_word_match(text_to_analyze, credential_keywords)
        
        # Urgency signals
        negate_urgency = ["nothing urgent", "no urgency", "no rush", "whenever", "not urgent", "whenever you get time"]
        has_negation = has_word_match(text_to_analyze, negate_urgency)
        urgent_keywords = ["prod review", "bridge now", "escalation", "incident bridge", "emergency", "critical", 
                           "blocking", "asap", "immediate", "immediately", "deadline", "penalty list", "heads-up", "water now", "now", "warning", "attention", "urgent request"]
        is_urgent = has_word_match(text_to_analyze, urgent_keywords) and not has_negation
        
        # Events
        event_keywords = ["parents", "school parents", "circular", "field trip", "internship", "faculty advising", 
                          "consent", "meeting", "standup", "class", "session", "cultural", "celebration", "gathering", 
                          "festival", "party", "club", "form is open", "sheet", "appointment", "clinic", "prescription", "doctor"]
        is_event = has_word_match(text_to_analyze, event_keywords)
        
        # Payments
        payment_keywords = ["due", "payment", "transaction", "amount due", "credit card bill", "bill", "invoice", "rewards"]
        is_payment = has_word_match(text_to_analyze, payment_keywords)
        
        # Promotions
        promotion_keywords = ["sale", "off", "discount", "offer", "coupon", "marketing", "unsubscribe", "try50", 
                              "kurta set", "denim jacket", "promo", "selling", "sell", "interested", "dm if", "dm"]
        is_promotion = has_word_match(text_to_analyze, promotion_keywords)
        
        # Updates
        update_keywords = ["order", "packed", "shipped", "delivered", "hub", "delivery-code", "tracking", "fedex", 
                           "delivery attempt", "pickup", "driver", "route status", "scheduled between"]
        is_update = has_word_match(text_to_analyze, update_keywords)

        # Greetings & Forwards
        greeting_keywords = ["good morning", "good evening", "sabko", "positive energy", "blessings", "vibes", "how are you", "hope today is peaceful"]
        is_greeting = has_word_match(text_to_analyze, greeting_keywords)
        
        forward_phrases = ["forward this", "luck changes", "sharing here", "forward to family"]
        is_forward = (has_word_match(text_to_analyze, ["fwd"]) or 
                      any(phrase in text_lower for phrase in forward_phrases) or 
                      msg.get('forwarded_count', 0) > 3)
                      
        is_safety_advisory = "safety advisory" in text_lower or "security advisory" in text_lower or "never ask" in text_lower

        # Spam
        spam_keywords = ["win", "winner", "winning", "lottery", "cashback", "lucky draw", "jackpot", "prize desk"]
        is_spam = has_word_match(text_to_analyze, spam_keywords)
        
        # Direct mention & group admin indicators
        is_mentioned = msg.get('is_mentioned', False)
        is_sender_admin = msg.get('is_sender_admin', False)
        group_muted = user_pref.get('group_muted', False)
        
        # Quick check if sender is unverified business
        is_unverified_business = False
        if conv_type == 'business':
            is_unverified_business = sender_profile.get('verified', 0) == 0
            
        has_fast_historical_reply = historical_stats.get('has_fast_historical_reply', False)

        # 2. High-Priority Safety Overrides
        is_scam_or_phish = False
        safety_reason = ""
        
        # Block immediately if user has historically reported this sender
        if historical_stats.get('reported_count', 0) > 0:
            return {
                'action': 'mute',
                'message_type': 'scam' if has_credentials_request else 'spam',
                'reason': "Sender has been historically reported by the user for unwanted or suspicious content.",
                'confidence': 0.95,
                'evidence_message_ids': evidence_str
            }

        if conv_type == 'business':
            # Check domain mismatch
            official_domain = sender_profile.get('official_domain')
            if not official_domain or str(official_domain) == 'nan':
                official_domain = ""
            official_domain = str(official_domain).strip()

            domain_used = sender_profile.get('domain_used_by_sender')
            if not domain_used or str(domain_used) == 'nan':
                domain_used = ""
            domain_used = str(domain_used).strip()
            
            if official_domain != domain_used:
                if is_unverified_business:
                    is_scam_or_phish = True
                    is_impersonator = official_domain != ""
                    if is_impersonator:
                        safety_reason = "Unverified business brand impersonation detected via domain mismatch."
                    else:
                        safety_reason = "Unverified business sender using a suspicious domain."
            
            # Credentials requests by unverified business
            if has_credentials_request and is_unverified_business:
                is_scam_or_phish = True
                safety_reason = "Unverified business requests sensitive login, OTP, or verification info."
                
            # Extremely high reports on unverified business
            if is_unverified_business and sender_profile.get('user_reports_30d', 0) > 20:
                is_scam_or_phish = True
                safety_reason = "Unverified business account with extremely high report volume."
                
        elif conv_type in ['personal', 'group']:
            if has_credentials_request:
                # If first-time or no interaction
                if historical_stats.get('total_count', 0) == 0 or historical_stats.get('reply_rate', 0.0) == 0.0:
                    is_scam_or_phish = True
                    safety_reason = "Untrusted or first-time contact requesting sensitive verification codes or passwords."

        if is_scam_or_phish:
            is_impersonation = "impersonation" in safety_reason or "domain mismatch" in safety_reason or has_credentials_request
            return {
                'action': 'mute',
                'message_type': 'scam' if is_impersonation else 'spam',
                'reason': safety_reason,
                'confidence': 0.95,
                'evidence_message_ids': evidence_str
            }

        # 3. Personalized Scoring Engine
        notify_score = 0.0
        digest_score = 0.0
        mute_score = 0.0
        
        # Heuristics logic
        if is_spam:
            mute_score += 5.0
        elif is_promotion:
            if conv_type == 'business':
                if sender_profile.get('allows_promotions', True) and sender_profile.get('has_relationship', False):
                    digest_score += 3.0
                else:
                    mute_score += 4.0
            else:
                digest_score += 3.0
        elif is_greeting or is_forward:
            # Check noise engagement
            if historical_stats.get('total_count', 0) > 0 and (
                historical_stats.get('dismissal_rate', 0.0) >= 0.5 or 
                historical_stats.get('mute_rate', 0.0) >= 0.5 or 
                (historical_stats.get('reply_rate', 0.0) == 0.0 and historical_stats.get('dismissal_rate', 0.0) > 0)
            ):
                mute_score += 4.0
            else:
                digest_score += 3.0
        elif is_urgent or has_fast_historical_reply:
            notify_score += 4.0
        elif is_payment:
            if conv_type == 'business' and sender_profile.get('has_relationship', False):
                notify_score += 2.5
            else:
                digest_score += 2.0
        elif is_event:
            if conv_type == 'business' and sender_profile.get('has_relationship', False):
                notify_score += 2.5
            else:
                digest_score += 2.0
        elif is_update:
            if conv_type == 'business' and sender_profile.get('has_relationship', False):
                notify_score += 2.5
            else:
                digest_score += 2.0
        else:
            # Defaults
            if conv_type == 'personal':
                if historical_stats.get('total_count', 0) > 0 and historical_stats.get('reply_rate', 0.0) > 0.5:
                    notify_score += 2.0
                else:
                    digest_score += 2.0
            else:
                digest_score += 2.0

        # Low Urgency penalty
        low_urgency_keywords = ["whenever you get time", "whenever convenient", "no urgency", "no pressure", 
                                "no rush", "no need to reply", "nothing urgent", "read it before", "if you get time"]
        is_low_urgency = has_word_match(text_to_analyze, low_urgency_keywords)
        if is_low_urgency:
            notify_score -= 5.0
            digest_score += 3.0

        # Group Muting logic
        if conv_type == 'group':
            if group_muted:
                if is_mentioned and (is_urgent or has_fast_historical_reply) and not is_low_urgency:
                    notify_score = 4.0
                elif is_mentioned:
                    notify_score = 0.0
                    digest_score = 3.0
                else:
                    notify_score = -5.0
                    if is_greeting or is_forward or is_promotion:
                        mute_score += 5.0
                    else:
                        digest_score += 2.0
            else:
                if is_mentioned and not is_low_urgency:
                    notify_score += 3.0
                elif is_sender_admin and (is_urgent or is_event) and not is_low_urgency:
                    notify_score += 2.5
                else:
                    digest_score += 2.0

        # Unverified business penalty
        if conv_type == 'business' and is_unverified_business:
            if not sender_profile.get('has_relationship', False):
                mute_score = 6.0
                notify_score = 0.0
                digest_score = 0.0

        # Feedback surveys suppression
        feedback_keywords = ["fill a review", "give feedback", "experience", "how has your", "rate"]
        is_feedback = has_word_match(text_to_analyze, feedback_keywords)
        if is_feedback:
            notify_score = 0.0
            digest_score = 4.0

        # DND Suppressions
        is_suppressed_by_dnd = False
        dnd_window = user_pref.get('do_not_disturb_window')
        created_at = msg.get('created_at')
        if dnd_window and created_at and is_in_dnd_window(created_at, dnd_window):
            is_emergency = (is_urgent or has_fast_historical_reply) and (
                conv_type == 'personal' or (conv_type == 'group' and is_mentioned)
            )
            if not is_emergency:
                is_suppressed_by_dnd = True
                
        if is_suppressed_by_dnd and notify_score > digest_score:
            notify_score = 0.0
            digest_score = 4.0

        # Decision Output
        if mute_score > notify_score and mute_score > digest_score:
            action = 'mute'
            reason = "Message is a promotion or spam from an unverified, muted, or low-trust sender."
            if is_spam:
                reason = "Message contains generic spam, promotional lottery, or cashback triggers."
            elif is_promotion:
                reason = "Promotional message from a business the user has not opted into or opted out of."
        elif notify_score > digest_score:
            action = 'notify'
            reason = "Time-sensitive message from a trusted or close contact demanding immediate attention."
            if conv_type == 'group':
                if is_mentioned:
                    reason = "User is directly mentioned in active group chat."
                elif is_sender_admin:
                    reason = "Time-sensitive operational update sent by group admin."
            elif conv_type == 'business':
                reason = "Time-sensitive service update matching active customer history."
        else:
            action = 'digest'
            reason = "Low-priority message or general communication, suitable for later reading."
            if is_suppressed_by_dnd:
                reason = f"Notification suppressed to digest during user's DND window ({dnd_window})."
            elif is_feedback:
                reason = "Service update or statement notification, suitable for digest."
            elif group_muted:
                reason = "Group is muted by the user; general activity is suppressed."

        # 4. Message Type Resolution
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
                
        # Media type voice notes override
        if msg.get('media_type') == 'voice' and conv_type != 'business' and has_fast_historical_reply:
            msg_type = 'urgent'
            
        # Unfamiliar sender override
        if conv_type == 'personal' and historical_stats.get('total_count', 0) == 0:
            if msg_type not in ['scam', 'spam', 'urgent', 'payment']:
                msg_type = 'unknown'
                
        if is_spam:
            msg_type = 'spam'

        # 5. Confidence Calibration
        confidence = 0.70
        if action == 'mute':
            if is_spam or historical_stats.get('reported_count', 0) > 0:
                confidence = 0.95
            else:
                confidence = 0.90
        elif action == 'notify':
            if has_fast_historical_reply or is_mentioned:
                confidence = 0.92
            else:
                confidence = 0.85
        else:
            if is_suppressed_by_dnd or group_muted:
                confidence = 0.90
            elif historical_stats.get('total_count', 0) > 0:
                confidence = 0.82

        return {
            'action': action,
            'message_type': msg_type,
            'reason': reason,
            'confidence': round(confidence, 2),
            'evidence_message_ids': evidence_str
        }
