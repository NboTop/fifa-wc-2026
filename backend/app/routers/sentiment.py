from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.sentiment_model import SentimentItem
from app.engines.sentiment import sentiment_engine
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/sentiment/status")
def sentiment_status():
    """Returns which data sources are configured."""
    return {
        "reddit_configured":  sentiment_engine.reddit_configured,
        "twitter_configured": sentiment_engine.twitter_configured,
    }


# ── Refresh (collect + store) ─────────────────────────────────────────────────

@router.post("/sentiment/refresh")
def refresh_sentiment(
    match_tag: str = Query(..., description="e.g. 'Brazil vs Scotland'"),
    sources:   str = Query("reddit", description="Comma-separated: reddit, twitter"),
    db: Session    = Depends(get_db),
):
    """Fetch fresh posts about a match and persist analyzed results."""
    source_list = [s.strip().lower() for s in sources.split(",")]

    try:
        items = sentiment_engine.collect_and_analyze(
            match_tag, source_list, limit=30
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    stored = 0
    for item in items:
        db.add(SentimentItem(
            source     = item["source"],
            text       = item["text"],
            label      = item["label"],
            score      = item["score"],
            confidence = item["confidence"],
            match_tag  = item["match_tag"],
            url        = item.get("url", ""),
            author     = item.get("author", ""),
        ))
        stored += 1

    db.commit()
    return {"fetched": stored, "match_tag": match_tag, "sources": source_list}


# ── Feed ──────────────────────────────────────────────────────────────────────

@router.get("/sentiment/feed")
def get_feed(
    match_tag: Optional[str] = None,
    source:    Optional[str] = None,
    label:     Optional[str] = None,
    limit:     int           = 30,
    db: Session              = Depends(get_db),
):
    """Return recent sentiment items with optional filters."""
    q = db.query(SentimentItem).order_by(SentimentItem.created_at.desc())
    if match_tag:
        q = q.filter(SentimentItem.match_tag == match_tag)
    if source:
        q = q.filter(SentimentItem.source == source.lower())
    if label:
        q = q.filter(SentimentItem.label == label.upper())

    rows = q.limit(limit).all()
    return [
        {
            "id":         r.id,
            "source":     r.source,
            "text":       r.text,
            "label":      r.label,
            "score":      r.score,
            "confidence": r.confidence,
            "match_tag":  r.match_tag,
            "url":        r.url,
            "author":     r.author,
            "created_at": r.created_at,
        }
        for r in rows
    ]


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/sentiment/stats")
def get_stats(
    match_tag: Optional[str] = None,
    db: Session              = Depends(get_db),
):
    """Aggregate sentiment stats, optionally filtered by match."""
    q = db.query(SentimentItem)
    if match_tag:
        q = q.filter(SentimentItem.match_tag == match_tag)

    total    = q.count()
    positive = q.filter(SentimentItem.label == "POSITIVE").count()
    negative = q.filter(SentimentItem.label == "NEGATIVE").count()
    neutral  = q.filter(SentimentItem.label == "NEUTRAL").count()
    avg_score = float(
        db.query(func.avg(SentimentItem.score)).scalar() or 0.0
    )

    tags = [
        r[0] for r in
        db.query(SentimentItem.match_tag).distinct().all()
    ]

    return {
        "total":              total,
        "positive":           positive,
        "negative":           negative,
        "neutral":            neutral,
        "avg_score":          round(avg_score, 4),
        "match_tags":         tags,
        "reddit_configured":  sentiment_engine.reddit_configured,
        "twitter_configured": sentiment_engine.twitter_configured,
    }


# ── Trend ─────────────────────────────────────────────────────────────────────

@router.get("/sentiment/trend")
def get_trend(
    match_tag: Optional[str] = None,
    hours:     int           = 24,
    db: Session              = Depends(get_db),
):
    """Hourly sentiment trend over the last N hours."""
    since = datetime.utcnow() - timedelta(hours=hours)
    q     = db.query(SentimentItem).filter(SentimentItem.created_at >= since)
    if match_tag:
        q = q.filter(SentimentItem.match_tag == match_tag)

    trend: dict = {}
    for r in q.order_by(SentimentItem.created_at).all():
        hour = r.created_at.strftime("%H:00") if r.created_at else "00:00"
        if hour not in trend:
            trend[hour] = {"hour": hour, "positive": 0, "negative": 0, "neutral": 0, "total": 0}
        trend[hour][r.label.lower()] += 1
        trend[hour]["total"] += 1

    return list(trend.values())
