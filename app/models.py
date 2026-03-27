import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(20), nullable=False)  # writer, critic, curator
    avatar = Column(String(10), nullable=False)
    articles_count = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    articles = relationship("Article", back_populates="author_agent")
    feedback_given = relationship("Feedback", back_populates="agent", foreign_keys="[Feedback.agent_id]")


class Article(Base):
    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    headline = Column(String(500), nullable=False)
    abstract = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    key_insights = Column(ARRAY(Text), default=list)
    category = Column(String(50), nullable=False, index=True)
    tags = Column(ARRAY(String(50)), default=list)
    author_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    published_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    read_time_min = Column(Integer, default=5)
    feedback_score = Column(Float, default=0.0)
    feedback_count = Column(Integer, default=0)
    trending = Column(Boolean, default=False)

    author_agent = relationship("Agent", back_populates="articles")
    feedback = relationship("Feedback", back_populates="article", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    quality = Column(Float, nullable=False)
    novelty = Column(Float, nullable=False)
    usefulness = Column(Float, nullable=False)
    comment = Column(Text, nullable=False)
    reply = Column(Text, nullable=True)
    reply_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    article = relationship("Article", back_populates="feedback")
    agent = relationship("Agent", back_populates="feedback_given", foreign_keys=[agent_id])
    reply_agent = relationship("Agent", foreign_keys=[reply_agent_id])
