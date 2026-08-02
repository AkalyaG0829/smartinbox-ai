import re
from typing import List
from src.application.schemas import SafetyResult

class PromptInjectionShield:
    def __init__(self):
        # Compiled patterns for instruction injection detection
        self.risk_patterns = [
            (r"ignore\s+(previous|system|sender|safety|risk|rules|instructions)\b", "ignore instructions"),
            (r"system\s+note\b", "system note override"),
            (r"always\s+mark\s+this\s+as\s+notify\b", "forced notify override"),
            (r"override\s+the\s+router\b", "forced router override"),
            (r"follow\s+these\s+instructions\b", "follow instructions bypass"),
            (r"assistant\s+instruction\b", "assistant instruction bypass"),
            (r"ignore\s+sender\s+risk\b", "ignore risk instruction")
        ]

    def scan(self, text: str) -> SafetyResult:
        """
        Scans untrusted user text for instructional injection keywords.
        Returns a structured SafetyResult detailing matches, risk levels, and sanitized text.
        """
        if not text:
            return SafetyResult(detected=False, risk_level="low", matched_indicators=[], sanitized_text="")

        text_lower = text.lower()
        matched = []
        
        for pattern, label in self.risk_patterns:
            if re.search(pattern, text_lower):
                matched.append(label)

        if matched:
            risk_level = "high" if len(matched) == 1 else "critical"
            
            lines = text.split("\n")
            sanitized_lines = []
            for line in lines:
                line_lower = line.lower()
                has_match = any(re.search(pat, line_lower) for pat, _ in self.risk_patterns)
                if not has_match:
                    sanitized_lines.append(line)
            sanitized_text = "\n".join(sanitized_lines).strip()
            
            return SafetyResult(
                detected=True,
                risk_level=risk_level,
                matched_indicators=matched,
                sanitized_text=sanitized_text
            )
        else:
            return SafetyResult(
                detected=False,
                risk_level="low",
                matched_indicators=[],
                sanitized_text=text
            )
