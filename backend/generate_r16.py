import requests
import pandas as pd
from pathlib import Path

BASE   = "http://localhost:8000"
MODELS = Path("models")

r16_matches = [
    ("Brazil",         "Norway",          "Round of 16", "Jul-5"),
    ("Mexico",         "England",         "Round of 16", "Jul-5"),
    ("Portugal",       "Spain",           "Round of 16", "Jul-6"),
    ("United States",  "Belgium",         "Round of 16", "Jul-6"),
    ("Argentina",      "Egypt",           "Round of 16", "Jul-7"),
    ("Switzerland",    "Colombia",        "Round of 16", "Jul-7"),
    ("France",         "Morocco",         "Round of 16", "Jul-9"),
    ("Paraguay",       "Canada",          "Round of 16", "Jul-9"), # loser bracket — actually France won
]

# Correct R16 bracket based on actual R32 results
r16_matches = [
    ("Brazil",         "Norway",          "Round of 16", "Jul-5"),
    ("Mexico",         "England",         "Round of 16", "Jul-5"),
    ("Portugal",       "Spain",           "Round of 16", "Jul-6"),
    ("United States",  "Belgium",         "Round of 16", "Jul-6"),
    ("Argentina",      "Egypt",           "Round of 16", "Jul-7"),
    ("Switzerland",    "Colombia",        "Round of 16", "Jul-7"),
    ("France",         "Morocco",         "Round of 16", "Jul-9"),
    ("Norway",         "Mexico",          "Round of 16", "Jul-9"),  # placeholder — fix after today
]

# Final correct bracket
r16_matches = [
    ("Brazil",        "Norway",     "Round of 16", "Jul-5"),
    ("Mexico",        "England",    "Round of 16", "Jul-5"),
    ("Portugal",      "Spain",      "Round of 16", "Jul-6"),
    ("United States", "Belgium",    "Round of 16", "Jul-6"),
    ("Argentina",     "Egypt",      "Round of 16", "Jul-7"),
    ("Switzerland",   "Colombia",   "Round of 16", "Jul-7"),
    ("France",        "Morocco",    "Round of 16", "Jul-9"),
]

existing = pd.read_csv(MODELS / "wc2026_predictions.csv")

new_rows = []
for team_a, team_b, stage, date in r16_matches:
    already = ((existing.team_a == team_a) & (existing.team_b == team_b)).any()
    if already:
        print(f"  already exists: {team_a} vs {team_b}")
        continue
    try:
        r = requests.post(f"{BASE}/api/v1/predict",
                          json={"team_a": team_a, "team_b": team_b})
        d = r.json()
        new_rows.append({
            "team_a":         team_a,
            "team_b":         team_b,
            "team_a_win_pct": d["team_a_win"],
            "draw_pct":       d["draw"],
            "team_b_win_pct": d["team_b_win"],
            "predicted":      d["predicted"],
            "confidence":     d["confidence"],
            "actual_result":  None,
            "correct":        None,
            "date":           date,
            "stage":          stage,
        })
        print(f"  {team_a} vs {team_b} → {d['predicted']} ({d['confidence']}%)")
    except Exception as e:
        print(f"  ❌ {team_a} vs {team_b}: {e}")

if new_rows:
    combined = pd.concat([existing, pd.DataFrame(new_rows)], ignore_index=True)
    combined.to_csv(MODELS / "wc2026_predictions.csv", index=False)
    print(f"\n✅ Added {len(new_rows)} R16 predictions")
else:
    print("Nothing added")