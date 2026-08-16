import math
from typing import Dict, Any

class SemanticClassifier:
    def __init__(self, embedding_provider: Any):
        self.provider = embedding_provider
        self.notify_archetypes = [
            "medical emergency, heart attack, hospitalized, critically ill, injured",
            "production database is down, customers cannot access the application, server outage",
            "security breach, account compromised, unauthorized access",
            "serious emergency at home, you need to come right now, get here immediately"
        ]
        self.important_archetypes = [
            "interview is scheduled, please confirm your attendance",
            "project report deadline, submit before Friday",
            "appointment has been scheduled, please confirm",
            "team meeting, project review, standup",
            "review and sign the attached contract, sign documents by EOD"
        ]
        self.ignore_archetypes = [
            "congratulations, you won a free vacation, click here to claim your prize",
            "exclusive promotional reward, click now to claim",
            "limited time offer, buy now and receive a special discount",
            "lottery winner, jackpot, cashback",
            "urgent account locked, verify immediately, phishing scam",
            "summer sale, great deals inside, discount code"
        ]
        self.digest_archetypes = [
            "monthly company newsletter with the latest updates",
            "good morning, hope you are having a great day",
            "team shared the latest product updates for everyone to read",
            "casual conversation, informational update, non-actionable"
        ]

    async def get_scores(self, text: str) -> Dict[str, float]:
        if not text or not self.provider:
            return {"notify": 0.0, "important": 0.0, "ignore": 0.0, "digest": 0.0}

        try:
            v = await self.provider.get_embedding(text)
        except Exception:
            return {"notify": 0.0, "important": 0.0, "ignore": 0.0, "digest": 0.0}
        
        def cosine_similarity(v1, v2):
            dot = sum(a*b for a,b in zip(v1, v2))
            norm1 = math.sqrt(sum(a*a for a in v1))
            norm2 = math.sqrt(sum(b*b for b in v2))
            return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

        scores = {"notify": 0.0, "important": 0.0, "ignore": 0.0, "digest": 0.0}
        
        try:
            for arch in self.notify_archetypes:
                av = await self.provider.get_embedding(arch)
                scores["notify"] = max(scores["notify"], cosine_similarity(v, av))
                
            for arch in self.important_archetypes:
                av = await self.provider.get_embedding(arch)
                scores["important"] = max(scores["important"], cosine_similarity(v, av))
                
            for arch in self.ignore_archetypes:
                av = await self.provider.get_embedding(arch)
                scores["ignore"] = max(scores["ignore"], cosine_similarity(v, av))
                
            for arch in self.digest_archetypes:
                av = await self.provider.get_embedding(arch)
                scores["digest"] = max(scores["digest"], cosine_similarity(v, av))
        except Exception:
            pass
            
        return scores
