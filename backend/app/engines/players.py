import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

MODELS = Path(__file__).parent.parent.parent / "models"


class PlayerAnalyzer:
    def __init__(self):
        self.players_df       = None
        self.cluster_profiles = None
        self.team_composition = None

    @property
    def is_loaded(self) -> bool:
        return self.players_df is not None

    def load(self):
        self.players_df = pd.read_csv(MODELS / "wc2026_player_clusters.csv")

        with open(MODELS / "wc2026_cluster_profiles.json") as f:
            self.cluster_profiles = json.load(f)

        with open(MODELS / "wc2026_team_composition.json") as f:
            self.team_composition = json.load(f)

        print("✓ Engine 2: Player Analyzer ready")

    def get_team_players(self, nation: str) -> List[Dict]:
        sub = self.players_df[
            self.players_df["nationality_name"].str.lower() == nation.lower()
        ].sort_values("overall", ascending=False)
        return sub.head(23).fillna("").to_dict(orient="records")

    def get_cluster_profiles(self) -> Dict:
        return self.cluster_profiles or {}

    def get_team_composition(self, nation: str = None) -> Any:
        if nation:
            return self.team_composition.get(nation, {})
        return self.team_composition or {}

    def get_top_by_cluster(self, cluster_name: str, limit: int = 10) -> List[Dict]:
        sub = self.players_df[
            self.players_df["cluster_name"] == cluster_name
        ].sort_values("overall", ascending=False)
        return sub.head(limit).fillna("").to_dict(orient="records")

    def get_all_nations(self) -> List[str]:
        return sorted(self.players_df["nationality_name"].unique().tolist())


player_analyzer = PlayerAnalyzer()
