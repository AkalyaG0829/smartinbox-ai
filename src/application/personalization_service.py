from sqlalchemy.orm import Session
from typing import Dict, Any
from src.infrastructure.models import User, Message, ChannelMember, UserInteraction

class PersonalizationService:
    @staticmethod
    def get_historical_stats(db: Session, user_id: str, sender_id: str) -> Dict[str, Any]:
        """
        Dynamically aggregates user interaction metrics from the database
        for a specific user and sender (contact).
        """
        # Resolve user UUID mapping if user_id is an email
        user_obj = db.query(User).filter(User.email == user_id).first()
        if not user_obj:
            user_obj = db.query(User).filter(User.id == user_id).first()

        user_uuid = user_obj.id if user_obj else user_id

        # Query all interactions for this user and messages sent by this sender
        interactions = db.query(UserInteraction).join(Message).filter(
            UserInteraction.user_id == user_uuid,
            Message.sender_id == sender_id
        ).all()

        if not interactions:
            return {
                'total_count': 0,
                'open_rate': 0.5,
                'reply_rate': 0.0,
                'dismissal_rate': 0.0,
                'mute_rate': 0.0,
                'report_rate': 0.0,
                'reported_count': 0,
                'has_fast_historical_reply': False
            }

        total_count = len(interactions)
        opened_count = sum(1 for i in interactions if i.opened)
        replied_count = sum(1 for i in interactions if i.replied)
        dismissed_count = sum(1 for i in interactions if i.dismissed)
        reported_count = sum(1 for i in interactions if i.reported)

        # Mute rate: count how many sender's messages reside in channels muted by the user
        muted_channels = db.query(ChannelMember.channel_id).filter(
            ChannelMember.user_id == user_uuid,
            ChannelMember.is_muted == True
        )

        muted_count = db.query(Message).filter(
            Message.sender_id == sender_id,
            Message.channel_id.in_(muted_channels)
        ).count()

        total_messages_count = db.query(Message).filter(Message.sender_id == sender_id).count()
        mute_rate = (muted_count / total_messages_count) if total_messages_count > 0 else 0.0

        # Calculate fast reply status (replied within 5 minutes / 300 seconds)
        has_fast_historical_reply = any(
            i.replied and i.reaction_time_seconds is not None and i.reaction_time_seconds <= 300
            for i in interactions
        )

        return {
            'total_count': total_count,
            'open_rate': opened_count / total_count,
            'reply_rate': replied_count / total_count,
            'dismissal_rate': dismissed_count / total_count,
            'mute_rate': mute_rate,
            'report_rate': reported_count / total_count,
            'reported_count': reported_count,
            'has_fast_historical_reply': has_fast_historical_reply
        }
