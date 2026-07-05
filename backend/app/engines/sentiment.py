"""
Sentiment Pulse — Engine 3
---------------------------
Collects posts from Reddit (free) and Twitter/X (optional Bearer Token),
analyzes each with VADER (purpose-built for social media text, zero RAM overhead),
and returns structured sentiment results.

Why VADER over a transformer:
  • Social posts are short, slangy, emoji-heavy — VADER handles this natively
  • The WC2026 backend already loads ~500MB of sklearn/XGBoost models;
    adding a 250MB transformer would exceed 4GB RAM on low-end hardware
  • VADER runs in <1ms per post vs ~50ms for a transformer
  • Accuracy on tweet-style text is comparable to DistilBERT at this scale
"""

import os
import logging
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()
logger = logging.getLogger(__name__)


# ── VADER analyzer ────────────────────────────────────────────────────────────

class VADERSentiment:
    """Wraps VaderSentiment for social-media text."""

    def __init__(self):
        self._analyzer = SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> Dict[str, Any]:
        scores   = self._analyzer.polarity_scores(text)
        compound = scores["compound"]

        if compound >= 0.05:
            label = "POSITIVE"
        elif compound <= -0.05:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"

        return {
            "label":      label,
            "score":      round(compound, 4),
            "confidence": round(abs(compound), 4),
        }


# ── Reddit collector ──────────────────────────────────────────────────────────

import requests as http_requests

class RedditCollector:
    """
    Uses Reddit's public JSON endpoint — no API key or app registration needed.
    Works for reading public posts on r/worldcup, r/soccer, r/football.
    """

    SUBREDDITS = ["worldcup", "soccer", "football"]
    HEADERS    = {"User-Agent": "wc2026-sentiment/1.0"}

    @property
    def configured(self) -> bool:
        return True   # always available, no credentials needed

    def fetch(self, query: str, limit_per_sub: int = 10) -> List[Dict]:
        posts = []
        for sub in self.SUBREDDITS:
            try:
                url  = f"https://www.reddit.com/r/{sub}/search.json"
                resp = http_requests.get(
                    url,
                    params  = {"q": query, "sort": "new", "t": "day", "limit": limit_per_sub},
                    headers = self.HEADERS,
                    timeout = 8,
                )
                if resp.status_code != 200:
                    continue
                for child in resp.json().get("data", {}).get("children", []):
                    post = child.get("data", {})
                    text = f"{post.get('title','')} {post.get('selftext','')}".strip()
                    if len(text) < 12:
                        continue
                    posts.append({
                        "source": "reddit",
                        "text":   text[:600],
                        "url":    f"https://reddit.com{post.get('permalink','')}",
                        "author": post.get("author", "[deleted]"),
                    })
            except Exception as exc:
                logger.warning(f"Reddit r/{sub}: {exc}")
        return posts


# ── Twitter/X collector ───────────────────────────────────────────────────────

class TwitterCollector:
    """Fetches recent tweets using Tweepy v4 (free Bearer Token tier)."""

    def __init__(self):
        self._client = None

    @property
    def configured(self) -> bool:
        return bool(os.getenv("TWITTER_BEARER_TOKEN"))

    def _get_client(self):
        if self._client is None:
            import tweepy
            self._client = tweepy.Client(bearer_token=os.getenv("TWITTER_BEARER_TOKEN"))
        return self._client

    def fetch(self, query: str, limit: int = 25) -> List[Dict]:
        if not self.configured:
            return []

        try:
            client = self._get_client()
            resp   = client.search_recent_tweets(
                query        = f"{query} #WorldCup2026 lang:en -is:retweet",
                max_results  = min(max(limit, 10), 100),
                tweet_fields = ["text", "author_id"],
            )
            if not resp.data:
                return []
            return [{
                "source": "twitter",
                "text":   t.text,
                "url":    f"https://twitter.com/i/web/status/{t.id}",
                "author": str(t.author_id),
            } for t in resp.data]
        except Exception as exc:
            logger.warning(f"Twitter fetch: {exc}")
            return []


# ── Orchestrator ──────────────────────────────────────────────────────────────

class SentimentEngine:
    """Combines Reddit + Twitter collection with VADER analysis."""

    def __init__(self):
        self.vader   = VADERSentiment()
        self.reddit  = RedditCollector()
        self.twitter = TwitterCollector()

    @property
    def reddit_configured(self) -> bool:
        return self.reddit.configured

    @property
    def twitter_configured(self) -> bool:
        return self.twitter.configured

    def collect_and_analyze(
        self,
        match_tag:  str,
        sources:    Optional[List[str]] = None,
        limit:      int = 30,
    ) -> List[Dict[str, Any]]:
        if sources is None:
            sources = ["reddit", "twitter"]

        raw: List[Dict] = []
        if "reddit" in sources:
            raw += self.reddit.fetch(match_tag, limit_per_sub=max(limit // 3, 5))
        if "twitter" in sources:
            raw += self.twitter.fetch(match_tag, limit=limit)

        results: List[Dict] = []
        seen: set             = set()

        for item in raw:
            text = item["text"].strip()
            if not text or text in seen or len(text) < 12:
                continue
            seen.add(text)
            sentiment = self.vader.analyze(text)
            results.append({**item, **sentiment, "match_tag": match_tag})

        return results


# Module-level singleton
sentiment_engine = SentimentEngine()
