import pandas as pd
import requests
from pathlib import Path

MODELS = Path("models")
RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"

def auto_update():
    print("Fetching latest results...")
    results = pd.read_csv(RESULTS_URL)
    results['date'] = pd.to_datetime(results['date'])
    results = results.dropna(subset=['home_score', 'away_score'])

    preds = pd.read_csv(MODELS / "wc2026_predictions.csv")
    updated = 0

    for i, row in preds.iterrows():
        if pd.notna(row.get('actual_result')) and str(row.get('actual_result')).strip() not in ['', 'nan']:
            continue

        a, b = row['team_a'], row['team_b']
        match = results[
            ((results['home_team'] == a) & (results['away_team'] == b)) |
            ((results['home_team'] == b) & (results['away_team'] == a))
        ].sort_values('date', ascending=False).head(1)

        if len(match) == 0:
            continue

        m = match.iloc[0]
        if m.home_team == a:
            hs, as_ = m.home_score, m.away_score
        else:
            hs, as_ = m.away_score, m.home_score

        if hs > as_:    actual = a
        elif as_ > hs:  actual = b
        else:           actual = "Draw"

        predicted = str(row.get('predicted', '')).strip()
        correct   = str(actual) == str(predicted)

        preds.at[i, 'actual_result'] = actual
        preds.at[i, 'correct']       = correct
        updated += 1
        print(f"  ✓ {a} vs {b} → {actual} ({'✅' if correct else '❌'})")

    preds.to_csv(MODELS / "wc2026_predictions.csv", index=False)

    played  = preds[preds['actual_result'].notna() & (preds['actual_result'] != '')]
    correct = (played['correct'].astype(str).str.lower() == 'true').sum()
    print(f"\n✅ Updated {updated} rows")
    print(f"   Accuracy: {correct}/{len(played)} = {correct/len(played)*100:.1f}%")

if __name__ == "__main__":
    auto_update()