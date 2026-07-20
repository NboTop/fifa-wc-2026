# WC 2026 Intelligence Platform 🏆

An AI-powered match prediction, player analysis, and fan-sentiment platform tracking live World Cup 2026 results against model predictions in real time — from the group stage through the Final.

![Final Tournament Accuracy](https://img.shields.io/badge/Final%20Accuracy-68.6%25-gold)
![Predictions Tracked](https://img.shields.io/badge/Predictions%20Tracked-70-blue)
![Stage](https://img.shields.io/badge/Stage-Complete-green)

## What it does

- **Match Predictor** — predicts win/draw/loss probability for every WC 2026 match using a Random Forest + XGBoost ensemble trained on 32,000+ international fixtures since 1990, with dynamic Elo ratings computed from full match history (not static pre-tournament rankings)
- **Player Analyzer** — clusters 9,952 outfield players from all 48 nations into 6 statistical archetypes using K-Means on FC 26 player data, with a per-team squad composition explorer
- **Sentiment Pulse** — real-time Reddit sentiment analysis using VADER, tracking fan reaction match-by-match
- **Live Dashboard** — every prediction tracked against real tournament results as they happen, with accuracy broken down by confidence bucket and known failure modes

## Live Tournament Accuracy

| Metric | Result |
|--------|--------|
| Total predictions tracked | 70 |
| Matches played (full tournament) | 70 |
| Correct predictions | 48 |
| Overall accuracy | **68.6%** |
| Accuracy by stage | Group: 68% · R32: 82% · R16: 67% · QF: 75% · SF: 50% · Final stage: 0% |

The Final itself was called almost exactly right in spirit even though it was scored wrong: the model gave Argentina 30.1% and Spain 30.2% — a near-perfect coin flip — and Spain won 1-0. That's a well-calibrated model correctly expressing genuine uncertainty, not a failure.

The single clearest pattern across the tournament: **the model's errors cluster almost entirely around draws and near-50/50 matchups.** When the model was confident (≥70%), it was right the overwhelming majority of the time. Genuine upsets — Norway over Brazil, Morocco over Netherlands, Ecuador over Germany — account for the rest of the misses, and are documented below rather than hidden.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Match Prediction | Random Forest + XGBoost ensemble, scikit-learn |
| Team Strength | Dynamic Elo ratings (tournament-weighted K-factor) |
| Player Clustering | K-Means (k=6), StandardScaler, scikit-learn |
| Sentiment | VADER (social-media-tuned), Reddit public JSON API |
| Training | Google Colab (CPU + T4 GPU) |
| API | FastAPI, Pydantic, SQLAlchemy, Joblib |
| Frontend | Vue 3 (Composition API), Chart.js, Vite |
| Model hosting | Hugging Face Hub (pkl files, downloaded at runtime) |

## Architecture

```
┌─────────────────┐      ┌──────────────────────────┐      ┌─────────────────┐
│   Vue 3 + Vite   │ ───▶ │      FastAPI Backend      │ ───▶ │  Hugging Face    │
│  (3 live views)  │ ◀─── │  3 engines + SQLite DB    │ ◀─── │  Model Storage   │
└─────────────────┘      └──────────────────────────┘      └─────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
              Match Predictor  Player Analyzer   Sentiment Pulse
              (RF + XGBoost)     (K-Means)          (VADER)
```

## Model Details

### Engine 1 — Match Predictor
- **Data:** FIFA international results 1990–2026 (32,000+ matches), refreshed from a live-updating source
- **Features (19):** team form (win rate, goals scored/conceded, form trend), head-to-head record, scorer depth, **dynamic Elo rating** (tournament-weighted), tournament flag
- **Model:** Random Forest (calibrated) + XGBoost ensemble — probabilities averaged across both team orderings to cancel home-team bias on neutral-ground matches
- **CV Accuracy:** 59.1% (3-class: win/draw/loss; random baseline = 33.3%)
- **Live tournament accuracy:** 70.6% across 68 played matches

### Engine 2 — Player Analyzer
- **Data:** FC 26 / FIFA 26 complete player dataset (18,405 players)
- **Scope:** WC 2026 nations, outfield only, overall ≥ 60 → 9,952 players
- **Features:** pace, shooting, passing, dribbling, defending, physic (StandardScaler normalised)
- **Model:** K-Means k=6, n_init=20, cluster count chosen via elbow method
- **Archetypes:** Pacey Dribbler, Defensive Anchor, Deep Playmaker, Defensive Anchor II, Pacey Dribbler II, Target Striker — named from each centroid's top-2 Z-score attributes, not hand-labelled

### Engine 3 — Sentiment Pulse
- **Data source:** Reddit public JSON endpoints (r/worldcup, r/soccer, r/football) — no API key required
- **Model:** VADER (Valence Aware Dictionary and sEntiment Reasoner) — purpose-built for short, informal, emoji-heavy social text, chosen over a transformer to keep inference under 1ms and avoid a second multi-hundred-MB model on top of Engine 1 and 2
- **Storage:** SQLite, queryable by match tag, source, and sentiment label

## Known Limitations

| Failure mode | Explanation |
|---|---|
| Draws | The model's single largest error category. Pre-match statistics don't capture the chaos that produces a 0-0 or 1-1 result. |
| Order sensitivity (fixed) | Earlier versions showed home-team bias from training data. Fixed by averaging forward and reverse team-order predictions. |
| Genuine upsets | Norway beating Brazil, Morocco beating Netherlands, and similar results are real model misses — the underlying stats favoured the eventual loser, and no amount of feature engineering fully closes this gap. |
| Debutant/sparse-history nations | Teams with limited international match history (Curaçao, Cabo Verde) get less reliable Elo and form estimates. |

## Running locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
On first run, model files (~70MB) download automatically from Hugging Face Hub and cache locally.

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5174` for the dashboard, `http://localhost:8000/docs` for the interactive API.

> Model `.pkl` files are hosted on [Hugging Face](https://huggingface.co/void-logic/wc2026-models) rather than committed to the repo, and download automatically on backend startup — this keeps the repo small while still working out of the box.

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
│   │   └── routers/
│   │       ├── predictions.py
│   │       ├── players.py
│   │       └── sentiment.py
│   ├── models/                      # CSV/JSON tracked in repo; pkl via HF
│   └── auto_update.py               # Pulls live results, fills in outcomes
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
