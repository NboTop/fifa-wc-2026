# WC 2026 Intelligence Platform 🏆

An AI-powered match prediction and player analysis platform tracking live World Cup 2026 results against model predictions in real-time.

![Live Tournament Accuracy](https://img.shields.io/badge/Live%20Accuracy-66.7%25-gold)
![Decisive Results](https://img.shields.io/badge/Decisive%20Results-10%2F10-green)
![Predictions](https://img.shields.io/badge/Predictions%20Tracked-40-blue)

## What it does

- **Match Predictor** — predicts win/draw/loss probability for every WC 2026 match using a Random Forest + XGBoost ensemble trained on 32,000+ international fixtures since 1990
- **Player Analyzer** — clusters 9,952 outfield players from all 48 nations into 6 statistical archetypes using K-Means on FC 26 player data
- **Live Dashboard** — tracks every prediction against real tournament results as they happen, updating accuracy in real-time

## Live Tournament Accuracy

| Metric | Result |
|--------|--------|
| Total predictions tracked | 40 |
| Matches played | 15 |
| Correct predictions | 10 |
| Overall accuracy | **66.7%** |
| Accuracy on decisive results | **10/10 (100%)** |

Every incorrect prediction was a draw. When a match produced a winner, the model identified the correct team every time. Draws require individual performance data (goalkeeper saves, set pieces) unavailable to pre-match statistical models — a known, documented limitation of this class of model.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Match Prediction | Random Forest + XGBoost ensemble, scikit-learn |
| Player Clustering | K-Means (k=6), StandardScaler, scikit-learn |
| Training | Google Colab (T4 GPU for fine-tuning, CPU for clustering) |
| API | FastAPI, Pydantic, Joblib |
| Frontend | Vue 3 (Composition API), Chart.js, Vite |

## Model Details

### Engine 1 — Match Predictor
- **Data:** FIFA international results 1990–2026 (32,000+ matches)
- **Features (19):** team form (win rate, goals scored/conceded, form trend), head-to-head record, scorer depth, FIFA rankings, tournament flag
- **Model:** Random Forest (calibrated) + XGBoost ensemble — probabilities averaged
- **CV Accuracy:** 57.9% (3-class: win/draw/loss; random baseline = 33.3%)

### Engine 2 — Player Analyzer
- **Data:** FC 26 / FIFA 26 complete player dataset (18,405 players)
- **Scope:** WC 2026 nations, outfield only, overall ≥ 60 → 9,952 players
- **Features:** pace, shooting, passing, dribbling, defending, physic (StandardScaler normalised)
- **Model:** K-Means k=6, n_init=20
- **Archetypes:** Pacey Dribbler, Defensive Anchor, Deep Playmaker, Defensive Anchor II, Pacey Dribbler II, Target Striker

## Known Limitations

| Failure mode | Explanation |
|---|---|
| Goalless draws | Model cannot predict exceptional individual goalkeeper performances |
| Low-confidence calls | When no team exceeds 55% win probability, outcomes are genuinely uncertain |
| Debutant nations | Teams with limited international history have sparse form data |

## Running locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5174` for the dashboard, `http://localhost:8000/docs` for the API.

> **Note:** Model files (`.pkl`) are not included in the repo due to file size. Regenerate them by running the Colab notebooks linked in the `/notebooks` section.

## Project Structure

wc2026-intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── engines/
│   │   │   ├── predictor.py
│   │   │   └── players.py
│   │   └── routers/
│   │       ├── predictions.py
│   │       └── players.py
│   └── models/
└── frontend/
    └── src/
        ├── views/
        │   ├── Dashboard.vue
        │   └── Players.vue
        └── components/


## Built by

Neel
[github.com/NboTop](https://github.com/NboTop)
