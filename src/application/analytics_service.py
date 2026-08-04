from sqlalchemy.orm import Session
from src.infrastructure.models import UserInteraction, RoutingDecision, Message
from typing import Dict, Any

class AnalyticsService:
    @staticmethod
    def get_routing_alignment_analytics(db: Session) -> Dict[str, Any]:
        """
        Calculates the Routing Decision Alignment Analytics.
        Joins RoutingDecision and UserInteraction to determine if the system's
        action matches the user's actual behavior.
        """
        # Fetch all matching interaction/decision pairs
        results = db.query(RoutingDecision, UserInteraction).join(
            Message, RoutingDecision.message_id == Message.id
        ).join(
            UserInteraction, UserInteraction.message_id == Message.id
        ).all()

        total_actions = len(results)
        
        if total_actions == 0:
            return {
                "alignment_rate": 0.0,
                "total_actions": 0,
                "aligned_count": 0,
                "misaligned_count": 0,
                "mismatches": []
            }

        aligned_count = 0
        misaligned_count = 0
        mismatches = []

        for decision, interaction in results:
            is_aligned = False
            
            if decision.action == 'notify':
                # Aligned if user opened or replied
                if interaction.opened or interaction.replied:
                    is_aligned = True
            
            elif decision.action == 'mute':
                # Aligned if user reported, dismissed, or ignored (not opened, not replied)
                if interaction.reported or interaction.dismissed or (not interaction.opened and not interaction.replied):
                    is_aligned = True
            
            elif decision.action == 'digest':
                # Aligned if opened and not replied and not reported
                if interaction.opened and not interaction.replied and not interaction.reported:
                    is_aligned = True
            
            if is_aligned:
                aligned_count += 1
            else:
                misaligned_count += 1
                mismatches.append({
                    "message_id": decision.message_id,
                    "action": decision.action,
                    "message_type": decision.message_type,
                    "reason": decision.reason,
                    "interaction": {
                        "opened": interaction.opened,
                        "replied": interaction.replied,
                        "dismissed": interaction.dismissed,
                        "reported": interaction.reported
                    }
                })
        
        alignment_rate = round((aligned_count / total_actions) * 100, 2)
        
        return {
            "alignment_rate": alignment_rate,
            "total_actions": total_actions,
            "aligned_count": aligned_count,
            "misaligned_count": misaligned_count,
            "mismatches": mismatches
        }
