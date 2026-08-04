import pytest
from src.infrastructure.models import User, Channel, Contact, Message, RoutingDecision, UserInteraction
from src.application.analytics_service import AnalyticsService

def test_analytics_zero_data(db_session):
    result = AnalyticsService.get_routing_alignment_analytics(db_session)
    assert result["total_actions"] == 0
    assert result["alignment_rate"] == 0.0
    assert result["aligned_count"] == 0
    assert result["misaligned_count"] == 0
    assert result["mismatches"] == []

def test_analytics_alignment_cases(db_session):
    # Setup base entities
    user = User(id="u_test_analytics", email="analytics@example.com")
    channel = Channel(id="c_test_analytics", name="Analytics Channel", type="personal", external_id="c_test_analytics")
    contact = Contact(id="contact_analytics", name="Analytics Contact", type="user")
    
    db_session.add_all([user, channel, contact])
    db_session.commit()

    def create_scenario(msg_id, action, opened=False, replied=False, dismissed=False, reported=False):
        msg = Message(id=msg_id, channel_id=channel.id, sender_id=contact.id)
        db_session.add(msg)
        db_session.commit()
        
        decision = RoutingDecision(
            message_id=msg.id,
            user_id=user.id,
            action=action,
            message_type="personal",
            reason="test reason",
            confidence=0.9
        )
        interaction = UserInteraction(
            message_id=msg.id,
            user_id=user.id,
            opened=opened,
            replied=replied,
            dismissed=dismissed,
            reported=reported
        )
        db_session.add_all([decision, interaction])
        db_session.commit()

    # Case 1: notify + opened -> aligned
    create_scenario("msg_1", "notify", opened=True)
    
    # Case 2: notify + replied -> aligned
    create_scenario("msg_2", "notify", replied=True)
    
    # Case 3: notify + dismissed -> misaligned
    create_scenario("msg_3", "notify", dismissed=True)
    
    # Case 4: mute + reported -> aligned
    create_scenario("msg_4", "mute", reported=True)
    
    # Case 5: mute + dismissed -> aligned
    create_scenario("msg_5", "mute", dismissed=True)
    
    # Case 6: mute + opened -> misaligned
    create_scenario("msg_6", "mute", opened=True)
    
    # Case 7: digest + opened + not replied + not reported -> aligned
    create_scenario("msg_7", "digest", opened=True)
    
    # Case 8: digest mismatch cases -> digest + reported -> misaligned
    create_scenario("msg_8", "digest", reported=True)
    
    # Case 9: mute + nothing (ignored) -> aligned
    create_scenario("msg_9", "mute")

    # Fetch analytics
    result = AnalyticsService.get_routing_alignment_analytics(db_session)
    
    assert result["total_actions"] == 9
    assert result["aligned_count"] == 6 # msg_1, msg_2, msg_4, msg_5, msg_7, msg_9
    assert result["misaligned_count"] == 3 # msg_3, msg_6, msg_8
    assert result["alignment_rate"] == round((6 / 9) * 100, 2)
    assert len(result["mismatches"]) == 3
    
    mismatch_ids = [m["message_id"] for m in result["mismatches"]]
    assert "msg_3" in mismatch_ids
    assert "msg_6" in mismatch_ids
    assert "msg_8" in mismatch_ids
