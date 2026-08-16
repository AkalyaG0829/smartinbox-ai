import datetime
from typing import Dict, Any, List

from src.domain.preprocessing import MessagePreprocessor, get_jaccard_similarity, has_word_match
from src.domain.safety import PromptInjectionShield, SafetyResult
from src.domain.urgency import UrgencyAnalyzer
from src.domain.classification import MessageClassifier
from src.domain.personalization import PersonalizationEngine
from src.domain.confidence import ConfidenceScorer
from src.domain.action_policy import ActionPolicyEngine

def is_in_dnd_window(created_at: str, dnd_window: str) -> bool:
    if not isinstance(dnd_window, str) or '-' not in dnd_window:
        return False
    try:
        dt = datetime.datetime.fromisoformat(created_at.replace(" ", "T"))
        t = dt.time()
        start_str, end_str = dnd_window.split('-')
        start_t = datetime.datetime.strptime(start_str.strip(), "%H:%M").time()
        end_t = datetime.datetime.strptime(end_str.strip(), "%H:%M").time()
        if start_t <= end_t:
            return start_t <= t <= end_t
        else:
            return t >= start_t or t <= end_t
    except Exception:
        try:
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
        Backward compatible wrapper that instantiates and delegates execution
        to the newly decoupled Phase 2 domain engines.
        """
        raw_text = msg.get('message_text') or ""
        conv_type = msg.get('conversation_type')
        evidence_str = ";".join(evidence_ids) if evidence_ids else "none"

        # 1. Preprocessing Layer
        preprocessed_text = MessagePreprocessor.preprocess(raw_text)

        # 2. Safety & Prompt Injection Shield
        shield = PromptInjectionShield()
        safety_res = shield.scan(preprocessed_text)

        # Untrusted credentials request check
        credential_keywords = ["otp", "verification code", "verification link", "password", "login code", "login link",
                               "six digit", "6 digit", "verification pending", "confirm card", "confirm password",
                               "profile will be blocked", "wallet verification failed", "account-login.in", "verify now", "verification code abhi"]
        has_credentials_request = has_word_match(preprocessed_text, credential_keywords)

        is_unverified_business = conv_type == 'business' and sender_profile.get('verified', 0) == 0

        # Accumulate safety indicators to prevent overwrites
        matched_indicators = []
        sanitized_text = ""

        if safety_res.detected:
            matched_indicators.extend(safety_res.matched_indicators)
            sanitized_text = safety_res.sanitized_text

        # Inject user reported stats override
        if historical_stats.get('reported_count', 0) > 0:
            matched_indicators.append("user reported")
            if not sanitized_text:
                sanitized_text = "reported"

        # If personal/group and untrusted credentials request
        if conv_type in ['personal', 'group'] and has_credentials_request:
            if historical_stats.get('total_count', 0) == 0 or historical_stats.get('reply_rate', 0.0) == 0.0:
                matched_indicators.append("untrusted credential request")
                sanitized_text = "untrusted"

        # Unverified business requests credentials mismatch override
        if conv_type == 'business' and is_unverified_business and has_credentials_request:
            matched_indicators.append("unverified business credential request")
            sanitized_text = "unverified business"

        # Domain mismatch override
        if conv_type == 'business' and is_unverified_business:
            official_domain = sender_profile.get('official_domain') or ""
            if str(official_domain) == 'nan':
                official_domain = ""
            official_domain = str(official_domain).strip()

            domain_used = sender_profile.get('domain_used_by_sender') or ""
            if str(domain_used) == 'nan':
                domain_used = ""
            domain_used = str(domain_used).strip()

            if official_domain != domain_used:
                is_impersonator = official_domain != ""
                matched_indicators.append("domain mismatch")
                sanitized_text = "brand impersonation" if is_impersonator else "suspicious domain"

        if matched_indicators:
            safety_res = SafetyResult(
                detected=True,
                risk_level="high",
                matched_indicators=matched_indicators,
                sanitized_text=sanitized_text
            )

        # 3. Message Classifier Engine
        classifier = MessageClassifier()
        msg_type = classifier.classify(
            preprocessed_text, msg, sender_profile, historical_stats, safety_res, has_credentials_request
        )

        # 4. Urgency Analyzer Engine
        urgency_analyzer = UrgencyAnalyzer()
        urgency_res = urgency_analyzer.analyze(preprocessed_text)

        # Low Urgency penalty check
        low_urgency_keywords = ["whenever you get time", "whenever convenient", "no urgency", "no pressure",
                                "no rush", "no need to reply", "nothing urgent", "read it before", "if you get time"]
        is_low_urgency = has_word_match(preprocessed_text, low_urgency_keywords)
        if is_low_urgency:
            urgency_res.is_urgent = False
            urgency_res.urgency_score = 0.0

        # Feedback survey check
        feedback_keywords = ["fill a review", "give feedback", "experience", "how has your", "rate"]
        is_feedback = has_word_match(preprocessed_text, feedback_keywords)

        # 5. Personalization Engine
        personalization_engine = PersonalizationEngine()
        personalization_res = personalization_engine.evaluate(
            msg, user_pref, sender_profile, historical_stats
        )

        # 6. DND windows checking
        is_suppressed_by_dnd = False
        dnd_window = user_pref.get('do_not_disturb_window')
        created_at = msg.get('created_at')
        if dnd_window and created_at and is_in_dnd_window(created_at, dnd_window):
            is_emergency = (msg_type == 'urgent' or urgency_res.is_urgent or historical_stats.get('has_fast_historical_reply', False)) and (
                conv_type == 'personal' or (conv_type == 'group' and msg.get('is_mentioned', False))
            )
            if not is_emergency:
                is_suppressed_by_dnd = True

        # Check group muted overrides
        group_muted = user_pref.get('group_muted', False)

        # Setup exact keyword booleans for ActionPolicyEngine
        is_spam = has_word_match(preprocessed_text, classifier.spam_keywords)
        is_promotion = has_word_match(preprocessed_text, classifier.promotion_keywords)
        is_greeting = has_word_match(preprocessed_text, classifier.greeting_keywords)
        is_forward = (
            has_word_match(preprocessed_text, classifier.forward_words) or
            any(phrase in preprocessed_text.lower() for phrase in classifier.forward_phrases) or
            msg.get('forwarded_count', 0) > 3
        )
        is_urgent = urgency_res.is_urgent
        is_payment = has_word_match(preprocessed_text, classifier.payment_keywords)
        is_event = has_word_match(preprocessed_text, classifier.event_keywords)
        is_update = has_word_match(preprocessed_text, classifier.update_keywords)

        has_fast_historical_reply = historical_stats.get('has_fast_historical_reply', False)
        is_mentioned = msg.get('is_mentioned', False)
        is_sender_admin = msg.get('is_sender_admin', False)
        semantic_scores = msg.get('semantic_scores')

        # 7. Action Decision Engine
        action_res = ActionPolicyEngine.evaluate_action(
            msg_type=msg_type,
            urgency=urgency_res,
            personalization=personalization_res,
            safety=safety_res,
            user_pref=user_pref,
            sender_profile=sender_profile,
            conv_type=conv_type,
            is_suppressed_by_dnd=is_suppressed_by_dnd,
            historical_stats=historical_stats,
            is_spam=is_spam,
            is_promotion=is_promotion,
            is_greeting=is_greeting,
            is_forward=is_forward,
            is_urgent=is_urgent,
            is_payment=is_payment,
            is_event=is_event,
            is_update=is_update,
            is_feedback=is_feedback,
            is_low_urgency=is_low_urgency,
            has_fast_historical_reply=has_fast_historical_reply,
            is_mentioned=is_mentioned,
            is_sender_admin=is_sender_admin,
            semantic_scores=semantic_scores
        )

        # 8. Confidence Calibrations
        is_dnd_muted = is_suppressed_by_dnd or group_muted
        conf_res = ConfidenceScorer.calculate(
            action_res['action'], msg_type, historical_stats, personalization_res, is_dnd_muted
        )

        return {
            'action': action_res['action'],
            'message_type': msg_type,
            'reason': action_res['reason'],
            'confidence': conf_res['score'],
            'evidence_message_ids': evidence_str
        }
