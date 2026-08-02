import datetime
from sqlalchemy import Column, String, Integer, Boolean, Time, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from src.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(255), primary_key=True)  # e.g., 'u_001'
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False, default="dummy")
    dnd_start_time = Column(Time, nullable=True)
    dnd_end_time = Column(Time, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    memberships = relationship("ChannelMember", back_populates="user", cascade="all, delete-orphan")
    routing_decisions = relationship("RoutingDecision", back_populates="user", cascade="all, delete-orphan")
    interactions = relationship("UserInteraction", back_populates="user", cascade="all, delete-orphan")

class Channel(Base):
    __tablename__ = "channels"

    id = Column(String(255), primary_key=True)  # e.g., 'group_001', 'business_001', 'u_002'
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'personal', 'group', 'business'
    external_id = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    members = relationship("ChannelMember", back_populates="channel", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="channel", cascade="all, delete-orphan")

class ChannelMember(Base):
    __tablename__ = "channel_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel_id = Column(String(255), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="member")
    is_muted = Column(Boolean, default=False)

    user = relationship("User", back_populates="memberships")
    channel = relationship("Channel", back_populates="members")

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String(255), primary_key=True)  # e.g., 'business_001', 'u_002'
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'user', 'business'
    verified = Column(Boolean, default=False)
    official_domain = Column(String(255), nullable=True)
    sender_domain = Column(String(255), nullable=True)
    report_count_30d = Column(Integer, default=0)
    allows_promotions = Column(Boolean, default=True)

    messages = relationship("Message", back_populates="sender")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(255), primary_key=True)  # e.g., 'msg_001'
    channel_id = Column(String(255), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(String(255), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    message_text = Column(String, nullable=True)
    media_type = Column(String(50), default="none")  # 'none', 'image', 'voice'
    media_url = Column(String(509), nullable=True)
    media_transcript = Column(String, nullable=True)
    embedding_vector = Column(Vector(384), nullable=True)
    forwarded_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    channel = relationship("Channel", back_populates="messages")
    sender = relationship("Contact", back_populates="messages")
    routing_decisions = relationship("RoutingDecision", back_populates="message", cascade="all, delete-orphan")
    interactions = relationship("UserInteraction", back_populates="message", cascade="all, delete-orphan")

class RoutingDecision(Base):
    __tablename__ = "routing_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(255), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)  # 'notify', 'digest', 'mute'
    message_type = Column(String(50), nullable=False)  # 'personal', 'urgent', etc.
    reason = Column(String, nullable=False)
    confidence = Column(Numeric(3, 2), nullable=False)
    processed_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    message = relationship("Message", back_populates="routing_decisions")
    user = relationship("User", back_populates="routing_decisions")

class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(String(255), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    opened = Column(Boolean, default=False)
    replied = Column(Boolean, default=False)
    dismissed = Column(Boolean, default=False)
    reported = Column(Boolean, default=False)
    reaction_time_seconds = Column(Integer, nullable=True)
    interaction_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="interactions")
    message = relationship("Message", back_populates="interactions")
