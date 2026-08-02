# WC 2026 Intelligence Platform 🏆

A deployed, multi-engine ML system that tracked live World Cup 2026 results against model predictions in real time — from the group stage through the Final.

**🔗 Live demo:** [worldcupintelligence.vercel.app](https://worldcupintelligence.vercel.app)
**📡 API docs:** [wc2026-backend-cxdg.onrender.com/docs](https://wc2026-backend-cxdg.onrender.com/docs)

![Final Tournament Accuracy](https://img.shields.io/badge/Final%20Accuracy-68.6%25-gold)
![Predictions Tracked](https://img.shields.io/badge/Predictions%20Tracked-70-blue)
![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen)
![Stage](https://img.shields.io/badge/Stage-Complete-green)

## What it does

- **Match Predictor** — Random Forest + XGBoost ensemble with dynamic Elo ratings, trained on 32,000+ international fixtures since 1990, predicting win/draw/loss probability for every WC 2026 match
- **Player Analyzer** — K-Means clustering of 9,952 outfield players from all 48 nations into 6 tactical archetypes, with a per-team squad explorer
- **Sentiment Pulse** — real-time Reddit sentiment analysis using VADER, tracking fan reaction match-by-match
- **Live Dashboard** — every prediction tracked against real tournament results, with accuracy broken down by stage and documented failure modes

Each engine is isolated on purpose: match prediction, player clustering, and sentiment analysis solve different problems on different data, and keeping them separate meant a bug or a data-source change in one (see Engineering Decisions below) never risked breaking the other two.

## Final Tournament Accuracy

| Metric | Result |
|--------|--------|
| Total predictions tracked | 70 |
| Matches played (full tournament) | 70 |
| Correct predictions | 48 |
| Final accuracy | **68.6%** |
| Accuracy by stage | Group: 68% · R32: 82% · R16: 67% · QF: 75% · SF: 50% · Final stage: 0% |

The clearest pattern across the tournament: errors cluster almost entirely around **draws** and near-50/50 matchups. The Final itself: the model gave Argentina 30.1% and Spain 30.2% — a near-even split — and Spain won 1-0. That's the model expressing genuine uncertainty accurately, even though the single outcome scored as "wrong."

## System Flow

```
Client (Vue 3, Vercel)
   │  HTTP request
   ▼
FastAPI router  ──▶  Pydantic request validation
   │
   ▼
Engine layer (predictor.py / players.py / sentiment.py)
   │  feature lookup, model inference
   ▼
Model artifacts (RF, XGBoost, K-Means — loaded once at boot from Hugging Face Hub)
   │
   ▼
SQLite (sentiment_items) / static CSV (predictions, player clusters)
   │
   ▼
JSON response  ──▶  Vue dashboard renders
```

- **Model loading happens once, at startup**, not per-request — `download_models.py` pulls `.pkl` files from Hugging Face Hub if they're not already cached locally, then all three engines load into memory before the server accepts traffic.
- **If a model file fails to download**, startup fails loudly (the FastAPI lifespan raises) rather than serving a half-loaded app — an explicit crash-on-boot was chosen over a silent partial failure.
- **Sentiment fetches are the one live external dependency** (Arctic Shift's Reddit mirror) — these run per-subreddit in parallel with automatic retries, since that specific dependency has no uptime SLA (see Known Limitations).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Match Prediction | Random Forest + XGBoost ensemble, scikit-learn |
| Team Strength | Dynamic Elo ratings (tournament-weighted K-factor) |
| Player Clustering | K-Means (k=6), StandardScaler, scikit-learn |
| Sentiment | VADER (social-media-tuned), Reddit data via Arctic Shift API |
| Training | Google Colab (CPU + T4 GPU) |
| API | FastAPI, Pydantic, SQLAlchemy, Joblib |
| Frontend | Vue 3 (Composition API), Chart.js, Vite |
| Hosting | Render (backend) + Vercel (frontend) |
| Model storage | Hugging Face Hub (pkl files, downloaded at runtime) |
| CI | GitHub Actions — pytest on every push to `main` |

The stack favors fast iteration on ML-backed APIs while keeping model serving, application data, and the frontend cleanly separated.

## Model Details

### Match Predictor
Trained on 32,000+ international fixtures (1990–2026). Live inference averages predictions across **both team orderings** — `predict(A, B)` and `predict(B, A)` — to cancel out home-team bias inherited from the training data, since World Cup matches are played on neutral ground. CV accuracy: 59.1% (3-class win/draw/loss; random baseline = 33.3%). Live tournament accuracy: 68.6% across all 70 matches.

### Player Analyzer
K-Means (k=6, n_init=20) on standardized FC 26 attributes (pace, shooting, passing, dribbling, defending, physic). Cluster names are derived from each centroid's top-2 Z-score attributes, not hand-assigned — Pacey Dribbler, Defensive Anchor, Deep Playmaker, Defensive Anchor II, Pacey Dribbler II, Target Striker.

### Sentiment Pulse
VADER over Reddit posts fetched via the Arctic Shift API. Chosen over a transformer specifically to keep inference under 1ms and avoid a third multi-hundred-MB model competing for memory alongside Engines 1 and 2 on a free-tier host.

## Testing & Validation

```bash
cd backend
pytest tests/ -v
```

Tests run against the real FastAPI app with real model loading — the same lifespan that runs in production, not a mocked version — since inference is fast enough that this stays practical. Coverage focuses on the paths that matter, not on maximizing a percentage:

- Health checks, including a regression test for HEAD-request support (see Engineering Decisions)
- Prediction endpoint: response shape, probability distribution sums to 100%, valid predicted-winner value
- **Order-independence regression test** — `predict(A, B)` and `predict(B, A)` must describe the same matchup within tolerance (see Engineering Decisions)
- Data-integrity check: with the tournament complete, every tracked prediction should have a result (`played == total_predictions`)
- Player and cluster endpoint shape checks, including 404 handling for unknown nations
- Sentiment endpoint shape only, not live fetch success — Arctic Shift is a free third-party service with no uptime guarantee, so asserting on it would make CI flaky for reasons outside this app's control

CI runs this suite via GitHub Actions on every push to `main`.

## Deployment

- **Backend** — Render, Python 3.11.9 (pinned via `runtime.txt`), free tier
- **Frontend** — Vercel, auto-deploys on push
- **Models** — Hugging Face Hub, downloaded once at container boot and cached
- **Keep-alive** — UptimeRobot pings `/health` every 5 minutes to prevent Render's free-tier cold start (~30-60s) from hitting real visitors

Local and production environments intentionally use the same Python version and the same model-loading path, so "works on my machine" failures surface locally instead of only on deploy.

## Engineering Decisions & Incidents

Real problems hit during development, and how they were resolved — the kind of debugging an interview question like "tell me about a bug you tracked down in production" is actually asking about.

| Issue | Root cause | Fix |
|---|---|---|
| Predictions shifted depending on team input order | Training data over-represented home teams; model learned a home-side bias that leaked into neutral-venue tournament predictions | Average forward and reverse team-order inference at prediction time — covered by a regression test |
| `ValueError: Out of range float values are not JSON compliant` | Pandas `NaN` in the predictions CSV isn't valid JSON | Explicit `math.isnan()` check before serialization |
| Frontend calls silently failing after changing the Vercel domain | CORS origin allowlist in FastAPI didn't include the new domain | Added the new origin explicitly; documented as a checklist item for future domain changes |
| Backend crashed on deploy with a SQLAlchemy import error | Render's default runtime picked Python 3.14; SQLAlchemy 2.0.30 has a known incompatibility with it | Pinned `runtime.txt` to Python 3.11.9, bumped SQLAlchemy to `>=2.0.36` |
| Reddit sentiment collection returned zero results with no error | Reddit's public `.json` endpoint stopped reliably serving unauthenticated requests mid-project | Migrated to Arctic Shift, a keyless Reddit data mirror, with per-subreddit parallel fetching and automatic retries |
| UptimeRobot kept reporting the backend as down | `/health` only accepted `GET`; UptimeRobot's default check method is `HEAD`, which FastAPI correctly 405'd | Changed the route to accept both `GET` and `HEAD` |
| First visitor after 15 minutes of inactivity saw a 30-60s hang | Render's free tier spins down idle services | Scheduled an UptimeRobot ping to `/health` every 5 minutes |

## Known Limitations

**Model limitations**
- Draws are the model's single largest error category — pre-match statistics can't capture what produces a 0-0 or 1-1 result
- Genuine upsets (Norway over Brazil, Morocco over Netherlands, Ecuador over Germany) are real misses, not just draws scored as wrong

**Data limitations**
- Teams with limited international match history (Curaçao, Cabo Verde) get less reliable Elo and form estimates
- Player clustering reflects a single FC 26 snapshot, not in-tournament form changes

**Infrastructure limitations**
- SQLite is sufficient for the current write volume (a single `sentiment_items` table, no concurrent writers) but would need to move to a managed database before supporting multiple simultaneous users or persistent per-user state
- Arctic Shift has no uptime SLA; sentiment fetches can fail on high-traffic subreddits and are retried automatically rather than guaranteed

## Running locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Model files (~70MB) download automatically from Hugging Face Hub on first run.

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5174` for the dashboard, `http://localhost:8000/docs` for the interactive API.

## Project Structure

```
wc2026-intelligence/
├── .github/workflows/
│   └── ci.yml                       # pytest on every push
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── download_models.py       # Hugging Face model fetch on boot
│   │   ├── engines/
│   │   │   ├── predictor.py         # Engine 1
│   │   │   ├── players.py           # Engine 2
│   │   │   └── sentiment.py         # Engine 3
│   │   ├── sentiment_model.py       # SQLAlchemy model for sentiment items
│   │   └── routers/
│   │       ├── predictions.py
│   │       ├── players.py
│   │       └── sentiment.py
│   ├── models/                      # CSV/JSON tracked; pkl via Hugging Face
│   ├── tests/
│   │   └── test_api.py
│   ├── auto_update.py               # Pulls live results, fills in outcomes
│   └── runtime.txt                  # Pins Python 3.11 for Render
└── frontend/
    └── src/
        ├── views/
        │   ├── Dashboard.vue        # Predictions + live predictor
        │   ├── Players.vue          # Archetype radar + team explorer
        │   └── Sentiment.vue        # Fan reaction feed
        └── App.vue
```

## Built by

Neel 
[github.com/NboTop](https://github.com/NboTop)
