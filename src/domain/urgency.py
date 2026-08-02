import re
from typing import List
from src.application.schemas import UrgencyResult

class UrgencyAnalyzer:
    def __init__(self):
        # Compiled regexes for word boundaries
        self.urgent_keywords = [
            (r"\bprod\s+review\b", "production review request"),
            (r"\bbridge\s+now\b", "bridge attendance call"),
            (r"\bescalation\b", "operational escalation"),
            (r"\bincident\s+bridge\b", "incident coordination"),
            (r"\bemergency\b", "critical emergency"),
            (r"\bcritical\b", "high priority flag"),
            (r"\bblocking\b", "blocker blocker"),
            (r"\basap\b", "asap urgency directive"),
            (r"\bimmediate(ly)?\b", "immediate deadline alert"),
            (r"\bdeadline\b", "deadline target"),
            (r"\bpenalty\s+list\b", "penalty risk list"),
            (r"\bheads-up\b", "heads-up operational notice"),
            (r"\bwater\s+now\b", "water utility emergency"),
            (r"\bnow\b", "now instruction"),
            (r"\bwarning\b", "safety warnings"),
            (r"\battention\b", "operational attention directive"),
            (r"\burgent\s+request\b", "urgent request")
        ]

        self.negation_patterns = [
            r"\bnothing\s+urgent\b",
            r"\bno\s+urgency\b",
            r"\bno\s+rush\b",
            r"\bwhenever\b",
            r"\bnot\s+urgent\b",
            r"\bwhenever\s+you\s+get\s+time\b",
            r"\bwhenever\s+convenient\b",
            r"\bno\s+pressure\b",
            r"\bno\s+need\s+to\s+reply\b",
            r"\bif\s+you\s+get\s+time\b"
        ]

    def analyze(self, text: str) -> UrgencyResult:
        """
        Token-aware urgency parser utilizing word boundaries to prevent substring collisions.
        Returns a structured UrgencyResult.
        """
        if not text:
            return UrgencyResult(is_urgent=False, urgency_score=0.0, urgency_reasons=[])

        text_lower = text.lower()
        
        has_negation = False
        matched_negations = []
        for pattern in self.negation_patterns:
            if re.search(pattern, text_lower):
                has_negation = True
                matched_negations.append(pattern.replace(r"\b", "").strip())
                
        reasons = []
        score = 0.0
        
        for pattern, reason in self.urgent_keywords:
            if re.search(pattern, text_lower):
                reasons.append(reason)
                score += 1.5

        score = min(score, 5.0)

        is_urgent = len(reasons) > 0 and not has_negation
        
        if has_negation:
            score = max(score - 4.0, 0.0)

        return UrgencyResult(
            is_urgent=is_urgent,
            urgency_score=round(score, 2),
            urgency_reasons=reasons
        )
