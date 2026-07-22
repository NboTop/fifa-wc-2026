# WC 2026 Intelligence Platform 🏆

An AI-powered match prediction, player analysis, and fan-sentiment platform that tracked live World Cup 2026 results against model predictions in real time — from the group stage through the Final.

**🔗 Live demo:** [worldcupintelligence.vercel.app](https://worldcupintelligence.vercel.app)
**📡 API:** [wc2026-backend-cxdg.onrender.com/docs](https://wc2026-backend-cxdg.onrender.com/docs)

![Final Tournament Accuracy](https://img.shields.io/badge/Final%20Accuracy-68.6%25-gold)
![Predictions Tracked](https://img.shields.io/badge/Predictions%20Tracked-70-blue)
![Stage](https://img.shields.io/badge/Stage-Complete-green)

## What it does

- **Match Predictor** — predicts win/draw/loss probability for every WC 2026 match using a Random Forest + XGBoost ensemble trained on 32,000+ international fixtures since 1990, with dynamic Elo ratings computed from full match history
- **Player Analyzer** — clusters 9,952 outfield players from all 48 nations into 6 statistical archetypes using K-Means on FC 26 player data, with a per-team squad composition explorer
- **Sentiment Pulse** — real-time Reddit sentiment analysis using VADER, tracking fan reaction match-by-match
- **Live Dashboard** — every prediction tracked against real tournament results, with accuracy broken down by confidence level and documented failure modes

## Final Tournament Accuracy

| Metric | Result |
|--------|--------|
| Total predictions tracked | 70 |
| Matches played (full tournament) | 70 |
| Correct predictions | 48 |
| Final accuracy | **68.6%** |
| Accuracy by stage | Group: 68% · R32: 82% · R16: 67% · QF: 75% · SF: 50% · Final stage: 0% |

The clearest pattern across the tournament: errors cluster almost entirely around **draws** and near-50/50 matchups. The Final itself was called almost exactly right in spirit even though scored wrong — the model gave Argentina 30.1% and Spain 30.2%, a near-perfect coin flip, and Spain won 1-0. That's a well-calibrated model correctly expressing genuine uncertainty, not a failure.

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

## Architecture

```
┌─────────────────┐      ┌──────────────────────────┐      ┌─────────────────┐
│   Vue 3 + Vite   │ ───▶ │      FastAPI Backend      │ ───▶ │  Hugging Face    │
│   (Vercel)       │ ◀─── │  3 engines + SQLite DB    │ ◀─── │  Model Storage   │
└─────────────────┘      │       (Render)            │      └─────────────────┘
                          └──────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
              Match Predictor  Player Analyzer   Sentiment Pulse
              (RF + XGBoost)     (K-Means)        (VADER + Reddit)
```

## Model Details

### Engine 1 — Match Predictor
- **Data:** FIFA international results 1990–2026 (32,000+ matches)
- **Features (19):** team form, head-to-head record, scorer depth, **dynamic Elo rating**, tournament flag
- **Model:** Random Forest (calibrated) + XGBoost ensemble — probabilities averaged across both team orderings to cancel home-team bias on neutral-ground matches
- **CV Accuracy:** 59.1% (3-class: win/draw/loss; random baseline = 33.3%)
- **Live tournament accuracy:** 68.6% across all 70 matches, group stage through the Final

### Engine 2 — Player Analyzer
- **Data:** FC 26 / FIFA 26 complete player dataset (18,405 players)
- **Scope:** WC 2026 nations, outfield only, overall ≥ 60 → 9,952 players
- **Model:** K-Means k=6, n_init=20, cluster count chosen via elbow method
- **Archetypes:** Pacey Dribbler, Defensive Anchor, Deep Playmaker, Defensive Anchor II, Pacey Dribbler II, Target Striker — named from each centroid's top-2 Z-score attributes, not hand-labelled

### Engine 3 — Sentiment Pulse
- **Data source:** Arctic Shift API — a free, keyless Reddit data mirror. Reddit's own public `.json` endpoint stopped reliably serving unauthenticated requests during development; Arctic Shift ingests the same data independently and exposes it through a stable HTTP API
- **Model:** VADER — purpose-built for short, informal, emoji-heavy social text, chosen over a transformer to keep inference under 1ms and avoid a third multi-hundred-MB model alongside Engines 1 and 2

## Known Limitations

| Failure mode | Explanation |
|---|---|
| Draws | The model's single largest error category — pre-match statistics can't capture what produces a 0-0 or 1-1 result |
| Genuine upsets | Norway beating Brazil, Morocco beating Netherlands, Ecuador beating Germany — real model misses, not just draws |
| Order sensitivity (fixed) | Early versions showed home-team bias inherited from training data; fixed by averaging forward and reverse team-order predictions |
| Debutant/sparse-history nations | Teams with limited international match history (Curaçao, Cabo Verde) get less reliable Elo and form estimates |
| Reddit free-tier reliability | Arctic Shift has no uptime SLA; occasional 422s/timeouts on high-traffic subreddits are retried automatically |

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

Neel Menghani — B.E. Computer Engineering, Gujarat Technological University
[github.com/NboTop](https://github.com/NboTop)
