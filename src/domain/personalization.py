from typing import Dict, Any, List
from src.application.schemas import PersonalizationResult

class PersonalizationEngine:
    def __init__(self):
        pass

    def evaluate(
        self, 
        msg: Dict[str, Any], 
        user_pref: Dict[str, Any], 
        sender_profile: Dict[str, Any], 
        historical_stats: Dict[str, Any]
    ) -> PersonalizationResult:
        """
        Processes historical statistics and sender trust metrics to calculate 
        reusable personalization scores.
        """
        reasons = []
        
        # 1. Compute trust score (0.0 to 5.0)
        trust = 3.5
        if sender_profile.get('verified', 0) == 1:
            trust += 1.5
            reasons.append("Sender is a verified official brand")
            
        reports = sender_profile.get('user_reports_30d', 0)
        if reports > 0:
            penalty = min(reports * 0.2, 3.5)
            trust -= penalty
            reasons.append(f"Sender has {reports} global user reports in the last 30 days")
            
        hist_reports = historical_stats.get('reported_count', 0)
        if hist_reports > 0:
            trust = 0.0
            reasons.append("Sender was previously reported by the receiving user")

        trust = max(0.0, min(5.0, trust))

        # 2. Compute relationship score (0.0 to 5.0)
        relationship = 2.0
        total_pings = historical_stats.get('total_count', 0)
        
        if total_pings > 0:
            reply_rate = historical_stats.get('reply_rate', 0.0)
            dismissal_rate = historical_stats.get('dismissal_rate', 0.0)
            mute_rate = historical_stats.get('mute_rate', 0.0)
            
            if reply_rate > 0.5:
                relationship += 2.0
                reasons.append(f"Highly engaged conversation history (reply rate: {reply_rate:.1%})")
            elif reply_rate > 0.0:
                relationship += 1.0
                
            if dismissal_rate >= 0.5:
                relationship -= 1.5
                reasons.append(f"User frequently dismisses notifications from this sender (dismissal rate: {dismissal_rate:.1%})")
                
            if mute_rate >= 0.5:
                relationship -= 1.5
                reasons.append("User has historically muted chats after receiving messages from this sender")
        else:
            reasons.append("First-time sender contact")

        relationship = max(0.0, min(5.0, relationship))

        # 3. Compute priority score (0.0 to 5.0)
        priority = 2.0
        
        if msg.get('is_mentioned', False):
            priority += 2.5
            reasons.append("User is directly mentioned in the message text")
            
        if msg.get('is_sender_admin', False):
            priority += 1.5
            reasons.append("Message sender is a group administrator")
            
        if historical_stats.get('has_fast_historical_reply', False):
            priority += 1.5
            reasons.append("User historically replies to this sender within 5 minutes")

        priority = max(0.0, min(5.0, priority))

        return PersonalizationResult(
            priority_score=round(priority, 2),
            trust_score=round(trust, 2),
            relationship_score=round(relationship, 2),
            reasons=reasons
        )
