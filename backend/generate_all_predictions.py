import requests
import pandas as pd
from pathlib import Path

BASE   = "http://localhost:8000"
AS_OF  = "2026-06-22"
MODELS = Path("models")

# All remaining group stage matches across all 12 groups
# Round 2 = currently playing or just finished
# Round 3 = upcoming June 24-27
MATCHES = [
    # Group A — Round 3 (June 24)
    ("Mexico",              "Czechia",               "Group A", "June 24"),
    ("South Africa",        "Korea Republic",         "Group A", "June 24"),
    # Group B — Round 3 (June 24)
    ("Switzerland",         "Canada",                 "Group B", "June 24"),
    ("Bosnia and Herzegovina", "Qatar",               "Group B", "June 24"),
    # Group C — Round 3 (June 24)
    ("Brazil",              "Scotland",               "Group C", "June 24"),
    ("Morocco",             "Haiti",                  "Group C", "June 24"),
    # Group D — Round 3 (June 25)
    ("United States",       "Turkey",                 "Group D", "June 25"),
    ("Paraguay",            "Australia",              "Group D", "June 25"),
    # Group E — Round 3 (June 25)
    ("Germany",             "Ecuador",                "Group E", "June 25"),
    ("Cote d'Ivoire",       "Curacao",                "Group E", "June 25"),
    # Group F — Round 3 (June 26)
    ("Japan",               "Sweden",                 "Group F", "June 26"),
    ("Netherlands",         "Tunisia",                "Group F", "June 26"),
    # Group G — Round 2 (June 22-23)
    ("Belgium",             "Iran",                   "Group G", "June 22"),
    ("New Zealand",         "Egypt",                  "Group G", "June 22"),
    # Group G — Round 3 (June 26)
    ("Belgium",             "New Zealand",            "Group G", "June 26"),
    ("Egypt",               "Iran",                   "Group G", "June 26"),
    # Group H — Round 2 (June 21, some may have played)
    ("Uruguay",             "Cabo Verde",             "Group H", "June 21"),
    # Group H — Round 3 (June 25)
    ("Spain",               "Uruguay",                "Group H", "June 25"),
    ("Cabo Verde",          "Saudi Arabia",           "Group H", "June 25"),
    # Group I — Round 3 (June 26) — already in CSV, skip
    # Group J — Round 2 (June 22)
    ("Argentina",           "Austria",                "Group J", "June 22"),
    ("Algeria",             "Jordan",                 "Group J", "June 22"),
    # Group J — Round 3 (June 27)
    ("Argentina",           "Jordan",                 "Group J", "June 27"),
    ("Algeria",             "Austria",                "Group J", "June 27"),
    # Group K — Round 2 (June 23)
    ("Portugal",            "Uzbekistan",             "Group K", "June 23"),
    ("Colombia",            "Congo DR",               "Group K", "June 23"),
    # Group K — Round 3 (June 27)
    ("Colombia",            "Portugal",               "Group K", "June 27"),
    ("Congo DR",            "Uzbekistan",             "Group K", "June 27"),
    # Group L — Round 2 (June 23)
    ("England",             "Ghana",                  "Group L", "June 23"),
    ("Panama",              "Croatia",                "Group L", "June 23"),
    # Group L — Round 3 (June 27)
    ("Panama",              "England",                "Group L", "June 27"),
    ("Croatia",             "Ghana",                  "Group L", "June 27"),
]

print("Generating predictions for all 12 groups...\n")
rows = []
for team_a, team_b, group, date in MATCHES:
    try:
        r = requests.post(f"{BASE}/api/v1/predict",
                          json={"team_a": team_a, "team_b": team_b, "as_of": AS_OF})
        d = r.json()
        rows.append({
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
            "stage":          group,
        })
        print(f"  {group} | {team_a} vs {team_b} → {d['predicted']} ({d['confidence']}%)")
    except Exception as e:
        print(f"  ❌ {team_a} vs {team_b}: {e}")

# Merge with existing predictions CSV (keep the 4 filled-in results)
existing = pd.read_csv(MODELS / "wc2026_predictions.csv")
new_df   = pd.DataFrame(rows)

# Remove any duplicates (matches already in existing CSV)
existing_pairs = set(zip(existing.team_a, existing.team_b))
new_df = new_df[~new_df.apply(lambda r: (r.team_a, r.team_b) in existing_pairs, axis=1)]

combined = pd.concat([existing, new_df], ignore_index=True)
combined.to_csv(MODELS / "wc2026_predictions.csv", index=False)
print(f"\n✅ Total predictions: {len(combined)} ({len(new_df)} new added)")
print(f"   Saved → models/wc2026_predictions.csv")