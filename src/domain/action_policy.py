from typing import Dict, Any
from src.application.schemas import SafetyResult, UrgencyResult, PersonalizationResult

class ActionPolicyEngine:
    @staticmethod
    def evaluate_action(
        msg_type: str,
        urgency: UrgencyResult,
        personalization: PersonalizationResult,
        safety: SafetyResult,
        user_pref: Dict[str, Any],
        sender_profile: Dict[str, Any],
        conv_type: str,
        is_suppressed_by_dnd: bool,
        historical_stats: Dict[str, Any],
        is_spam: bool,
        is_promotion: bool,
        is_greeting: bool,
        is_forward: bool,
        is_urgent: bool,
        is_payment: bool,
        is_event: bool,
        is_update: bool,
        is_feedback: bool,
        is_low_urgency: bool,
        has_fast_historical_reply: bool,
        is_mentioned: bool,
        is_sender_admin: bool,
        semantic_scores: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Action Policy Engine: Evaluates the exact heuristic scoring algorithms from Phase 1
        using precise keyword signals and personalization results to determine the routing action.
        """
        # 1. High-Priority Safety Overrides
        if safety.detected:
            reason = safety.matched_indicators[0] if safety.matched_indicators else "untrusted"
            actual_reason = safety.sanitized_text if safety.sanitized_text else "Adversarial instructions blocked."
            
            # Map standard override reasons exactly
            if "domain mismatch" in actual_reason or "impersonation" in actual_reason:
                actual_reason = "Unverified business brand impersonation detected via domain mismatch."
            elif "suspicious domain" in actual_reason:
                actual_reason = "Unverified business sender using a suspicious domain."
            elif "reported" in actual_reason or "user reported" in reason:
                actual_reason = "Sender has been historically reported by the user for unwanted or suspicious content."
            elif "untrusted" in actual_reason or "untrusted" in reason:
                actual_reason = "Untrusted or first-time contact requesting sensitive verification codes or passwords."
            elif "unverified business" in actual_reason:
                actual_reason = "Unverified business requests sensitive login, OTP, or verification info."
            else:
                actual_reason = "Unverified business brand impersonation detected via domain mismatch."
                
            return {
                "action": "ignore",
                "reason": actual_reason
            }

        # 2. Personalized Action Scoring Engine
        notify_score = 0.0
        important_score = 0.0
        digest_score = 0.0
        ignore_score = 0.0

        # Extract stats
        total_count = historical_stats.get('total_count', 0)
        reply_rate = historical_stats.get('reply_rate', 0.0)
        dismissal_rate = historical_stats.get('dismissal_rate', 0.0)
        mute_rate = historical_stats.get('mute_rate', 0.0)

        # Content type defaults based on exact keyword booleans
        if is_spam:
            ignore_score += 5.0
        elif is_promotion:
            if conv_type == 'business':
                if sender_profile.get('allows_promotions', True) and sender_profile.get('has_relationship', False):
                    digest_score += 3.0
                else:
                    ignore_score += 4.0
            else:
                digest_score += 3.0
        elif is_greeting or is_forward:
            # Check noise engagement
            if total_count > 0 and (
                dismissal_rate >= 0.5 or 
                mute_rate >= 0.5 or 
                (reply_rate == 0.0 and dismissal_rate > 0)
            ):
                ignore_score += 4.0
            else:
                digest_score += 3.0
        elif is_urgent or has_fast_historical_reply:
            notify_score += 4.0
        elif is_payment:
            if conv_type == 'business' and sender_profile.get('has_relationship', False):
                important_score += 3.0
            else:
                digest_score += 2.0
        elif is_event:
            important_score += 3.0
            notify_score += 1.0 # events can lean to notify if other factors align
        elif is_update:
            important_score += 2.5
        else: # Defaults (personal / unknown / etc.)
            if conv_type == 'personal':
                if total_count > 0 and reply_rate > 0.5:
                    important_score += 2.0
                else:
                    digest_score += 2.0
            else:
                digest_score += 2.0

        # Low Urgency penalty
        if is_low_urgency:
            notify_score -= 5.0
            important_score -= 3.0
            digest_score += 3.0

        # Group Muting Penalties & Overrides
        group_muted = user_pref.get('group_muted', False)
        
        if conv_type == 'group':
            if group_muted:
                if is_mentioned and (is_urgent or has_fast_historical_reply) and not is_low_urgency:
                    notify_score = 4.0
                elif is_mentioned:
                    notify_score = 0.0
                    important_score = 3.0
                else:
                    notify_score = -5.0
                    important_score = -5.0
                    if is_greeting or is_forward or is_promotion:
                        ignore_score += 5.0
                    else:
                        digest_score += 2.0
            else:
                if is_mentioned and not is_low_urgency:
                    notify_score += 3.0
                elif is_sender_admin and (is_urgent or is_event) and not is_low_urgency:
                    notify_score += 2.5
                else:
                    digest_score += 2.0

        # Incorporate Semantic Scores
        if semantic_scores:
            for cat, score in semantic_scores.items():
                if score > 0.45:
                    if cat == 'notify':
                        notify_score += 6.0
                    elif cat == 'important':
                        important_score += 5.0
                    elif cat == 'ignore':
                        ignore_score += 5.0
                    elif cat == 'digest':
                        digest_score += 3.0

        # Business unverified penalty
        is_unverified_business = conv_type == 'business' and sender_profile.get('verified', 0) == 0
        if is_unverified_business:
            if not sender_profile.get('has_relationship', False):
                ignore_score = 6.0
                notify_score = 0.0
                important_score = 0.0
                digest_score = 0.0

        # Suppress feedback surveys
        if is_feedback:
            notify_score = 0.0
            important_score = 0.0
            digest_score = 4.0

        # DND Suppressions
        if is_suppressed_by_dnd and (notify_score > digest_score or important_score > digest_score):
            notify_score = 0.0
            important_score = 0.0
            digest_score = 4.0

        # Select action
        if ignore_score > notify_score and ignore_score > important_score and ignore_score > digest_score:
            action = 'ignore'
            reason = "Message is a promotion or spam from an unverified, muted, or low-trust sender."
            if is_spam:
                reason = "Message contains generic spam, promotional lottery, or cashback triggers."
            elif is_promotion:
                reason = "Promotional message from a business the user has not opted into or opted out of."
        elif notify_score > important_score and notify_score > digest_score:
            action = 'notify'
            reason = "Time-sensitive message from a trusted or close contact demanding immediate attention."
            if conv_type == 'group':
                if is_mentioned:
                    reason = "User is directly mentioned in active group chat."
                elif is_sender_admin:
                    reason = "Time-sensitive operational update sent by group admin."
            elif conv_type == 'business':
                reason = "Time-sensitive service update matching active customer history."
        elif important_score > digest_score:
            action = 'important'
            reason = "Time-sensitive event, update, or important information requiring attention."
        else:
            action = 'digest'
            reason = "Low-priority message or general communication, suitable for later reading."
            dnd_window = user_pref.get('do_not_disturb_window')
            if is_suppressed_by_dnd:
                reason = f"Notification suppressed to digest during user's DND window ({dnd_window})."
            elif is_feedback:
                reason = "Service update or statement notification, suitable for digest."
            elif group_muted:
                reason = "Group is muted by the user; general activity is suppressed."

        return {
            "action": action,
            "reason": reason
        }
