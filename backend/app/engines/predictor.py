import joblib
import pandas as pd
from pathlib import Path
from typing import Dict, Any

MODELS = Path(__file__).parent.parent.parent / "models"

class MatchPredictor:
    def __init__(self):
        self.rf      = None
        self.xgb     = None
        self.le      = None
        self.history = None

    @property
    def is_loaded(self) -> bool:
        return self.rf is not None

    def load(self):
        self.rf      = joblib.load(MODELS / "rf_model.pkl")
        self.xgb     = joblib.load(MODELS / "xgb_model.pkl")
        self.le      = joblib.load(MODELS / "label_encoder.pkl")
        self.elo = joblib.load(MODELS / "elo_ratings.pkl")
        self.history = joblib.load(MODELS / "match_history.pkl")
        self.history["date"] = pd.to_datetime(self.history["date"])
        print("✓ Engine 1: Match Predictor ready")

    def _form(self, team: str, before: str, n: int = 10) -> Dict:
        df = self.history
        mask   = ((df["home_team"] == team) | (df["away_team"] == team)) & (df["date"] < before)
        recent = df[mask].sort_values("date", ascending=False).head(n)

        if len(recent) == 0:
            return {"win_rate": 0.33, "goals_scored": 1.2, "goals_conceded": 1.2, "form_trend": 0}

        wins = draws = gs = gc = 0
        for _, m in recent.iterrows():
            s, c = (m.home_score, m.away_score) if m.home_team == team else (m.away_score, m.home_score)
            gs += s; gc += c
            if s > c:    wins  += 1
            elif s == c: draws += 1

        n_m         = len(recent)
        half        = max(1, n_m // 2)
        first_half  = recent.tail(half)
        second_half = recent.head(half)

        def wr(subset, t):
            w = sum(1 for _, r in subset.iterrows()
                    if (r.home_team == t and r.home_score > r.away_score) or
                       (r.away_team == t and r.away_score > r.home_score))
            return w / len(subset) if len(subset) else 0

        return {
            "win_rate":       wins / n_m,
            "goals_scored":   gs   / n_m,
            "goals_conceded": gc   / n_m,
            "form_trend":     wr(second_half, team) - wr(first_half, team),
        }

    def _h2h(self, a: str, b: str, before: str, n: int = 10) -> Dict:
        df   = self.history
        mask = (
            ((df["home_team"] == a) & (df["away_team"] == b)) |
            ((df["home_team"] == b) & (df["away_team"] == a))
        ) & (df["date"] < before)

        h2h = df[mask].sort_values("date", ascending=False).head(n)
        if len(h2h) == 0:
            return {"a_wins": 0.33, "draws": 0.33, "b_wins": 0.33}

        a_w = draws = b_w = 0
        for _, m in h2h.iterrows():
            hs, as_ = (m.home_score, m.away_score) if m.home_team == a else (m.away_score, m.home_score)
            if hs > as_:    a_w   += 1
            elif hs == as_: draws += 1
            else:           b_w   += 1

        t = len(h2h)
        return {"a_wins": a_w / t, "draws": draws / t, "b_wins": b_w / t}

    def predict(self, team_a: str, team_b: str, as_of: str = "2026-07-01") -> Dict[str, Any]:
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        # Run prediction both ways and average — removes home team bias
        # since WC matches are on neutral ground
        def _single(a, b):
            fa  = self._form(a, as_of)
            fb  = self._form(b, as_of)
            h2h = self._h2h(a, b, as_of)
            a_elo = self.elo.get(a, 1500)
            b_elo = self.elo.get(b, 1500)

            feat = pd.DataFrame([{
                'a_win_rate':       fa['win_rate'],
                'a_goals_scored':   fa['goals_scored'],
                'a_goals_conceded': fa['goals_conceded'],
                'a_form_trend':     fa['form_trend'],
                'a_scorer_depth':   0.5,
                'a_elo':            a_elo,
                'b_win_rate':       fb['win_rate'],
                'b_goals_scored':   fb['goals_scored'],
                'b_goals_conceded': fb['goals_conceded'],
                'b_form_trend':     fb['form_trend'],
                'b_scorer_depth':   0.5,
                'b_elo':            b_elo,
                'win_rate_diff':    fa['win_rate']     - fb['win_rate'],
                'goals_diff':       fa['goals_scored'] - fb['goals_scored'],
                'elo_diff':         a_elo - b_elo,
                'h2h_a_wins':       h2h['a_wins'],
                'h2h_draws':        h2h['draws'],
                'h2h_b_wins':       h2h['b_wins'],
                'is_tournament':    1,
            }])

            rf_p  = self.rf.predict_proba(feat)[0]
            xgb_p = self.xgb.predict_proba(feat)[0]
            return (rf_p + xgb_p) / 2

        # Forward: A vs B
        fwd = _single(team_a, team_b)
        # Reverse: B vs A — then flip a_win/b_win
        rev = _single(team_b, team_a)

        classes = self.le.classes_  # ['a_win', 'b_win', 'draw']
        idx_a   = list(classes).index('a_win')
        idx_b   = list(classes).index('b_win')
        idx_d   = list(classes).index('draw')

        # Reverse prediction: a_win in reversed = b_win in forward
        rev_flipped = [0.0] * 3
        rev_flipped[idx_a] = rev[idx_b]
        rev_flipped[idx_b] = rev[idx_a]
        rev_flipped[idx_d] = rev[idx_d]

        avg = [(fwd[i] + rev_flipped[i]) / 2 for i in range(3)]

        a_pct    = round(float(avg[idx_a]) * 100, 1)
        draw_pct = round(float(avg[idx_d]) * 100, 1)
        b_pct    = round(float(avg[idx_b]) * 100, 1)

        if a_pct >= b_pct and a_pct >= draw_pct:
            predicted, conf = team_a, a_pct
        elif b_pct >= a_pct and b_pct >= draw_pct:
            predicted, conf = team_b, b_pct
        else:
            predicted, conf = 'Draw', draw_pct

        return {
            'team_a':     team_a, 'team_b': team_b,
            'team_a_win': a_pct,  'draw':   draw_pct, 'team_b_win': b_pct,
            'predicted':  predicted, 'confidence': conf,
            'draw_risk':  draw_pct >= 28,
        }

    def get_all_predictions(self) -> list:
        path = MODELS / "wc2026_predictions.csv"
        if not path.exists():
            return []
        df = pd.read_csv(path)
        df = df.where(pd.notna(df), None)   # NaN → None → JSON null
        return df.to_dict(orient="records")

    def get_accuracy(self) -> Dict[str, Any]:
        path = MODELS / "wc2026_predictions.csv"
        if not path.exists():
            return {"total_predictions": 0, "played": 0, "correct": 0, "accuracy": 0}
        df     = pd.read_csv(path)
        played = df[df["actual_result"].notna()]
        total  = len(played)
        correct = int(played["correct"].apply(lambda x: str(x).strip().lower() == "true").sum())
        return {
            "total_predictions": len(df),
            "played":   total,
            "correct":  correct,
            "accuracy": round(correct / total * 100, 1) if total else 0,
    }


match_predictor = MatchPredictor()
