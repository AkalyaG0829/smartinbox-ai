import pytest
from src.infrastructure.models import User, Contact, Channel, Message, UserInteraction, ChannelMember
from src.application.personalization_service import PersonalizationService

def test_personalization_service_aggregation(db_session):
    """
    Focused unit tests covering dynamic statistics aggregation for:
    - zero interactions
    - all-open interactions
    - replies
    - dismissals
    - reports
    - fast replies within 5 minutes
    - multiple interactions
    - user/sender isolation
    - mute rate tracking where existing data supports it
    """
    # 1. Setup users, contacts, channels
    user = User(id="u_agg_001", email="agg_user@example.com")
    db_session.add(user)

    sender_friendly = Contact(id="u_agg_002", name="Friendly Contact", type="user")
    sender_unfriendly = Contact(id="u_agg_003", name="Spam Contact", type="user")
    db_session.add(sender_friendly)
    db_session.add(sender_unfriendly)

    chan1 = Channel(id="c_agg_001", name="Chan 1", type="personal", external_id="c_agg_001")
    chan2 = Channel(id="c_agg_002", name="Chan 2", type="personal", external_id="c_agg_002")
    db_session.add(chan1)
    db_session.add(chan2)
    db_session.flush()

    # A. Zero interactions case
    stats_zero = PersonalizationService.get_historical_stats(db_session, user.id, sender_friendly.id)
    assert stats_zero['total_count'] == 0
    assert stats_zero['open_rate'] == 0.5
    assert stats_zero['reply_rate'] == 0.0
    assert stats_zero['dismissal_rate'] == 0.0
    assert stats_zero['mute_rate'] == 0.0
    assert stats_zero['report_rate'] == 0.0
    assert stats_zero['reported_count'] == 0
    assert stats_zero['has_fast_historical_reply'] is False

    # B. Seed messages
    msg1 = Message(id="m_agg_001", channel_id=chan1.id, sender_id=sender_friendly.id, message_text="Hello")
    msg2 = Message(id="m_agg_002", channel_id=chan1.id, sender_id=sender_friendly.id, message_text="Hey")
    msg3 = Message(id="m_agg_003", channel_id=chan2.id, sender_id=sender_unfriendly.id, message_text="Click here")
    db_session.add(msg1)
    db_session.add(msg2)
    db_session.add(msg3)
    db_session.flush()

    # C. All-open interactions for friendly contact
    int1 = UserInteraction(user_id=user.id, message_id=msg1.id, opened=True, replied=False, dismissed=False, reported=False)
    db_session.add(int1)
    db_session.flush()

    stats_friendly = PersonalizationService.get_historical_stats(db_session, user.id, sender_friendly.id)
    assert stats_friendly['total_count'] == 1
    assert stats_friendly['open_rate'] == 1.0
    assert stats_friendly['reply_rate'] == 0.0
    assert stats_friendly['has_fast_historical_reply'] is False

    # D. Reply and fast reply within 5 minutes (reaction_time_seconds <= 300)
    int2 = UserInteraction(user_id=user.id, message_id=msg2.id, opened=True, replied=True, dismissed=False, reported=False, reaction_time_seconds=120)
    db_session.add(int2)
    db_session.flush()

    stats_friendly2 = PersonalizationService.get_historical_stats(db_session, user.id, sender_friendly.id)
    assert stats_friendly2['total_count'] == 2
    assert stats_friendly2['open_rate'] == 1.0
    assert stats_friendly2['reply_rate'] == 0.5
    assert stats_friendly2['has_fast_historical_reply'] is True

    # E. Dismissals and Reports on Unfriendly sender (user/sender isolation checks)
    int3 = UserInteraction(user_id=user.id, message_id=msg3.id, opened=False, replied=False, dismissed=True, reported=True)
    db_session.add(int3)
    db_session.flush()

    stats_unfriendly = PersonalizationService.get_historical_stats(db_session, user.id, sender_unfriendly.id)
    assert stats_unfriendly['total_count'] == 1
    assert stats_unfriendly['open_rate'] == 0.0
    assert stats_unfriendly['dismissal_rate'] == 1.0
    assert stats_unfriendly['report_rate'] == 1.0
    assert stats_unfriendly['reported_count'] == 1
    assert stats_unfriendly['has_fast_historical_reply'] is False

    # Isolation assertion: friendly stats should remain unaffected by unfriendly events
    stats_friendly_check = PersonalizationService.get_historical_stats(db_session, user.id, sender_friendly.id)
    assert stats_friendly_check['total_count'] == 2
    assert stats_friendly_check['report_rate'] == 0.0

    # F. Mute rate checks
    # Create channel member for chan1 as unmuted, chan2 as muted
    mem1 = ChannelMember(user_id=user.id, channel_id=chan1.id, is_muted=False)
    mem2 = ChannelMember(user_id=user.id, channel_id=chan2.id, is_muted=True)
    db_session.add(mem1)
    db_session.add(mem2)
    db_session.flush()

    # unfriendly sender only sent msg3 to chan2, which is muted.
    # So mute_rate should be 1.0 (1/1 messages in muted channels)
    stats_unfriendly2 = PersonalizationService.get_historical_stats(db_session, user.id, sender_unfriendly.id)
    assert stats_unfriendly2['mute_rate'] == 1.0

    # friendly sender sent both msg1 and msg2 to chan1, which is unmuted.
    # So mute_rate should be 0.0 (0/2 messages in muted channels)
    stats_friendly3 = PersonalizationService.get_historical_stats(db_session, user.id, sender_friendly.id)
    assert stats_friendly3['mute_rate'] == 0.0
