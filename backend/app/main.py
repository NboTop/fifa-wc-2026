from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.engines.predictor import match_predictor
from app.engines.players   import player_analyzer
from app.routers import predictions, players
from app.routers import sentiment as sentiment_router
from app.db import engine, Base
from app.sentiment_model import SentimentItem          # ensures table is registered
from app.download_models import ensure_models_downloaded
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_models_downloaded()   # ← add this line first
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Sentiment DB tables ready")

    logger.info("Loading engines...")
    match_predictor.load()
    player_analyzer.load()
    logger.info("All engines ready ✓")
    yield


app = FastAPI(
    title      = "WC 2026 Intelligence API",
    version    = "2.0.0",
    lifespan   = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins    = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials= True,
    allow_methods    = ["*"],
    allow_headers    = ["*"],
)

app.include_router(predictions.router,        prefix="/api/v1", tags=["predictions"])
app.include_router(players.router,            prefix="/api/v1", tags=["players"])
app.include_router(sentiment_router.router,   prefix="/api/v1", tags=["sentiment"])


@app.get("/health")
def health():
    from app.engines.sentiment import sentiment_engine
    return {
        "status":  "ok",
        "engines": {
            "predictor":           match_predictor.is_loaded,
            "players":             player_analyzer.is_loaded,
            "reddit_configured":   sentiment_engine.reddit_configured,
            "twitter_configured":  sentiment_engine.twitter_configured,
        },
    }
