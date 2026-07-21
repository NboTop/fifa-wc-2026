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

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    Fetches Reddit posts via the Arctic Shift API (free, keyless Reddit
    data mirror). Runs all target subreddits in parallel with automatic
    retries, since very high-traffic subreddits occasionally return a
    422 or time out on Arctic Shift's free tier.
    """

    BASE_URL   = "https://arctic-shift.photon-reddit.com/api/posts/search"
    SUBREDDITS = ["worldcup", "soccer", "football"]
    HEADERS    = {"User-Agent": "wc2026-sentiment/1.0"}
    TIMEOUT    = 15
    RETRIES    = 2

    @property
    def configured(self) -> bool:
        return True

    def _fetch_subreddit(self, sub: str, query: str, limit: int) -> List[Dict]:
        last_error = None
        for attempt in range(self.RETRIES):
            try:
                resp = http_requests.get(
                    self.BASE_URL,
                    params={
                        "subreddit": sub,
                        "query":     query,
                        "sort":      "desc",
                        "limit":     min(limit, 100),
                    },
                    headers=self.HEADERS,
                    timeout=self.TIMEOUT,
                )
                if resp.status_code != 200:
                    last_error = f"HTTP {resp.status_code}"
                    time.sleep(0.5)
                    continue

                posts = []
                for post in resp.json().get("data", []):
                    text = f"{post.get('title','')} {post.get('selftext','')}".strip()
                    if len(text) < 12:
                        continue
                    permalink = post.get("permalink") or f"/r/{sub}/comments/{post.get('id','')}/"
                    posts.append({
                        "source": "reddit",
                        "text":   text[:600],
                        "url":    f"https://reddit.com{permalink}",
                        "author": post.get("author", "[deleted]"),
                    })
                return posts  # success — stop retrying this subreddit

            except Exception as exc:
                last_error = str(exc)
                time.sleep(0.5)

        logger.warning(f"Arctic Shift r/{sub}: failed after {self.RETRIES} attempts ({last_error})")
        return []

    def fetch(self, query: str, limit_per_sub: int = 10) -> List[Dict]:
        posts = []
        with ThreadPoolExecutor(max_workers=len(self.SUBREDDITS)) as pool:
            futures = {
                pool.submit(self._fetch_subreddit, sub, query, limit_per_sub): sub
                for sub in self.SUBREDDITS
            }
            for future in as_completed(futures):
                posts.extend(future.result())
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
