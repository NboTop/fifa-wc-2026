import requests
import pandas as pd
from pathlib import Path

BASE   = "http://localhost:8000"
MODELS = Path("models")

qf_matches = [
    ("Norway",    "England",     "Quarterfinal", "Jul-11"),
    ("Spain",     "Belgium",     "Quarterfinal", "Jul-10"),
    ("Argentina", "Switzerland", "Quarterfinal", "Jul-11"),
]

df = pd.read_csv(MODELS / "wc2026_predictions.csv")
updated = False

for team_a, team_b, stage, date in qf_matches:
    mask = (df.team_a == team_a) & (df.team_b == team_b)
    row  = df[mask]

    # Fill if row missing OR prediction columns are empty
    needs_pred = row.empty or pd.isna(row.iloc[0]["predicted"]) or str(row.iloc[0]["predicted"]).strip() == ""

    if not needs_pred:
        print(f"  already predicted: {team_a} vs {team_b} → {row.iloc[0]['predicted']}")
        continue

    try:
        r = requests.post(f"{BASE}/api/v1/predict",
                          json={"team_a": team_a, "team_b": team_b})
        d = r.json()
        print(f"  {team_a} vs {team_b} → {d['predicted']} ({d['confidence']}%)")

        if row.empty:
            new_row = pd.DataFrame([{
                "team_a": team_a, "team_b": team_b,
                "team_a_win_pct": d["team_a_win"],
                "draw_pct": d["draw"],
                "team_b_win_pct": d["team_b_win"],
                "predicted": d["predicted"],
                "confidence": d["confidence"],
                "actual_result": None, "correct": None,
                "date": date, "stage": stage,
            }])
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            df.loc[mask, "team_a_win_pct"] = d["team_a_win"]
            df.loc[mask, "draw_pct"]       = d["draw"]
            df.loc[mask, "team_b_win_pct"] = d["team_b_win"]
            df.loc[mask, "predicted"]      = d["predicted"]
            df.loc[mask, "confidence"]     = d["confidence"]
        updated = True
    except Exception as e:
        print(f"  ❌ {team_a} vs {team_b}: {e}")

if updated:
    df.to_csv(MODELS / "wc2026_predictions.csv", index=False)
    print("\n✅ QF predictions saved")
else:
    print("Nothing to update")