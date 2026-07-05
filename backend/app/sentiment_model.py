from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.db import Base


class SentimentItem(Base):
    __tablename__ = "sentiment_items"

    id         = Column(Integer, primary_key=True, index=True)
    source     = Column(String(20),  nullable=False, index=True)   # reddit / twitter
    text       = Column(Text,        nullable=False)
    label      = Column(String(20),  nullable=False, index=True)   # POSITIVE / NEGATIVE / NEUTRAL
    score      = Column(Float,       nullable=False)                # VADER compound −1→1
    confidence = Column(Float,       nullable=False)                # abs(score)
    match_tag  = Column(String(120), nullable=False, index=True)   # "Brazil vs Scotland"
    url        = Column(String(500), nullable=True)
    author     = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
