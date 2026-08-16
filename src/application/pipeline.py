import datetime
import pandas as pd
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.domain.rules import MessageRouterRules, get_jaccard_similarity, is_in_dnd_window
from src.domain.interfaces import SpeechToTextProvider, OCRProvider, EmbeddingProvider, PromptInjectionShield
from src.infrastructure.models import User, Channel, ChannelMember, Contact, Message, RoutingDecision, UserInteraction

# Import Phase 2 decoupled components
from src.domain.preprocessing import MessagePreprocessor, has_word_match
from src.domain.safety import PromptInjectionShield as DomainPromptInjectionShield, SafetyResult
from src.domain.urgency import UrgencyAnalyzer, UrgencyResult
from src.domain.classification import MessageClassifier
from src.domain.personalization import PersonalizationEngine, PersonalizationResult
from src.domain.confidence import ConfidenceScorer
from src.domain.action_policy import ActionPolicyEngine
from src.application.schemas import MessageProcessingRequest, MessageProcessingResult
from src.domain.evidence import EvidenceRetriever

class MessageRoutingPipeline:
    def __init__(
        self,
        db: Optional[Session],
        stt_provider: SpeechToTextProvider,
        ocr_provider: OCRProvider,
        embedding_provider: EmbeddingProvider,
        injection_shield: PromptInjectionShield
    ):
        self.db = db
        self.stt_provider = stt_provider
        self.ocr_provider = ocr_provider
        self.embedding_provider = embedding_provider
        self.injection_shield = injection_shield

    async def route_incoming_message(self, raw_msg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the entire routing pipeline for an incoming message (legacy entry point).
        """
        text_content = raw_msg.get('message_text') or ""
        media_type = raw_msg.get('media_type')
        media_id = raw_msg.get('media_id')
        user_id = raw_msg.get('user_id')
        conv_type = raw_msg.get('conversation_type')

        media_transcript = None

        if media_type == 'voice':
            media_transcript = raw_msg.get('media_transcript')
            if not media_transcript:
                media_transcript = await self.stt_provider.transcribe(None)
        elif media_type == 'image':
            media_transcript = raw_msg.get('media_transcript')
            if not media_transcript:
                media_transcript = await self.ocr_provider.extract_text(None)

        if media_transcript:
            from src.config.settings import settings
            if settings.ENABLE_REDACTION:
                from src.domain.redaction import DataRedactor
                media_transcript = DataRedactor.redact(media_transcript)

        analyzable_text = text_content
        if not analyzable_text.strip() and media_transcript:
            analyzable_text = media_transcript

        if self.injection_shield.scan(analyzable_text):
            evidence_ids = raw_msg.get('evidence_message_ids', '')
            evidence_list = evidence_ids.split(';') if (evidence_ids and evidence_ids != 'none') else []
            decision = {
                'action': 'mute',
                'message_type': 'scam',
                'reason': "Adversarial prompt injection attempt blocked in input stream.",
                'confidence': 0.95,
                'evidence_message_ids': ";".join(evidence_list) if evidence_list else "none"
            }
            try:
                from src.application.metrics import ROUTING_DECISIONS, CONFIDENCE_BANDS
                ROUTING_DECISIONS.labels(action=decision['action']).inc()
                conf_score = float(decision['confidence'])
                band = "high" if conf_score >= 0.8 else ("medium" if conf_score >= 0.5 else "low")
                CONFIDENCE_BANDS.labels(band=band).inc()
            except Exception:
                pass
            return decision

        user_pref = {
            'do_not_disturb_window': None,
            'group_muted': False
        }

        sender_profile = {
            'verified': 0,
            'official_domain': "",
            'domain_used_by_sender': "",
            'user_reports_30d': 0,
            'allows_promotions': True,
            'allows_notifications': True,
            'has_relationship': False,
            'category': 'unknown'
        }

        historical_stats = {
            'total_count': 0,
            'open_rate': 0.5,
            'reply_rate': 0.0,
            'dismissal_rate': 0.0,
            'mute_rate': 0.0,
            'report_rate': 0.0,
            'reported_count': 0,
            'has_fast_historical_reply': False
        }

        evidence_list = []
        if self.db:
            import time
            from src.application.metrics import EMBEDDING_DURATION
            start_time = time.time()
            evidence_list = await self._retrieve_evidence_from_db(raw_msg, analyzable_text)
            duration = time.time() - start_time
            EMBEDDING_DURATION.observe(duration)

            user_obj = self.db.query(User).filter(User.email == user_id).first()
            if not user_obj:
                user_obj = self.db.query(User).filter(User.id == user_id).first()
            if user_obj:
                dnd_start = user_obj.dnd_start_time.strftime("%H:%M") if user_obj.dnd_start_time else "22:00"
                dnd_end = user_obj.dnd_end_time.strftime("%H:%M") if user_obj.dnd_end_time else "07:00"
                user_pref['do_not_disturb_window'] = f"{dnd_start}-{dnd_end}"

            if conv_type == 'group' and raw_msg.get('group_id'):
                chan = self.db.query(Channel).filter(Channel.external_id == raw_msg['group_id']).first()
                if chan and user_obj:
                    member = self.db.query(ChannelMember).filter(
                        ChannelMember.user_id == user_obj.id,
                        ChannelMember.channel_id == chan.id
                    ).first()
                    if member:
                        user_pref['group_muted'] = member.is_muted

            sender_id_val = raw_msg.get('sender_user_id') if conv_type != 'business' else raw_msg.get('business_id')
            if sender_id_val:
                contact_obj = self.db.query(Contact).filter(Contact.id == sender_id_val).first()
                if contact_obj:
                    sender_profile['verified'] = 1 if contact_obj.verified else 0
                    sender_profile['official_domain'] = contact_obj.official_domain or ""
                    sender_profile['domain_used_by_sender'] = contact_obj.sender_domain or ""
                    sender_profile['user_reports_30d'] = contact_obj.report_count_30d
                    sender_profile['allows_promotions'] = contact_obj.allows_promotions
                    sender_profile['has_relationship'] = True
                    sender_profile['category'] = contact_obj.type

        if raw_msg.get('do_not_disturb_window'):
            user_pref['do_not_disturb_window'] = raw_msg['do_not_disturb_window']
        if 'group_muted' in raw_msg:
            user_pref['group_muted'] = raw_msg['group_muted']
        if 'allows_promotions' in raw_msg:
            sender_profile['allows_promotions'] = raw_msg['allows_promotions']
        if 'verified' in raw_msg:
            sender_profile['verified'] = raw_msg['verified']
        if 'official_domain' in raw_msg:
            sender_profile['official_domain'] = raw_msg['official_domain']
        if 'domain_used_by_sender' in raw_msg:
            sender_profile['domain_used_by_sender'] = raw_msg['domain_used_by_sender']
        if 'user_reports_30d' in raw_msg:
            sender_profile['user_reports_30d'] = raw_msg['user_reports_30d']
        if 'category' in raw_msg:
            sender_profile['category'] = raw_msg['category']
        if 'historical_stats' in raw_msg:
            historical_stats.update(raw_msg['historical_stats'])
        elif self.db:
            sender_id_val = raw_msg.get('sender_user_id') if conv_type != 'business' else raw_msg.get('business_id')
            if sender_id_val:
                from src.application.personalization_cache import PersonalizationCache
                cached_stats = PersonalizationCache.get(user_id, sender_id_val)
                if cached_stats:
                    historical_stats.update(cached_stats)
                else:
                    from src.application.personalization_service import PersonalizationService
                    db_stats = PersonalizationService.get_historical_stats(self.db, user_id, sender_id_val)
                    historical_stats.update(db_stats)
                    PersonalizationCache.set(user_id, sender_id_val, db_stats)

        if not evidence_list:
            ev_field = raw_msg.get('evidence_message_ids')
            if ev_field and ev_field != 'none' and isinstance(ev_field, str):
                evidence_list = ev_field.split(';')

        from src.domain.semantic import SemanticClassifier
        semantic_classifier = SemanticClassifier(self.embedding_provider)
        semantic_scores = await semantic_classifier.get_scores(analyzable_text)
        raw_msg['semantic_scores'] = semantic_scores

        decision = MessageRouterRules.classify_and_route(
            raw_msg,
            user_pref,
            sender_profile,
            historical_stats,
            evidence_list
        )

        try:
            from src.application.metrics import ROUTING_DECISIONS, CONFIDENCE_BANDS
            ROUTING_DECISIONS.labels(action=decision['action']).inc()
            conf_score = float(decision['confidence'])
            band = "high" if conf_score >= 0.8 else ("medium" if conf_score >= 0.5 else "low")
            CONFIDENCE_BANDS.labels(band=band).inc()
        except Exception:
            pass

        if self.db:
            await self._save_records_to_db(raw_msg, analyzable_text, media_transcript, decision)

        return decision

    async def process_incoming_message(self, request: MessageProcessingRequest) -> MessageProcessingResult:
        """
        Executes the modular Phase 2 processing pipeline, returning a detailed MessageProcessingResult.
        """
        raw_msg = request.model_dump()
        text_content = request.message_text or ""
        media_type = request.media_type or "none"
        user_id = request.user_id
        conv_type = request.conversation_type

        media_transcript = None
        if media_type == 'voice':
            media_transcript = await self.stt_provider.transcribe(None)
        elif media_type == 'image':
            media_transcript = await self.ocr_provider.extract_text(None)

        if media_transcript:
            from src.config.settings import settings
            if settings.ENABLE_REDACTION:
                from src.domain.redaction import DataRedactor
                media_transcript = DataRedactor.redact(media_transcript)

        analyzable_text = text_content
        if not analyzable_text.strip() and media_transcript:
            analyzable_text = media_transcript

        user_pref = {
            'do_not_disturb_window': request.do_not_disturb_window,
            'group_muted': request.group_muted or False
        }

        sender_profile = {
            'verified': request.verified if request.verified is not None else 0,
            'official_domain': request.official_domain or "",
            'domain_used_by_sender': request.domain_used_by_sender or "",
            'user_reports_30d': request.user_reports_30d if request.user_reports_30d is not None else 0,
            'allows_promotions': request.allows_promotions if request.allows_promotions is not None else True,
            'allows_notifications': True,
            'has_relationship': False,
            'category': request.category or 'unknown'
        }

        historical_stats = {
            'total_count': 0,
            'open_rate': 0.5,
            'reply_rate': 0.0,
            'dismissal_rate': 0.0,
            'mute_rate': 0.0,
            'report_rate': 0.0,
            'reported_count': 0,
            'has_fast_historical_reply': False
        }
        if request.historical_stats:
            historical_stats.update(request.historical_stats)
        elif self.db:
            sender_id_val = request.sender_user_id if conv_type != 'business' else request.business_id
            if sender_id_val:
                from src.application.personalization_cache import PersonalizationCache
                cached_stats = PersonalizationCache.get(user_id, sender_id_val)
                if cached_stats:
                    historical_stats.update(cached_stats)
                else:
                    from src.application.personalization_service import PersonalizationService
                    db_stats = PersonalizationService.get_historical_stats(self.db, user_id, sender_id_val)
                    historical_stats.update(db_stats)
                    PersonalizationCache.set(user_id, sender_id_val, db_stats)

        evidence_list = []
        if request.evidence_message_ids and request.evidence_message_ids != "none":
            evidence_list = request.evidence_message_ids.split(";")

        if self.db:
            if not evidence_list:
                import time
                try:
                    from src.application.metrics import EMBEDDING_DURATION
                    start_time = time.time()
                    evidence_list = await self._retrieve_evidence_from_db(raw_msg, analyzable_text)
                    duration = time.time() - start_time
                    EMBEDDING_DURATION.observe(duration)
                except Exception:
                    evidence_list = await self._retrieve_evidence_from_db(raw_msg, analyzable_text)

            user_obj = self.db.query(User).filter(User.email == user_id).first()
            if not user_obj:
                user_obj = self.db.query(User).filter(User.id == user_id).first()
            if user_obj:
                if not user_pref['do_not_disturb_window']:
                    dnd_start = user_obj.dnd_start_time.strftime("%H:%M") if user_obj.dnd_start_time else "22:00"
                    dnd_end = user_obj.dnd_end_time.strftime("%H:%M") if user_obj.dnd_end_time else "07:00"
                    user_pref['do_not_disturb_window'] = f"{dnd_start}-{dnd_end}"

            if conv_type == 'group' and request.group_id:
                chan = self.db.query(Channel).filter(Channel.external_id == request.group_id).first()
                if chan and user_obj:
                    member = self.db.query(ChannelMember).filter(
                        ChannelMember.user_id == user_obj.id,
                        ChannelMember.channel_id == chan.id
                    ).first()
                    if member and request.group_muted is None:
                        user_pref['group_muted'] = member.is_muted

            sender_id_val = request.sender_user_id if conv_type != 'business' else request.business_id
            if sender_id_val:
                contact_obj = self.db.query(Contact).filter(Contact.id == sender_id_val).first()
                if contact_obj:
                    if request.verified is None:
                        sender_profile['verified'] = 1 if contact_obj.verified else 0
                    if not request.official_domain:
                        sender_profile['official_domain'] = contact_obj.official_domain or ""
                    if not request.domain_used_by_sender:
                        sender_profile['domain_used_by_sender'] = contact_obj.sender_domain or ""
                    if request.user_reports_30d is None:
                        sender_profile['user_reports_30d'] = contact_obj.report_count_30d
                    if request.allows_promotions is None:
                        sender_profile['allows_promotions'] = contact_obj.allows_promotions
                    sender_profile['has_relationship'] = True
                    if not request.category:
                        sender_profile['category'] = contact_obj.type

        preprocessor = MessagePreprocessor()
        preprocessed_text = preprocessor.preprocess(analyzable_text)

        shield = DomainPromptInjectionShield()
        safety_res = shield.scan(preprocessed_text)

        if historical_stats.get('reported_count', 0) > 0:
            safety_res = SafetyResult(
                detected=True,
                risk_level="high",
                matched_indicators=["user reported"],
                sanitized_text="reported"
            )

        credential_keywords = ["otp", "verification code", "verification link", "password", "login code", "login link",
                               "six digit", "6 digit", "verification pending", "confirm card", "confirm password",
                               "profile will be blocked", "wallet verification failed", "account-login.in", "verify now", "verification code abhi"]
        has_credentials_request = has_word_match(preprocessed_text, credential_keywords)
        
        from src.domain.semantic import SemanticClassifier
        semantic_classifier = SemanticClassifier(self.embedding_provider)
        semantic_scores = await semantic_classifier.get_scores(preprocessed_text)
        
        if conv_type in ['personal', 'group'] and has_credentials_request:
            if historical_stats.get('total_count', 0) == 0 or historical_stats.get('reply_rate', 0.0) == 0.0:
                safety_res = SafetyResult(
                    detected=True,
                    risk_level="high",
                    matched_indicators=["untrusted credential request"],
                    sanitized_text="untrusted"
                )

        is_unverified_business = conv_type == 'business' and sender_profile.get('verified', 0) == 0
        if conv_type == 'business' and is_unverified_business and has_credentials_request:
            safety_res = SafetyResult(
                detected=True,
                risk_level="high",
                matched_indicators=["unverified business credential request"],
                sanitized_text="unverified business"
            )

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
                safety_res = SafetyResult(
                    detected=True,
                    risk_level="high",
                    matched_indicators=["domain mismatch"],
                    sanitized_text="brand impersonation" if is_impersonator else "suspicious domain"
                )

        classifier = MessageClassifier()
        msg_type = classifier.classify(
            preprocessed_text, raw_msg, sender_profile, historical_stats, safety_res, has_credentials_request
        )

        urgency_analyzer = UrgencyAnalyzer()
        urgency_res = urgency_analyzer.analyze(preprocessed_text)

        low_urgency_keywords = ["whenever you get time", "whenever convenient", "no urgency", "no pressure",
                                "no rush", "no need to reply", "nothing urgent", "read it before", "if you get time"]
        is_low_urgency = has_word_match(preprocessed_text, low_urgency_keywords)
        if is_low_urgency:
            urgency_res.is_urgent = False
            urgency_res.urgency_score = 0.0

        feedback_keywords = ["fill a review", "give feedback", "experience", "how has your", "rate"]
        is_feedback = has_word_match(preprocessed_text, feedback_keywords)

        personalization_engine = PersonalizationEngine()
        personalization_res = personalization_engine.evaluate(
            raw_msg, user_pref, sender_profile, historical_stats
        )

        is_suppressed_by_dnd = False
        dnd_window = user_pref.get('do_not_disturb_window')
        created_at = request.created_at
        if dnd_window and created_at and is_in_dnd_window(created_at, dnd_window):
            is_emergency = (msg_type == 'urgent' or urgency_res.is_urgent or historical_stats.get('has_fast_historical_reply', False)) and (
                conv_type == 'personal' or (conv_type == 'group' and request.is_mentioned)
            )
            if not is_emergency:
                is_suppressed_by_dnd = True

        is_spam = has_word_match(preprocessed_text, classifier.spam_keywords)
        is_promotion = has_word_match(preprocessed_text, classifier.promotion_keywords)
        is_greeting = has_word_match(preprocessed_text, classifier.greeting_keywords)
        is_forward = (
            has_word_match(preprocessed_text, classifier.forward_words) or
            any(phrase in preprocessed_text.lower() for phrase in classifier.forward_phrases) or
            request.forwarded_count > 3
        )
        is_urgent = urgency_res.is_urgent
        is_payment = has_word_match(preprocessed_text, classifier.payment_keywords)
        is_event = has_word_match(preprocessed_text, classifier.event_keywords)
        is_update = has_word_match(preprocessed_text, classifier.update_keywords)

        has_fast_historical_reply = historical_stats.get('has_fast_historical_reply', False)

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
            is_mentioned=request.is_mentioned or False,
            is_sender_admin=request.is_sender_admin or False,
            semantic_scores=semantic_scores
        )

        is_dnd_muted = is_suppressed_by_dnd or user_pref['group_muted']
        conf_res = ConfidenceScorer.calculate(
            action_res['action'], msg_type, historical_stats, personalization_res, is_dnd_muted
        )

        decision = {
            'action': action_res['action'],
            'message_type': msg_type,
            'reason': action_res['reason'],
            'confidence': conf_res['score'],
            'evidence_message_ids': ";".join(evidence_list) if evidence_list else "none"
        }

        try:
            from src.application.metrics import ROUTING_DECISIONS, CONFIDENCE_BANDS
            ROUTING_DECISIONS.labels(action=decision['action']).inc()

            conf_score = float(decision['confidence'])
            band = "high" if conf_score >= 0.8 else ("medium" if conf_score >= 0.5 else "low")
            CONFIDENCE_BANDS.labels(band=band).inc()
        except Exception:
            pass

        if self.db:
            await self._save_records_to_db(raw_msg, analyzable_text, media_transcript, decision)

        return MessageProcessingResult(
            message_id=request.message_id,
            message_type=msg_type,
            action=decision['action'],
            confidence=decision['confidence'],
            reason=decision['reason'],
            safety_result=safety_res,
            urgency_result=urgency_res,
            personalization_result=personalization_res,
            evidence_message_ids=decision['evidence_message_ids'],
            processing_metadata={
                "processed_at": datetime.datetime.utcnow().isoformat(),
                "preprocessed_text": preprocessed_text,
                "engine_version": "2.0.0-modular"
            }
        )

    async def _retrieve_evidence_from_db(self, msg: Dict[str, Any], text_to_search: str) -> List[str]:
        """
        Retrieves matching historical messages from Postgres using pgvector cosine distance,
        delegating to the EvidenceRetriever coordinator.
        """
        return await EvidenceRetriever.retrieve_evidence(
            db=self.db,
            msg=msg,
            text_to_search=text_to_search,
            embedding_provider=self.embedding_provider
        )

    async def _save_records_to_db(self, msg: Dict[str, Any], text: str, transcript: Optional[str], decision: Dict[str, Any]):
        """
        Saves incoming message and decision parameters to active database models.
        """
        try:
            user_id = msg.get('user_id')
            user_obj = self.db.query(User).filter(User.email == user_id).first()
            if not user_obj:
                user_obj = self.db.query(User).filter(User.id == user_id).first()
            if not user_obj:
                user_obj = User(id=user_id, email=user_id, password_hash="dummy")
                self.db.add(user_obj)
                self.db.flush()

            external_channel_id = msg.get('group_id') or msg.get('business_id') or msg.get('sender_user_id') or "default_channel"
            chan = self.db.query(Channel).filter(Channel.external_id == external_channel_id).first()
            if not chan:
                chan = Channel(
                    id=external_channel_id,
                    name=f"Channel {external_channel_id}",
                    type=msg.get('conversation_type') or 'personal',
                    external_id=external_channel_id
                )
                self.db.add(chan)
                self.db.flush()

            member = self.db.query(ChannelMember).filter(
                ChannelMember.user_id == user_obj.id,
                ChannelMember.channel_id == chan.id
            ).first()
            if not member:
                member = ChannelMember(
                    user_id=user_obj.id,
                    channel_id=chan.id,
                    role='member',
                    is_muted=msg.get('group_muted', False)
                )
                self.db.add(member)
                self.db.flush()

            sender_id_val = msg.get('sender_user_id') or msg.get('business_id') or "system"
            contact_obj = self.db.query(Contact).filter(Contact.id == sender_id_val).first()
            if not contact_obj:
                contact_obj = Contact(
                    id=sender_id_val,
                    name=sender_id_val,
                    type='business' if msg.get('conversation_type') == 'business' else 'user',
                    verified=msg.get('verified', False),
                    allows_promotions=msg.get('allows_promotions', True)
                )
                self.db.add(contact_obj)
                self.db.flush()

            emb_vector = None
            if text:
                try:
                    dialect_name = self.db.bind.dialect.name
                    if dialect_name == "postgresql":
                        emb_vector = await self.embedding_provider.get_embedding(text)
                except Exception:
                    pass

            db_msg = Message(
                id=msg.get('message_id') or f"msg_{int(datetime.datetime.utcnow().timestamp())}",
                channel_id=chan.id,
                sender_id=contact_obj.id,
                message_text=msg.get('message_text'),
                media_type=msg.get('media_type') or 'none',
                media_url=msg.get('media_id'),
                media_transcript=transcript,
                embedding_vector=emb_vector,
                forwarded_count=msg.get('forwarded_count', 0)
            )
            self.db.add(db_msg)
            self.db.flush()

            db_dec = RoutingDecision(
                message_id=db_msg.id,
                user_id=user_obj.id,
                action=decision['action'],
                message_type=decision['message_type'],
                reason=decision['reason'],
                confidence=decision['confidence']
            )
            self.db.add(db_dec)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
