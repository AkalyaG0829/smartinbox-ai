from typing import Dict, Any, List

class ConfidenceScorer:
    @staticmethod
    def calculate(
        action: str, 
        msg_type: str, 
        historical_stats: Dict[str, Any], 
        personalization: Any, 
        is_dnd_muted: bool
    ) -> Dict[str, Any]:
        """
        Calibrates routing confidence based on signal strength.
        """
        score = 0.70
        signals = []

        if action == 'mute':
            if msg_type in ['spam', 'scam'] or historical_stats.get('reported_count', 0) > 0:
                score = 0.95
                signals.append("Verified safety hazard or historical sender report matching")
            else:
                score = 0.90
                signals.append("Baseline promotion/forward suppression rule")
                
        elif action == 'notify':
            has_fast = historical_stats.get('has_fast_historical_reply', False)
            is_high_engaged = personalization.relationship_score >= 4.0
            
            if has_fast or is_high_engaged or personalization.priority_score >= 4.0:
                score = 0.92
                signals.append("Active recipient mention or fast historical engagement matched")
            else:
                score = 0.85
                signals.append("Time-sensitive notification heuristics")
                
        else: # digest
            if is_dnd_muted:
                score = 0.90
                signals.append("System window suppression override (DND or muted channel)")
            elif historical_stats.get('total_count', 0) > 0:
                score = 0.82
                signals.append("Historical sender logs matching suitable digest criteria")
            else:
                score = 0.70
                signals.append("Default low-priority fallback")

        return {
            "score": round(score, 2),
            "signals": signals,
            "explanation": " / ".join(signals)
        }
